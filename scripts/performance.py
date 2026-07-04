#!/usr/bin/env python3
"""Fetch Core Web Vitals and Lighthouse scores from Google PageSpeed Insights.

Uses the public PSI API — no API key required for basic use (rate-limited to
~25 req/100s). Set PAGESPEED_API_KEY env var for higher limits.

Returns:
  - Lighthouse performance score (0-100)
  - Core Web Vitals: LCP, INP, CLS (plus FCP, TTFB; FID retired Sept 2024)
  - Top Lighthouse opportunities (what to fix)
  - Strategy: mobile (default) or desktop

Thresholds (unchanged as of mid-2026, per web.dev — ignore blog claims of
2026 changes): LCP <= 2.5 s, INP <= 200 ms, CLS <= 0.1.
"""
from __future__ import annotations

import json
import os
import sys
from urllib.parse import quote

import requests

TIMEOUT = 60  # PSI can be slow


def analyze(url: str, strategy: str = "mobile") -> dict:
    api_key = os.environ.get("PAGESPEED_API_KEY", "")
    endpoint = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params: dict = {
        "url": url,
        "strategy": strategy,
        "category": "performance",
    }
    if api_key:
        params["key"] = api_key

    try:
        r = requests.get(endpoint, params=params, timeout=TIMEOUT)
    except requests.exceptions.Timeout:
        return {"url": url, "error": "PageSpeed Insights timed out (60s). Try again later."}
    except Exception as e:
        return {"url": url, "error": str(e)}

    if r.status_code != 200:
        if r.status_code == 429:
            return {"url": url, "error": "PageSpeed Insights daily quota exceeded. Set PAGESPEED_API_KEY for higher limits."}
        return {"url": url, "error": f"PageSpeed Insights returned {r.status_code}."}

    data = r.json()
    result: dict = {"url": url, "strategy": strategy}

    # Lighthouse score
    lh = data.get("lighthouseResult", {})
    perf = lh.get("categories", {}).get("performance", {})
    result["lighthouse_score"] = int((perf.get("score") or 0) * 100)

    # Core Web Vitals from field data (CrUX)
    crux = data.get("loadingExperience", {})
    metrics = crux.get("metrics", {})
    field: dict = {}

    mapping = {
        "LARGEST_CONTENTFUL_PAINT_MS": ("lcp_ms", "Largest Contentful Paint"),
        "FIRST_INPUT_DELAY_MS": ("fid_ms", "First Input Delay (legacy, retired 2024)"),
        "INTERACTION_TO_NEXT_PAINT": ("inp_ms", "Interaction to Next Paint"),
        "CUMULATIVE_LAYOUT_SHIFT_SCORE": ("cls", "Cumulative Layout Shift"),
        "FIRST_CONTENTFUL_PAINT_MS": ("fcp_ms", "First Contentful Paint"),
        "EXPERIMENTAL_TIME_TO_FIRST_BYTE": ("ttfb_ms", "Time to First Byte"),
    }
    for psi_key, (short, label) in mapping.items():
        m = metrics.get(psi_key)
        if m:
            field[short] = {
                "value": m.get("percentile"),
                "category": m.get("category", "").lower(),
                "label": label,
            }

    result["field_data"] = field if field else "No CrUX field data (site may have insufficient traffic)."
    result["overall_category"] = crux.get("overall_category", "unknown").lower()

    # Lab data audits (Lighthouse)
    audits = lh.get("audits", {})
    lab: dict = {}
    lab_keys = [
        ("first-contentful-paint", "FCP"),
        ("largest-contentful-paint", "LCP"),
        ("total-blocking-time", "TBT"),
        ("cumulative-layout-shift", "CLS"),
        ("speed-index", "Speed Index"),
        ("interactive", "Time to Interactive"),
    ]
    for key, label in lab_keys:
        a = audits.get(key, {})
        if a.get("numericValue") is not None:
            lab[label] = {
                "value": round(a["numericValue"], 1),
                "display": a.get("displayValue", ""),
                "score": a.get("score"),
            }
    result["lab_data"] = lab

    # Top opportunities
    opportunities: list[dict] = []
    for key, audit in audits.items():
        if audit.get("details", {}).get("type") == "opportunity":
            savings = audit.get("details", {}).get("overallSavingsMs")
            if savings and savings > 100:
                opportunities.append({
                    "audit": audit.get("title", key),
                    "savings_ms": int(savings),
                    "description": audit.get("description", "")[:200],
                })
    opportunities.sort(key=lambda x: x["savings_ms"], reverse=True)
    result["opportunities"] = opportunities[:5]

    # Diagnostics (warnings)
    diagnostics: list[str] = []
    for key, audit in audits.items():
        if audit.get("details", {}).get("type") == "table" and audit.get("score") == 0:
            diagnostics.append(audit.get("title", key))
    result["diagnostics"] = diagnostics[:5]

    return result


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: performance.py <url> [mobile|desktop]", file=sys.stderr)
        return 2
    url = sys.argv[1]
    strategy = sys.argv[2] if len(sys.argv) > 2 else "mobile"
    print(json.dumps(analyze(url, strategy), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
