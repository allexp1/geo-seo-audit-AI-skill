#!/usr/bin/env python3
"""Check where a domain ranks on Google for given keywords.

Three modes (checked in order):
  1. SerpAPI (set SERPAPI_KEY) — real Google results. Free: 100/month.
  2. Google Custom Search API (set GOOGLE_CSE_KEY + GOOGLE_CSE_CX) — 100/day free.
  3. DuckDuckGo via `ddgs` (fallback, no key needed).

Usage:
  python3 keyword_rank.py <domain> <keyword1> [keyword2 ...]
  python3 keyword_rank.py <domain> --from-extract <url>  (auto-extract top keywords)
"""
from __future__ import annotations

import json
import os
import sys
import time
from urllib.parse import urlparse

import requests

TIMEOUT = 20
RATE_LIMIT = 2  # seconds between queries


def _domain_matches(result_url: str, target_domain: str) -> bool:
    parsed = urlparse(result_url)
    host = parsed.netloc.lower().lstrip("www.")
    target = target_domain.lower().lstrip("www.")
    return host == target or host.endswith("." + target)


# ---------------------------------------------------------------------------
# Mode 1: SerpAPI (real Google)
# ---------------------------------------------------------------------------

def _search_serpapi(keyword: str, domain: str) -> dict:
    try:
        from serpapi import GoogleSearch
    except ImportError:
        from serpapi.google_search import GoogleSearch

    params = {
        "q": keyword,
        "api_key": os.environ["SERPAPI_KEY"],
        "engine": "google",
        "num": 30,
        "hl": "en",
        "gl": "us",
    }

    try:
        search = GoogleSearch(params)
        data = search.get_dict()
    except Exception as e:
        return {
            "keyword": keyword, "domain": domain, "method": "serpapi",
            "error": str(e), "top_position": None, "appearances": [],
        }

    positions: list[dict] = []
    all_results: list[dict] = []

    for item in data.get("organic_results", []):
        rank = item.get("position", 0)
        link = item.get("link", "")
        title = item.get("title", "")
        snippet = item.get("snippet", "")[:120]
        all_results.append({"rank": rank, "url": link, "title": title, "snippet": snippet})
        if _domain_matches(link, domain):
            positions.append({"rank": rank, "url": link, "title": title, "snippet": snippet})

    # Also check featured snippets, knowledge panels, etc.
    featured = data.get("answer_box", {})
    if featured.get("link") and _domain_matches(featured["link"], domain):
        positions.insert(0, {
            "rank": 0, "url": featured["link"],
            "title": featured.get("title", "Featured Snippet"),
            "type": "featured_snippet",
        })

    # People Also Ask
    paa = data.get("related_questions", [])
    paa_appearances = []
    for q in paa:
        if q.get("link") and _domain_matches(q["link"], domain):
            paa_appearances.append({"question": q.get("question", ""), "url": q["link"]})

    result: dict = {
        "keyword": keyword,
        "domain": domain,
        "method": "google (serpapi)",
        "top_position": positions[0]["rank"] if positions else None,
        "appearances": positions,
        "total_results_checked": len(data.get("organic_results", [])),
        "top_3": all_results[:3],
    }
    if paa_appearances:
        result["people_also_ask"] = paa_appearances
    if data.get("search_information", {}).get("total_results"):
        result["total_google_results"] = data["search_information"]["total_results"]
    return result


# ---------------------------------------------------------------------------
# Mode 2: Google Custom Search API
# ---------------------------------------------------------------------------

