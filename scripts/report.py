#!/usr/bin/env python3
"""Run all checks against a URL and emit a markdown GEO + SEO report.

Three pillars:

GEO Score (0-100):   AI crawler access, citability, schema, llms.txt
SEO Score (0-100):   on-page, technical, keyword rankings, readability
Performance (0-100): Lighthouse score (optional — depends on PSI API availability)

Composite = (GEO + SEO) / 2  (performance is shown but not in composite).
"""
from __future__ import annotations

import sys
from urllib.parse import urlparse

from fetch_page import fetch
from crawler_check import check as check_crawlers
from citability import analyze as analyze_citability
from schema_extract import analyze as analyze_schema
from llmstxt import check as check_llmstxt
from onpage_seo import analyze as analyze_onpage
from technical_seo import analyze as analyze_technical
from keyword_extract import extract as extract_keywords
from keyword_rank import check_rankings
from readability import analyze as analyze_readability
from performance import analyze as analyze_performance


# --- GEO sub-scores -----------------------------------------------------------

def crawler_score(data: dict) -> tuple[float, str]:
    if not data.get("robots_present"):
        return 100.0, "No robots.txt — all bots allowed by default."
    summary = data.get("summary", {})
    blocked = summary.get("blocked", 0)
    total = summary.get("total", 1)
    pct_open = 1 - (blocked / total)
    return pct_open * 100, f"{blocked}/{total} known AI bots blocked at root."


def citability_score(data: dict) -> tuple[float, str]:
    if data.get("passage_count", 0) == 0:
        return 0.0, "No analyzable passages found."
    return float(data["avg_score"]), f"Avg across {data['passage_count']} passages."


def schema_score(data: dict) -> tuple[float, str]:
    found = data.get("types_found", [])
    if not found:
        return 0.0, "No JSON-LD blocks found."
    high_value = {"Organization", "WebSite", "Article", "BlogPosting", "Product",
                  "LocalBusiness", "FAQPage", "BreadcrumbList"}
    hits = len(set(found) & high_value)
    return min(100.0, 20 + hits * 15), f"{len(found)} type(s); {hits} high-value."


def llms_score(data: dict) -> tuple[float, str]:
    if data.get("present"):
        if data.get("analysis", {}).get("valid_shape"):
            return 100.0, "Present and well-formed."
        return 60.0, "Present but incomplete."
    return 0.0, "Not present."


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


# --- rendering helpers --------------------------------------------------------

def render_bots_table(bots: list[dict]) -> str:
    lines = ["| Bot | Vendor | Purpose | Status |", "|---|---|---|---|"]
    for b in bots:
        if b.get("blocked_root"):
            status = "BLOCKED"
        elif b.get("source") == "explicit":
            status = "explicitly allowed"
        elif b.get("source") == "wildcard":
            status = "via wildcard"
        elif b.get("source") == "no-robots":
            status = "no robots.txt"
        else:
            status = "default-allow"
        lines.append(f"| `{b['token']}` | {b['vendor']} | {b['purpose']} | {status} |")
    return "\n".join(lines)


def yes_no(v) -> str:
    return "yes" if v else "no"


# --- report builder -----------------------------------------------------------

