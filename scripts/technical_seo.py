#!/usr/bin/env python3
"""Technical SEO checks at the HTTP layer.

Covers:
  - HTTPS upgrade behavior
  - Security headers (HSTS, CSP, X-Content-Type-Options, X-Frame-Options,
    Referrer-Policy, Permissions-Policy)
  - Compression (Content-Encoding gzip/br)
  - Caching headers
  - Response time
  - sitemap.xml presence + URL count + reference in robots.txt
  - Server header (informational)
"""
from __future__ import annotations

import json
import re
import sys
import time
from urllib.parse import urlparse
from xml.etree import ElementTree as ET

import requests

UA = "Mozilla/5.0 (compatible; geo-skill/1.0)"
TIMEOUT = 20

SECURITY_HEADERS = [
    "Strict-Transport-Security",
    "Content-Security-Policy",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Referrer-Policy",
    "Permissions-Policy",
]

CACHE_HEADERS = ["Cache-Control", "ETag", "Last-Modified", "Expires"]


def check_https(url: str) -> dict:
    parsed = urlparse(url)
    base = parsed.netloc or parsed.path
    http_url = f"http://{base}/"
    out: dict = {"requested": url}
    try:
        r = requests.get(
            http_url,
            headers={"User-Agent": UA},
            timeout=TIMEOUT,
            allow_redirects=True,
        )
        out["http_to_https_redirect"] = r.url.startswith("https://")
        out["final_url"] = r.url
        out["redirect_chain_length"] = len(r.history)
    except Exception as e:
        out["error"] = str(e)
        out["http_to_https_redirect"] = False
    return out


def fetch_with_timing(url: str) -> dict:
    start = time.perf_counter()
    r = requests.get(
        url,
        headers={"User-Agent": UA, "Accept-Encoding": "gzip, br, deflate"},
        timeout=TIMEOUT,
        allow_redirects=True,
    )
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    headers = {k: v for k, v in r.headers.items()}
    security = {h: headers.get(h, "") for h in SECURITY_HEADERS}
    cache = {h: headers.get(h, "") for h in CACHE_HEADERS}

    # Cloudflare fronting matters for GEO: since July 2025 it blocks AI
    # training crawlers by default, regardless of what robots.txt says.
    behind_cloudflare = ("cloudflare" in headers.get("Server", "").lower()
                         or "cf-ray" in {k.lower() for k in headers})

    return {
        "final_url": r.url,
        "status": r.status_code,
        "elapsed_ms": elapsed_ms,
        "content_length_bytes": len(r.content),
        "content_encoding": headers.get("Content-Encoding", ""),
        "content_type": headers.get("Content-Type", ""),
        "server": headers.get("Server", ""),
        "x_powered_by": headers.get("X-Powered-By", ""),
        "behind_cloudflare": behind_cloudflare,
        "security_headers": security,
        "security_headers_present": sum(1 for v in security.values() if v),
        "cache_headers": cache,
    }


def check_sitemap(origin: str, robots_text: str) -> dict:
    out: dict = {}
    # Sitemap referenced in robots.txt?
    sitemap_lines = re.findall(
        r"^\s*sitemap\s*:\s*(\S+)", robots_text or "", re.IGNORECASE | re.MULTILINE
    )
    out["referenced_in_robots"] = sitemap_lines

    # Try standard locations
    candidates = list(dict.fromkeys(sitemap_lines + [f"{origin}/sitemap.xml", f"{origin}/sitemap_index.xml"]))
    found = None
    for cand in candidates:
        try:
            r = requests.get(cand, headers={"User-Agent": UA}, timeout=TIMEOUT)
            if r.status_code == 200 and ("xml" in r.headers.get("content-type", "").lower() or r.text.lstrip().startswith("<")):
                found = (cand, r.text)
                break
        except Exception:
            continue

    if not found:
        out["present"] = False
        return out

    cand, body = found
    out["present"] = True
    out["url"] = cand
    out["bytes"] = len(body)

    # Count URLs (handle <urlset> and <sitemapindex>)
    try:
        root = ET.fromstring(body)
        # Strip namespaces for simple counting
        tag = root.tag.split("}")[-1]
        if tag == "urlset":
            out["type"] = "urlset"
            out["url_count"] = sum(1 for _ in root.iter() if _.tag.split("}")[-1] == "url")
        elif tag == "sitemapindex":
            out["type"] = "sitemapindex"
            out["sitemap_count"] = sum(1 for _ in root.iter() if _.tag.split("}")[-1] == "sitemap")
        else:
            out["type"] = tag
    except ET.ParseError as e:
        out["parse_error"] = str(e)

    return out


def analyze(url: str) -> dict:
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
        parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    out: dict = {"url": url, "origin": origin}
    out["https"] = check_https(url)
    out["response"] = fetch_with_timing(url)

    # robots.txt is needed to look for Sitemap: lines
    robots_text = ""
    try:
        rb = requests.get(f"{origin}/robots.txt", headers={"User-Agent": UA}, timeout=TIMEOUT)
        if rb.status_code == 200:
            robots_text = rb.text
    except Exception:
        pass

    out["sitemap"] = check_sitemap(origin, robots_text)
    return out


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: technical_seo.py <url>", file=sys.stderr)
        return 2
    print(json.dumps(analyze(sys.argv[1]), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