def _search_google_cse(keyword: str, domain: str) -> dict:
    key = os.environ["GOOGLE_CSE_KEY"]
    cx = os.environ["GOOGLE_CSE_CX"]
    positions: list[dict] = []
    all_results: list[dict] = []

    for start in range(1, 101, 10):
        params = {"key": key, "cx": cx, "q": keyword, "start": start, "num": 10}
        r = requests.get(
            "https://www.googleapis.com/customsearch/v1",
            params=params,
            timeout=TIMEOUT,
        )
        data = r.json()
        items = data.get("items", [])
        if not items:
            break
        for i, item in enumerate(items):
            rank = start + i
            link = item.get("link", "")
            title = item.get("title", "")
            all_results.append({"rank": rank, "url": link, "title": title})
            if _domain_matches(link, domain):
                positions.append({"rank": rank, "url": link, "title": title})

    return {
        "keyword": keyword,
        "domain": domain,
        "method": "google (cse api)",
        "top_position": positions[0]["rank"] if positions else None,
        "appearances": positions,
        "checked_results": len(all_results),
        "top_3": all_results[:3],
    }


# ---------------------------------------------------------------------------
# Mode 3: DuckDuckGo fallback
# ---------------------------------------------------------------------------

def _search_ddg(keyword: str, domain: str) -> dict:
    try:
        from ddgs import DDGS
        results = list(DDGS().text(keyword, max_results=30))
    except Exception as e:
        return {
            "keyword": keyword, "domain": domain, "method": "duckduckgo",
            "error": str(e), "top_position": None, "appearances": [],
        }

    positions: list[dict] = []
    all_results: list[dict] = []
    for i, r in enumerate(results, 1):
        url = r.get("href", "")
        title = r.get("title", "")
        all_results.append({"rank": i, "url": url, "title": title})
        if _domain_matches(url, domain):
            positions.append({"rank": i, "url": url, "title": title})

    return {
        "keyword": keyword,
        "domain": domain,
        "method": "duckduckgo (fallback)",
        "top_position": positions[0]["rank"] if positions else None,
        "appearances": positions,
        "total_results_checked": len(results),
        "top_3": all_results[:3],
    }


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def _pick_engine():
    if os.environ.get("SERPAPI_KEY"):
        return "serpapi"
    if os.environ.get("GOOGLE_CSE_KEY") and os.environ.get("GOOGLE_CSE_CX"):
        return "cse"
    return "ddg"


def _search(keyword: str, domain: str, engine: str) -> dict:
    if engine == "serpapi":
        return _search_serpapi(keyword, domain)
    elif engine == "cse":
        return _search_google_cse(keyword, domain)
    else:
        return _search_ddg(keyword, domain)


def check_rankings(domain: str, keywords: list[str]) -> dict:
    engine = _pick_engine()
    results = []

    for i, kw in enumerate(keywords):
        results.append(_search(kw, domain, engine))
        if i < len(keywords) - 1:
            time.sleep(RATE_LIMIT)

    ranked = [r for r in results if r.get("top_position") is not None]
    not_found = [r for r in results if r.get("top_position") is None and "error" not in r]

    return {
        "domain": domain,
        "engine": engine,
        "method": results[0].get("method", engine) if results else engine,
        "keywords_checked": len(keywords),
        "keywords_ranking": len(ranked),
        "results": results,
        "summary": {
            "best_position": min((r["top_position"] for r in ranked), default=None),
            "avg_position": (
                round(sum(r["top_position"] for r in ranked) / len(ranked), 1)
                if ranked else None
            ),
            "not_in_results": [r["keyword"] for r in not_found],
        },
    }


def main() -> int:
    if len(sys.argv) < 3:
        print(
            "usage: keyword_rank.py <domain> <kw1> [kw2 ...]\n"
            "       keyword_rank.py <domain> --from-extract <url>",
            file=sys.stderr,
        )
        return 2

    domain = sys.argv[1]

    if sys.argv[2] == "--from-extract":
        if len(sys.argv) < 4:
            print("need a URL after --from-extract", file=sys.stderr)
            return 2
        from keyword_extract import extract
        data = extract(sys.argv[3])
        multi = [k["keyword"] for k in data["keywords"] if " " in k["keyword"]][:4]
        single = [k["keyword"] for k in data["keywords"] if " " not in k["keyword"]][:2]
        keywords = (multi + single)[:5]
        if not keywords:
            keywords = [k["keyword"] for k in data["keywords"][:5]]
    else:
        keywords = sys.argv[2:]

    print(json.dumps(check_rankings(domain, keywords), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
