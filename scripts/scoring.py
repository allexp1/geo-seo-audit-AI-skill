#!/usr/bin/env python3
"""Single source of truth for all sub-scores and pillar weights.

Used by report.py and generate_pdf.py so the markdown and PDF reports can
never drift apart.

Three pillars, composite = mean:

  GEO   (AI search visibility): crawlers 30%, citability 30%, schema 20%,
                                llms.txt 10%, answer-first structure 10%
  SEO   (traditional):          on-page 50%, technical 50%
  AGENT (AI-agent usability):   agent_readiness.py score, used directly

The ora.ai score is external validation and is NOT folded into the composite.
"""
from __future__ import annotations

GEO_WEIGHTS = {"crawlers": 0.30, "citability": 0.30, "schema": 0.20,
               "llms": 0.10, "answer_first": 0.10}
SEO_WEIGHTS = {"onpage": 0.50, "technical": 0.50}


# --- GEO sub-scores -----------------------------------------------------------

def crawler_score(data: dict) -> tuple[float, str]:
    """Category-aware: blocking search/user-fetch bots removes the site from AI
    answers (heavy penalty); blocking training bots is a policy choice (light).
    Blocking Googlebot/Bingbot also kills AI Overviews/Copilot (score cap)."""
    if not data.get("robots_present"):
        return 100.0, "No robots.txt — all bots allowed by default."

    bots = data.get("bots", [])
    vis_bots = [b for b in bots if b.get("category") in ("search", "user-fetch")]
    train_bots = [b for b in bots if b.get("category") == "training"]
    vis_blocked = sum(1 for b in vis_bots if b.get("blocked_root"))
    train_blocked = sum(1 for b in train_bots if b.get("blocked_root"))

    vis_frac = 1 - vis_blocked / max(1, len(vis_bots))
    train_frac = 1 - train_blocked / max(1, len(train_bots))
    score = (0.85 * vis_frac + 0.15 * train_frac) * 100

    notes = []
    if vis_blocked:
        notes.append(f"{vis_blocked}/{len(vis_bots)} search/user-fetch bots blocked — "
                     "these remove the site from AI answers")
    if train_blocked:
        notes.append(f"{train_blocked}/{len(train_bots)} training bots blocked (policy choice)")
    if data.get("core_search_blocked"):
        score = min(score, 20.0)
        notes.append(f"{', '.join(data['core_search_blocked'])} blocked — also kills "
                     "AI Overviews/Copilot")
    if not notes:
        notes.append("No AI bots blocked at root.")
    return score, "; ".join(notes)


def citability_score(data: dict) -> tuple[float, str]:
    if data.get("passage_count", 0) == 0:
        return 0.0, "No analyzable passages found."
    return float(data["avg_score"]), f"Avg across {data['passage_count']} passages."


def answer_first_score(data: dict) -> tuple[float, str]:
    """Rewards a citable passage early in the page (most AI citations come from
    the first 30% of content) plus comparison formats (tables/ordered lists)."""
    if data.get("passage_count", 0) == 0:
        return 0.0, "No content to assess."
    score = 70.0 if data.get("answer_first") else min(50.0, float(data.get("early_content_avg_score", 0)))
    formats = data.get("comparison_formats", {})
    has_comparison = formats.get("tables", 0) > 0 or formats.get("ordered_lists", 0) > 0
    if has_comparison:
        score += 30.0
    note = ("Strong early answer" if data.get("answer_first") else "No strong passage in first 30%")
    note += "; comparison table/list present." if has_comparison else "; no comparison table/list."
    return min(100.0, score), note


def schema_score(data: dict) -> tuple[float, str]:
    found = data.get("types_found", [])
    if not found:
        return 0.0, "No JSON-LD blocks found."
    high_value = {"Organization", "WebSite", "Article", "BlogPosting", "Product",
                  "LocalBusiness", "FAQPage", "BreadcrumbList"}
    hits = len(set(found) & high_value)
    score = min(100.0, 20 + hits * 15 + (10 if data.get("organization_entity_linked") else 0))
    note = f"{len(found)} type(s); {hits} high-value"
    note += "; Organization entity-linked via sameAs." if data.get("organization_entity_linked") \
        else "; Organization not entity-linked (add sameAs)."
    if data.get("deprecated_rich_results"):
        dep = ", ".join(d["type"] for d in data["deprecated_rich_results"])
        note += f" Deprecated rich results present: {dep}."
    return score, note


def llms_score(data: dict) -> tuple[float, str]:
    full = data.get("llms_full_present", False)
    if data.get("present"):
        if data.get("analysis", {}).get("valid_shape"):
            return 100.0, "Present and well-formed" + (" (+ llms-full.txt)." if full else ".")
        return (70.0 if full else 60.0), "Present but incomplete."
    if full:
        return 20.0, "Only llms-full.txt present — add the /llms.txt index."
    return 0.0, "Not present."


def geo_score(crawlers: dict, cite: dict, schema: dict, llms: dict) -> tuple[float, dict]:
    """Returns (pillar score, {component: (score, note)})."""
    parts = {
        "crawlers": crawler_score(crawlers),
        "citability": citability_score(cite),
        "schema": schema_score(schema),
        "llms": llms_score(llms),
        "answer_first": answer_first_score(cite),
    }
    total = sum(GEO_WEIGHTS[k] * parts[k][0] for k in GEO_WEIGHTS)
    return total, parts


# --- SEO sub-scores -----------------------------------------------------------

def onpage_score(data: dict) -> tuple[float, str]:
    score = float(data.get("score", 0))
    notes = data.get("notes", [])
    return score, "; ".join(notes[:3]) if notes else "All on-page basics present."


def technical_score(data: dict) -> tuple[float, str]:
    score = 0
    notes: list[str] = []

    https = data.get("https", {})
    if https.get("http_to_https_redirect"):
        score += 20
    else:
        notes.append("no HTTP→HTTPS redirect")

    resp = data.get("response", {})
    sec_count = resp.get("security_headers_present", 0)
    score += min(25, sec_count * 5)
    if sec_count < 3:
        notes.append(f"only {sec_count}/6 security headers")

    if resp.get("content_encoding") in ("gzip", "br", "deflate", "zstd"):
        score += 10
    else:
        notes.append("no compression")

    elapsed = resp.get("elapsed_ms", 0)
    if elapsed and elapsed < 800:
        score += 15
    elif elapsed and elapsed < 2000:
        score += 8
        notes.append(f"slow ({elapsed} ms)")
    else:
        notes.append(f"very slow ({elapsed} ms)")

    cache = resp.get("cache_headers", {})
    if cache.get("Cache-Control") or cache.get("ETag"):
        score += 10
    else:
        notes.append("no caching headers")

    sm = data.get("sitemap", {})
    if sm.get("present"):
        score += 15
        if sm.get("referenced_in_robots"):
            score += 5
        else:
            notes.append("sitemap not in robots.txt")
    else:
        notes.append("no sitemap.xml")

    return float(min(100, score)), "; ".join(notes[:3]) if notes else "Solid technical baseline."


def seo_score(onpage: dict, technical: dict) -> tuple[float, dict]:
    parts = {
        "onpage": onpage_score(onpage),
        "technical": technical_score(technical),
    }
    total = sum(SEO_WEIGHTS[k] * parts[k][0] for k in SEO_WEIGHTS)
    return total, parts


# --- Composite ------------------------------------------------------------------

def composite_score(geo: float, seo: float, agent: float | None) -> float:
    """Mean of the available pillars (agent may be None if the check failed)."""
    pillars = [geo, seo] + ([agent] if agent is not None else [])
    return sum(pillars) / len(pillars)
