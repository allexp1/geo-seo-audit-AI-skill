#!/usr/bin/env python3
"""Check for /llms.txt (and /llms-full.txt) and report conformance to the spec.

Spec: https://llmstxt.org — a markdown file at site root that summarizes a
site for LLMs. Should start with an H1 (the site name), an optional blockquote
summary, then markdown sections of links. /llms-full.txt is the community
convention for a single file with full page content inlined.

Honest value note (2026): Google says Search does NOT consume llms.txt, and
no major AI vendor has committed to it. It IS checked by Lighthouse's
Agentic Browsing audit and fetched by coding/IDE agents (Cursor, Claude Code,
Copilot) on docs sites. Treat it as a low-weight agent-readiness signal.

If the file is absent, emits a generated template based on the homepage.
"""
from __future__ import annotations

import json
import re
import sys
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (compatible; geo-skill/1.0)"
TIMEOUT = 15


def check_existing(text: str) -> dict:
    lines = text.splitlines()
    has_h1 = bool(lines) and lines[0].startswith("# ")
    has_summary = any(line.startswith("> ") for line in lines[:10])
    section_headers = [l for l in lines if l.startswith("## ")]
    link_count = len(re.findall(r"\[[^\]]+\]\([^)]+\)", text))
    return {
        "size": len(text),
        "starts_with_h1": has_h1,
        "has_summary_blockquote": has_summary,
        "section_count": len(section_headers),
        "sections": [s.lstrip("# ").strip() for s in section_headers],
        "link_count": link_count,
        "valid_shape": has_h1 and link_count > 0,
    }


def generate_template(url: str) -> str:
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
        soup = BeautifulSoup(r.text, "html.parser")
        title = (soup.title.string.strip() if soup.title and soup.title.string else "Site")
        md = soup.find("meta", attrs={"name": "description"})
        desc = md["content"].strip() if md and md.get("content") else "One-line summary of what this site offers."
    except Exception:
        title = "Site"
        desc = "One-line summary of what this site offers."

    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    return f"""# {title}

> {desc}

## Documentation

- [Homepage]({origin}/): Overview and entry point.
- [About]({origin}/about): Who runs this site and why.

## Products

- [Product or service]({origin}/product): Short description of what it does.

## Optional

- [Blog]({origin}/blog): Long-form content and updates.
- [Contact]({origin}/contact): How to reach the team.
"""


def check(url: str) -> dict:
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
        parsed = urlparse(url)
    target = f"{parsed.scheme}://{parsed.netloc}/llms.txt"

    out: dict = {"url": target}
    try:
        r = requests.get(target, headers={"User-Agent": UA}, timeout=TIMEOUT)
    except Exception as e:
        out["error"] = str(e)
        return out

    out["status"] = r.status_code
    if r.status_code == 200 and "html" not in r.headers.get("content-type", "").lower():
        out["present"] = True
        out["analysis"] = check_existing(r.text)
    else:
        out["present"] = False
        out["suggested_template"] = generate_template(f"{parsed.scheme}://{parsed.netloc}/")

    # Companion file with full content inlined (community convention)
    try:
        rf = requests.get(f"{parsed.scheme}://{parsed.netloc}/llms-full.txt",
                          headers={"User-Agent": UA}, timeout=TIMEOUT)
        out["llms_full_present"] = (rf.status_code == 200
                                    and "html" not in rf.headers.get("content-type", "").lower())
        if out["llms_full_present"]:
            out["llms_full_size"] = len(rf.text)
    except Exception:
        out["llms_full_present"] = False

    out["value_note"] = (
        "llms.txt is not consumed by Google Search; it is checked by Lighthouse's "
        "Agentic Browsing audit and fetched by coding/IDE agents. Low-weight signal."
    )
    return out


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: llmstxt.py <url>", file=sys.stderr)
        return 2
    print(json.dumps(check(sys.argv[1]), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
