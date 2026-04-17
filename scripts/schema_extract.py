#!/usr/bin/env python3
"""Extract and validate JSON-LD blocks from a page.

Reports each block's @type(s), whether it parses, and which common schema
types are missing. Does not validate against full schema.org definitions —
just checks structure and presence of expected fields.
"""
from __future__ import annotations

import json
import sys

import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (compatible; geo-skill/1.0)"
TIMEOUT = 20

# Types that signal good entity coverage for AI search
COMMON_TYPES = {
    "Organization": ["name", "url", "sameAs", "logo"],
    "WebSite": ["name", "url"],
    "Article": ["headline", "author", "datePublished"],
    "BlogPosting": ["headline", "author", "datePublished"],
    "BreadcrumbList": ["itemListElement"],
    "FAQPage": ["mainEntity"],
    "Product": ["name", "offers"],
    "LocalBusiness": ["name", "address", "telephone"],
    "Person": ["name"],
    "SoftwareApplication": ["name", "applicationCategory"],
}


def types_of(obj) -> list[str]:
    if not isinstance(obj, dict):
        return []
    t = obj.get("@type")
    if isinstance(t, list):
        return [str(x) for x in t]
    if isinstance(t, str):
        return [t]
    return []


def walk(obj, found: set[str]) -> None:
    if isinstance(obj, dict):
        for t in types_of(obj):
            found.add(t)
        for v in obj.values():
            walk(v, found)
    elif isinstance(obj, list):
        for v in obj:
            walk(v, found)


def field_check(obj, expected: list[str]) -> dict:
    if not isinstance(obj, dict):
        return {"ok": False, "missing": expected}
    missing = [f for f in expected if f not in obj]
    return {"ok": not missing, "missing": missing}


def analyze(url: str) -> dict:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
    soup = BeautifulSoup(r.text, "html.parser")
    blocks = []
    found_types: set[str] = set()
    field_reports: dict[str, dict] = {}

    for s in soup.find_all("script", type="application/ld+json"):
        if not s.string:
            continue
        raw = s.string.strip()
        entry: dict = {"size": len(raw)}
        try:
            data = json.loads(raw)
            entry["parsed"] = True
            entry["types"] = []
            walk(data, found_types)

            # Check field presence on top-level objects (or @graph entries)
            top_objs: list = []
            if isinstance(data, list):
                top_objs = data
            elif isinstance(data, dict):
                if "@graph" in data and isinstance(data["@graph"], list):
                    top_objs = data["@graph"]
                else:
                    top_objs = [data]

            for obj in top_objs:
                for t in types_of(obj):
                    entry["types"].append(t)
                    if t in COMMON_TYPES and t not in field_reports:
                        field_reports[t] = field_check(obj, COMMON_TYPES[t])
        except json.JSONDecodeError as e:
            entry["parsed"] = False
            entry["error"] = str(e)
        blocks.append(entry)

    missing_common = [t for t in COMMON_TYPES if t not in found_types]
    return {
        "url": url,
        "block_count": len(blocks),
        "types_found": sorted(found_types),
        "common_types_missing": missing_common,
        "field_checks": field_reports,
        "blocks": blocks,
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: schema_extract.py <url>", file=sys.stderr)
        return 2
    print(json.dumps(analyze(sys.argv[1]), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
