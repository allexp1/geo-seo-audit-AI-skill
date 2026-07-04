#!/usr/bin/env python3
"""Fetch the ora.ai Agent Readiness score for a domain.

ora.ai scans a domain and scores 0-100 how well AI agents can discover,
understand, access, transact with, and operate the site. The read API is
free and keyless, rate-limited to ~10 req/min per IP.

  GET  https://ora.ai/api/score/{domain}   cached scan result (404 = never scanned)
  POST https://ora.ai/api/scan             fresh scan — takes minutes, and the
                                           domain appears on ora's PUBLIC leaderboard

Because a fresh scan publishes the domain publicly, this script only reads
the cached score by default. Pass --scan to explicitly request a new scan.

Output: score, grade, per-layer breakdown, and the top failing checks with
ora's own remediation recommendations (sorted by estimated score gain).
"""
from __future__ import annotations

import json
import sys
from urllib.parse import urlparse

import requests

UA = "Mozilla/5.0 (compatible; geo-skill/2.0)"
API = "https://ora.ai/api"
TIMEOUT = 30
SCAN_TIMEOUT = 300  # fresh scans run real agent probes and can take minutes

GRADE_SCALE = "A+ 95-100 | A 86-94 | B 70-85 | C 48-69 | D 28-47 | F 0-27"


def domain_of(url: str) -> str:
    parsed = urlparse(url if "://" in url else "https://" + url)
    return (parsed.netloc or parsed.path).split("/")[0].removeprefix("www.")


def summarize(data: dict) -> dict:
    layers = []
    recommendations = []
    for layer in data.get("layers", []):
        checks = layer.get("checks", [])
        failing = [c for c in checks if c.get("status") in ("fail", "warning")]
        layers.append({
            "id": layer.get("id"),
            "name": layer.get("name"),
            "score": layer.get("score"),
            "max_score": layer.get("maxScore"),
            "checks_total": len(checks),
            "checks_failing": len(failing),
        })
        for c in failing:
            if c.get("recommendation"):
                recommendations.append({
                    "layer": layer.get("name"),
                    "check": c.get("name"),
                    "status": c.get("status"),
                    "score": c.get("score"),
                    "max_score": c.get("maxScore"),
                    "est_score_gain": c.get("estScoreGain"),
                    "recommendation": c.get("recommendation"),
                })

    recommendations.sort(key=lambda r: (r["est_score_gain"] or 0), reverse=True)
    return {
        "source": "ora.ai",
        "domain": data.get("domain"),
        "score": data.get("score"),
        "max_score": data.get("maxScore"),
        "grade": data.get("grade"),
        "grade_scale": GRADE_SCALE,
        "scanned_at": data.get("scannedAt"),
        "analysis_status": data.get("analysisStatus"),
        "layers": layers,
        "top_recommendations": recommendations[:10],
        "total_recommendations": len(recommendations),
        "report_url": f"https://ora.ai/score/{data.get('domain')}",
        "badge_url": f"{API}/badge/{data.get('domain')}",
    }


def get_score(domain: str, allow_scan: bool = False) -> dict:
    try:
        r = requests.get(f"{API}/score/{domain}", headers={"User-Agent": UA}, timeout=TIMEOUT)
    except Exception as e:
        return {"source": "ora.ai", "domain": domain, "error": str(e)}

    if r.status_code == 200:
        return summarize(r.json())

    if r.status_code == 404:
        if not allow_scan:
            return {
                "source": "ora.ai",
                "domain": domain,
                "scanned": False,
                "note": (
                    "Domain has not been scanned by ora.ai yet. "
                    "Re-run with --scan to request one — note that scanned domains "
                    "appear on ora.ai's public leaderboard."
                ),
            }
        try:
            r = requests.post(
                f"{API}/scan",
                json={"url": domain},
                headers={"User-Agent": UA},
                timeout=SCAN_TIMEOUT,
            )
        except requests.exceptions.Timeout:
            return {
                "source": "ora.ai",
                "domain": domain,
                "error": "Scan timed out — try again in a few minutes; ora may still finish it server-side.",
            }
        except Exception as e:
            return {"source": "ora.ai", "domain": domain, "error": str(e)}
        if r.status_code == 200:
            return summarize(r.json())
        return {"source": "ora.ai", "domain": domain, "error": f"Scan failed: HTTP {r.status_code}"}

    if r.status_code == 429:
        retry = r.headers.get("Retry-After", "?")
        return {"source": "ora.ai", "domain": domain,
                "error": f"Rate limited (10 req/min/IP). Retry after {retry}s."}
    return {"source": "ora.ai", "domain": domain, "error": f"HTTP {r.status_code}"}


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print("usage: ora_score.py <url-or-domain> [--scan]", file=sys.stderr)
        return 2
    allow_scan = "--scan" in sys.argv
    result = get_score(domain_of(args[0]), allow_scan=allow_scan)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
