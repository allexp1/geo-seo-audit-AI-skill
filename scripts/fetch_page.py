#!/usr/bin/env python3
"""Fetch a URL and emit normalized page data as JSON."""
from __future__ import annotations

import json
import sys
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (compatible; geo-skill/1.0; +https://github.com/)"
TIMEOUT = 20


def fetch(url: str) -> dict:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT, allow_redirects=True)
    soup = BeautifulSoup(r.text, "html.parser")

    title = (soup.title.string.strip() if soup.title and soup.title.string else "")
    meta_desc = ""
    md = soup.find("meta", attrs={"name": "description"})
    if md and md.get("content"):
        meta_desc = md["content"].strip()

    canonical = ""
    link = soup.find("link", rel="canonical")
    if link and link.get("href"):
        canonical = link["href"].strip()

    h1 = [h.get_text(strip=True) for h in soup.find_all("h1")]
    h2 = [h.get_text(strip=True) for h in soup.find_all("h2")]

    jsonld_blocks = []
    for s in soup.find_all("script", type="application/ld+json"):
        if s.string:
            jsonld_blocks.append(s.string.strip())

    parsed = urlparse(r.url)
    return {
        "requested_url": url,
        "final_url": r.url,
        "origin": f"{parsed.scheme}://{parsed.netloc}",
        "status": r.status_code,
        "content_type": r.headers.get("content-type", ""),
        "title": title,
        "meta_description": meta_desc,
        "canonical": canonical,
        "h1": h1,
        "h2_count": len(h2),
        "html_bytes": len(r.content),
        "jsonld_count": len(jsonld_blocks),
        "jsonld_raw": jsonld_blocks,
        "html": r.text,
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: fetch_page.py <url>", file=sys.stderr)
        return 2
    data = fetch(sys.argv[1])
    # Strip the heavy fields when printing unless --full is passed
    if "--full" not in sys.argv:
        data.pop("html", None)
        data.pop("jsonld_raw", None)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