def build_report(url: str) -> str:
    # Collect all data
    page = fetch(url)
    crawlers = check_crawlers(url)
    cite = analyze_citability(url)
    schema = analyze_schema(url)
    llms = check_llmstxt(url)
    onpage = analyze_onpage(url)
    technical = analyze_technical(url)
    keywords = extract_keywords(url)
    read = analyze_readability(url)

    # Keyword rankings: use top extracted keywords (limited to 5 to stay within rate limits)
    parsed = urlparse(page["final_url"])
    domain = parsed.netloc.lstrip("www.")
    kw_list = [k["keyword"] for k in keywords.get("keywords", []) if " " in k["keyword"]][:3]
    kw_list += [k["keyword"] for k in keywords.get("keywords", []) if " " not in k["keyword"]][:2]
    kw_list = kw_list[:5]
    rankings = check_rankings(domain, kw_list) if kw_list else None

    # Performance (PageSpeed Insights — may fail due to rate limits)
    perf = analyze_performance(url)

    # GEO scoring
    s_crawl, n_crawl = crawler_score(crawlers)
    s_cite, n_cite = citability_score(cite)
    s_schema, n_schema = schema_score(schema)
    s_llms, n_llms = llms_score(llms)
    geo = 0.35 * s_crawl + 0.35 * s_cite + 0.20 * s_schema + 0.10 * s_llms

    # SEO scoring
    s_onpage, n_onpage = onpage_score(onpage)
    s_tech, n_tech = technical_score(technical)
    seo = 0.5 * s_onpage + 0.5 * s_tech

    composite = (geo + seo) / 2

    md: list[str] = []

    # --- Header ---
    md.append(f"# GEO + SEO Audit — {parsed.netloc}\n")
    md.append(f"URL: {page['final_url']}  ")
    md.append(f"Status: {page['status']}  ")
    md.append(f"Page size: {page['html_bytes']:,} bytes\n")

    # --- Scores ---
    md.append("## Scores\n")
    md.append("| | Score | |")
    md.append("|---|---:|---|")
    md.append(f"| **Composite** | **{composite:.0f} / 100** | |")
    md.append(f"| GEO (AI search) | {geo:.0f} / 100 | crawlers, citability, schema, llms.txt |")
    md.append(f"| SEO (traditional) | {seo:.0f} / 100 | on-page, technical |")
    if perf.get("lighthouse_score") is not None:
        md.append(f"| Performance | {perf['lighthouse_score']} / 100 | Lighthouse ({perf['strategy']}) |")
    md.append("")

    md.append("### GEO breakdown\n")
    md.append("| Category | Weight | Score | Notes |")
    md.append("|---|---|---:|---|")
    md.append(f"| AI Crawler Access | 35% | {s_crawl:.0f} | {n_crawl} |")
    md.append(f"| Citability | 35% | {s_cite:.0f} | {n_cite} |")
    md.append(f"| Schema Coverage | 20% | {s_schema:.0f} | {n_schema} |")
    md.append(f"| llms.txt | 10% | {s_llms:.0f} | {n_llms} |")
    md.append("")

    md.append("### SEO breakdown\n")
    md.append("| Category | Weight | Score | Notes |")
    md.append("|---|---|---:|---|")
    md.append(f"| On-Page SEO | 50% | {s_onpage:.0f} | {n_onpage} |")
    md.append(f"| Technical SEO | 50% | {s_tech:.0f} | {n_tech} |")
    md.append("")

    # ---------- On-page SEO ----------
    md.append("## On-page SEO\n")
    md.append(f"- **Title** ({onpage['title']['length']} chars): {onpage['title']['value'] or '_(missing)_'}")
    md.append(f"- **Meta description** ({onpage['meta_description']['length']} chars): {onpage['meta_description']['value'] or '_(missing)_'}")
    md.append(f"- **Headings:** {len(onpage['headings']['h1'])} H1, {onpage['headings']['h2_count']} H2, {onpage['headings']['h3_count']} H3")
    md.append(f"- **Canonical:** {onpage['canonical'] or '_(missing)_'}")
    md.append(f"- **Robots meta:** {onpage['robots_meta'] or '_(none)_'}")
    md.append(f"- **Lang:** {onpage['lang'] or '_(missing)_'} | **Charset:** {onpage['charset'] or '_(missing)_'} | **Viewport:** {onpage['viewport'] or '_(missing)_'}")
    og = onpage["open_graph"]
    og_present = sum(1 for v in og.values() if v)
    md.append(f"- **Open Graph:** {og_present}/{len(og)} fields")
    tw = onpage["twitter_card"]
    tw_present = sum(1 for v in tw.values() if v)
    md.append(f"- **Twitter Card:** {tw_present}/{len(tw)} fields")
    img = onpage["images"]
    md.append(f"- **Images:** {img['total']} total, {img['with_alt']} with alt, {img['decorative']} decorative")
    lk = onpage["links"]
    md.append(f"- **Links:** {lk['internal']} internal, {lk['external']} external, {lk['nofollow']} nofollow")
    md.append(f"- **Word count:** {onpage['word_count']}")
    md.append(f"- **Favicon:** {onpage['favicon'] or '_(missing)_'}\n")

    # ---------- Technical SEO ----------
    md.append("## Technical SEO\n")
    https = technical["https"]
    md.append(f"- **HTTPS upgrade:** {yes_no(https.get('http_to_https_redirect'))}")
    if https.get("redirect_chain_length"):
        md.append(f"- **Redirect chain:** {https['redirect_chain_length']} hops")
    resp = technical["response"]
    md.append(f"- **Response time:** {resp['elapsed_ms']} ms")
    md.append(f"- **Compression:** {resp['content_encoding'] or '_(none)_'}")
    md.append(f"- **Server:** {resp.get('server') or '_(hidden)_'}")
    md.append("- **Security headers:**")
    for h, v in resp["security_headers"].items():
        md.append(f"  - `{h}`: {'present' if v else '_(missing)_'}")
    cache_lines = [f"`{h}`: {v[:80]}" for h, v in resp["cache_headers"].items() if v]
    if cache_lines:
        md.append("- **Cache:** " + " | ".join(cache_lines))
    sm = technical["sitemap"]
    if sm.get("present"):
        entries = sm.get("url_count", sm.get("sitemap_count", "?"))
        md.append(f"- **Sitemap:** {sm['url']} ({sm.get('type', '')}, {entries} entries)")
        md.append(f"- **In robots.txt:** {yes_no(sm.get('referenced_in_robots'))}")
    else:
        md.append("- **Sitemap:** not found")
    md.append("")

    # ---------- Keywords ----------
    md.append("## Keywords\n")
    md.append("### Extracted from page\n")
    md.append("| Keyword | Score | Freq | Found in |")
    md.append("|---|---:|---:|---|")
    for k in keywords.get("keywords", [])[:15]:
        loc = ", ".join(k["found_in"]) if k["found_in"] else "body"
        md.append(f"| {k['keyword']} | {k['score']} | {k['frequency']} | {loc} |")
    md.append("")

    if rankings and rankings.get("results"):
        engine_label = rankings.get("method", "search engine")
        md.append(f"### Search rankings ({engine_label})\n")
        md.append("| Keyword | Position | Top 3 competitors |")
        md.append("|---|---:|---|")
        for r in rankings["results"]:
            pos = r.get("top_position")
            pos_str = f"#{pos}" if pos else "not in top 30"
            top3 = ", ".join(
                urlparse(t["url"]).netloc.lstrip("www.") for t in r.get("top_3", [])
            )
            md.append(f"| {r['keyword']} | {pos_str} | {top3} |")
        summ = rankings.get("summary", {})
        if summ.get("best_position"):
            md.append(f"\n**Best position:** #{summ['best_position']} | **Avg:** #{summ['avg_position']}")
        if summ.get("not_in_results"):
            md.append(f"**Not ranking for:** {', '.join(summ['not_in_results'])}")
        md.append("")

    # ---------- Readability ----------
    md.append("## Readability\n")
    if read.get("error"):
        md.append(f"_{read['error']}_\n")
    else:
        md.append(f"- **Flesch Reading Ease:** {read['flesch_reading_ease']} ({read['level']})")
        md.append(f"- **Flesch-Kincaid Grade:** {read['flesch_kincaid_grade']}")
        md.append(f"- **Gunning Fog Index:** {read['gunning_fog']}")
        md.append(f"- **Avg sentence length:** {read['avg_words_per_sentence']} words")
        md.append(f"- **Complex words:** {read['complex_word_pct']}%")
        md.append(f"- **AI citation friendly:** {yes_no(read['ai_citation_friendly'])} — {read['note']}\n")

    # ---------- Performance ----------
    md.append("## Performance (Lighthouse)\n")
    if perf.get("error"):
        md.append(f"_{perf['error']}_\n")
    elif perf.get("lighthouse_score") is not None:
        md.append(f"- **Score:** {perf['lighthouse_score']}/100 ({perf['strategy']})")
        md.append(f"- **Overall CrUX:** {perf.get('overall_category', 'unknown')}")
        # Field data (real users)
        fd = perf.get("field_data")
        if isinstance(fd, dict) and fd:
            md.append("\n**Core Web Vitals (field data):**\n")
            md.append("| Metric | Value | Rating |")
            md.append("|---|---:|---|")
            for key, info in fd.items():
                val = info.get("value")
                cat = info.get("category", "")
                label = info.get("label", key)
                unit = " ms" if key.endswith("_ms") else ""
                rating = {"good": "GOOD", "needs_improvement": "NEEDS WORK", "poor": "POOR"}.get(cat, cat)
                md.append(f"| {label} | {val}{unit} | {rating} |")
        elif isinstance(fd, str):
            md.append(f"\n_{fd}_")
        # Lab data
        lab = perf.get("lab_data", {})
        if lab:
            md.append("\n**Lab data:**\n")
            md.append("| Metric | Value |")
            md.append("|---|---|")
            for key, info in lab.items():
                md.append(f"| {key} | {info.get('display', info.get('value', ''))} |")
        # Opportunities
        opps = perf.get("opportunities", [])
        if opps:
            md.append("\n**Top opportunities:**\n")
            for o in opps:
                md.append(f"- **{o['audit']}** — save ~{o['savings_ms']} ms")
        md.append("")
    else:
        md.append("_No performance data available._\n")

    # ---------- AI crawlers ----------
    md.append("## AI crawlers (robots.txt)\n")
    md.append(f"Source: `{crawlers['robots_url']}`")
    if crawlers.get("robots_present"):
        md.append(f" ({crawlers.get('robots_size', 0)} bytes)\n")
    else:
        md.append(" _(no robots.txt — all bots allowed)_\n")
    md.append(render_bots_table(crawlers.get("bots", [])))
    md.append("")

    # ---------- Citability ----------
    md.append("## Citability\n")
    if cite.get("passage_count", 0) == 0:
        md.append(f"_{cite.get('note', 'No passages found.')}_\n")
    else:
        md.append(f"- Passages analyzed: **{cite['passage_count']}**")
        md.append(f"- In optimal 100-200 word band: **{cite['passages_in_optimal_band']}**")
        md.append(f"- Average score: **{cite['avg_score']}**\n")
        md.append("**Top 3 most citable passages:**\n")
        for i, p in enumerate(cite["top"][:3], 1):
            md.append(f"{i}. _(score {p['score']}, {p['words']} words)_  ")
            md.append(f"   {p['preview']}\n")

    # ---------- Schema ----------
    md.append("## Schema (JSON-LD)\n")
    if schema["block_count"] == 0:
        md.append("_No JSON-LD blocks found. See `schema/` for templates._\n")
    else:
        md.append(f"- Blocks: **{schema['block_count']}**")
        md.append(f"- Types: {', '.join(f'`{t}`' for t in schema['types_found'])}")
        if schema["common_types_missing"]:
            md.append(f"- Missing: {', '.join(f'`{t}`' for t in schema['common_types_missing'])}")
        if schema["field_checks"]:
            for t, fc in schema["field_checks"].items():
                if fc["missing"]:
                    md.append(f"- `{t}` missing: {', '.join(fc['missing'])}")
        md.append("")

    # ---------- llms.txt ----------
    md.append("## llms.txt\n")
    if llms.get("present"):
        a = llms["analysis"]
        md.append(f"- Present at `{llms['url']}` ({a['size']} bytes)")
        md.append(f"- H1: {yes_no(a['starts_with_h1'])} | Blockquote: {yes_no(a['has_summary_blockquote'])} | Sections: {a['section_count']} | Links: {a['link_count']}\n")
    else:
        md.append(f"- Not present at `{llms['url']}`")
        md.append("- Suggested template:\n")
        md.append("```markdown")
        md.append(llms.get("suggested_template", "").rstrip())
        md.append("```\n")

    # ---------- Actions: SEO ----------
    seo_actions: list[tuple[int, str]] = []

    if not onpage["title"]["value"]:
        seo_actions.append((1, "Add a `<title>` (30-60 chars)."))
    elif not (30 <= onpage["title"]["length"] <= 60):
        seo_actions.append((2, f"Tighten title to 30-60 chars (currently {onpage['title']['length']})."))
    if not onpage["meta_description"]["value"]:
        seo_actions.append((1, "Add a meta description (120-160 chars)."))
    elif not (120 <= onpage["meta_description"]["length"] <= 160):
        seo_actions.append((2, f"Adjust meta description to 120-160 chars (currently {onpage['meta_description']['length']})."))
    if len(onpage["headings"]["h1"]) != 1:
        seo_actions.append((1, f"Use exactly one H1 (currently {len(onpage['headings']['h1'])})."))
    if not onpage["canonical"]:
        seo_actions.append((2, "Add a canonical link."))
    if not onpage["viewport"]:
        seo_actions.append((1, "Add mobile viewport meta tag."))
    if not onpage["lang"]:
        seo_actions.append((2, "Add `lang` attribute to `<html>`."))
    og_missing = [f for f in ["og:title", "og:description", "og:image"] if not onpage["open_graph"].get(f)]
    if og_missing:
        seo_actions.append((3, f"Add Open Graph: {', '.join(og_missing)}."))
    if not onpage["twitter_card"].get("twitter:card"):
        seo_actions.append((3, "Add `twitter:card` meta."))
    img = onpage["images"]
    if img["total"] > 0 and (img["with_alt"] + img["decorative"]) / img["total"] < 0.9:
        seo_actions.append((2, f"Add alt text to images ({img['with_alt']}/{img['total']} covered)."))
    if "noindex" in onpage["robots_meta"]:
        seo_actions.append((1, "Page has `noindex` — confirm this is intentional."))

    if not technical["https"].get("http_to_https_redirect"):
        seo_actions.append((1, "Force HTTP→HTTPS redirect."))
    sec = technical["response"]["security_headers"]
    missing_sec = [h for h in ["Strict-Transport-Security", "X-Content-Type-Options", "Content-Security-Policy"] if not sec.get(h)]
    if missing_sec:
        seo_actions.append((2, f"Add security headers: {', '.join(missing_sec)}."))
    if technical["response"].get("content_encoding") not in ("gzip", "br", "deflate", "zstd"):
        seo_actions.append((1, "Enable gzip or brotli compression."))
    if technical["response"].get("elapsed_ms", 0) >= 2000:
        seo_actions.append((1, f"Slow TTFB ({technical['response']['elapsed_ms']} ms) — investigate server/CDN."))
    if not technical["sitemap"].get("present"):
        seo_actions.append((2, "Publish a `sitemap.xml` and reference in `robots.txt`."))

    # Keyword-based actions
    if rankings:
        not_ranking = rankings.get("summary", {}).get("not_in_results", [])
        if not_ranking:
            seo_actions.append((2, f"Not ranking for: {', '.join(not_ranking[:3])}. Create dedicated pages or optimize content for these keywords."))

    # Readability actions
    if not read.get("error"):
        if read["flesch_reading_ease"] < 40:
            seo_actions.append((3, f"Content is hard to read (Flesch {read['flesch_reading_ease']}). Simplify sentences for broader reach."))

    # Performance actions
    if perf.get("lighthouse_score") is not None and perf["lighthouse_score"] < 50:
        seo_actions.append((1, f"Lighthouse performance score is {perf['lighthouse_score']}/100. Check top opportunities above."))

    # ---------- Actions: GEO ----------
    geo_actions: list[tuple[int, str]] = []

    blocked_bots = [b for b in crawlers.get("bots", []) if b.get("blocked_root")]
    if blocked_bots:
        names = ", ".join(b["token"] for b in blocked_bots[:5])
        geo_actions.append((1, f"AI bots blocked: {names}. Review robots.txt."))
    if cite.get("passage_count", 0) == 0:
        geo_actions.append((1, "No analyzable passages — page is content-thin or JS-rendered."))
    elif cite.get("passages_in_optimal_band", 0) < 3:
        geo_actions.append((2, "Restructure content into self-contained 100-200 word answer blocks."))
    if schema["block_count"] == 0:
        geo_actions.append((2, "Add JSON-LD: Organization + WebSite at minimum. Templates in `schema/`."))
    elif "Organization" in schema["common_types_missing"]:
        geo_actions.append((2, "Add Organization schema with `sameAs` links."))
    if not llms.get("present"):
        geo_actions.append((3, "Publish `/llms.txt`."))
    elif llms.get("analysis", {}).get("link_count", 0) == 0:
        geo_actions.append((2, "llms.txt has no links — add markdown links to key pages."))
    if not read.get("error") and not read.get("ai_citation_friendly"):
        if read["flesch_reading_ease"] < 50:
            geo_actions.append((3, "Content reads at college level — simplify for AI citation (target Flesch 50-70)."))

    md.append("## Prioritized actions — SEO\n")
    if not seo_actions:
        md.append("_Solid SEO baseline. No high-priority fixes detected._\n")
    else:
        seo_actions.sort(key=lambda x: x[0])
        for prio, text in seo_actions:
            md.append(f"- **{['', 'P1', 'P2', 'P3'][prio]}** — {text}")
        md.append("")

    md.append("## Prioritized actions — GEO\n")
    if not geo_actions:
        md.append("_Solid GEO baseline. No high-priority fixes detected._")
    else:
        geo_actions.sort(key=lambda x: x[0])
        for prio, text in geo_actions:
            md.append(f"- **{['', 'P1', 'P2', 'P3'][prio]}** — {text}")

    return "\n".join(md)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: report.py <url>", file=sys.stderr)
        return 2
    print(build_report(sys.argv[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
