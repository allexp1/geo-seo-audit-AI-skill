#!/usr/bin/env python3
"""Run all checks against a URL and emit a markdown GEO + SEO + Agent report.

Three pillars (composite = their mean):

GEO Score (0-100):   AI search visibility — crawler access, citability,
                     schema, llms.txt, answer-first structure
SEO Score (0-100):   traditional search — on-page, technical
AGENT Score (0-100): AI-agent usability — parseability, labeled interactions,
                     agent interfaces (MCP/NLWeb/llms.txt), bot-wall access

Shown but not in composite: Lighthouse performance, keyword rankings,
readability, and the external ora.ai Agent Readiness score.
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
from agent_readiness import analyze as analyze_agent
from ora_score import get_score as get_ora_score, domain_of
import scoring


# --- rendering helpers --------------------------------------------------------

def render_bots_table(bots: list[dict]) -> str:
    lines = ["| Bot | Vendor | Category | Purpose | Status |", "|---|---|---|---|---|"]
    for b in bots:
        if b.get("blocked_root"):
            status = "**BLOCKED**"
        elif b.get("source") == "explicit":
            status = "explicitly allowed"
        elif b.get("source") == "wildcard":
            status = "via wildcard"
        elif b.get("source") == "no-robots":
            status = "no robots.txt"
        else:
            status = "default-allow"
        lines.append(f"| `{b['token']}` | {b['vendor']} | {b.get('category', '')} | {b['purpose']} | {status} |")
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
    agent = analyze_agent(url)

    # Keyword rankings: use top extracted keywords (limited to 5 to stay within rate limits)
    parsed = urlparse(page["final_url"])
    domain = parsed.netloc.lstrip("www.")
    kw_list = [k["keyword"] for k in keywords.get("keywords", []) if " " in k["keyword"]][:3]
    kw_list += [k["keyword"] for k in keywords.get("keywords", []) if " " not in k["keyword"]][:2]
    kw_list = kw_list[:5]
    rankings = check_rankings(domain, kw_list) if kw_list else None

    # Performance (PageSpeed Insights — may fail due to rate limits)
    perf = analyze_performance(url)

    # ora.ai external score (cached read only; never triggers a public scan)
    ora = get_ora_score(domain_of(page["final_url"]))

    # Scoring (shared module — same numbers as the PDF)
    geo, geo_parts = scoring.geo_score(crawlers, cite, schema, llms)
    seo, seo_parts = scoring.seo_score(onpage, technical)
    agent_val = agent.get("score") if not agent.get("error") else None
    composite = scoring.composite_score(geo, seo, agent_val)

    md: list[str] = []

    # --- Header ---
    md.append(f"# GEO + SEO + Agent Audit — {parsed.netloc}\n")
    md.append(f"URL: {page['final_url']}  ")
    md.append(f"Status: {page['status']}  ")
    md.append(f"Page size: {page['html_bytes']:,} bytes\n")

    # --- Scores ---
    md.append("## Scores\n")
    md.append("| | Score | |")
    md.append("|---|---:|---|")
    md.append(f"| **Composite** | **{composite:.0f} / 100** | mean of the pillars below |")
    md.append(f"| GEO (AI search) | {geo:.0f} / 100 | crawlers, citability, schema, llms.txt, answer-first |")
    md.append(f"| SEO (traditional) | {seo:.0f} / 100 | on-page, technical |")
    if agent_val is not None:
        md.append(f"| AGENT (AI-agent usability) | {agent_val:.0f} / 100 | parseability, interactions, interfaces, access |")
    if perf.get("lighthouse_score") is not None:
        md.append(f"| Performance | {perf['lighthouse_score']} / 100 | Lighthouse ({perf['strategy']}), not in composite |")
    if ora.get("score") is not None:
        md.append(f"| ora.ai Agent Readiness | {ora['score']} / {ora.get('max_score', 100)} (grade {ora.get('grade')}) | external, not in composite |")
    md.append("")

    md.append("### GEO breakdown\n")
    md.append("| Category | Weight | Score | Notes |")
    md.append("|---|---|---:|---|")
    labels = {"crawlers": "AI Crawler Access", "citability": "Citability",
              "schema": "Schema Coverage", "llms": "llms.txt", "answer_first": "Answer-First Structure"}
    for key, label in labels.items():
        s, n = geo_parts[key]
        md.append(f"| {label} | {scoring.GEO_WEIGHTS[key]:.0%} | {s:.0f} | {n} |")
    md.append("")

    md.append("### SEO breakdown\n")
    md.append("| Category | Weight | Score | Notes |")
    md.append("|---|---|---:|---|")
    md.append(f"| On-Page SEO | 50% | {seo_parts['onpage'][0]:.0f} | {seo_parts['onpage'][1]} |")
    md.append(f"| Technical SEO | 50% | {seo_parts['technical'][0]:.0f} | {seo_parts['technical'][1]} |")
    md.append("")

    if agent_val is not None:
        md.append("### AGENT breakdown\n")
        md.append("| Category | Weight | Score | Key numbers |")
        md.append("|---|---|---:|---|")
        cats = agent["categories"]
        cp = cats["content_parseability"]
        md.append(f"| Content parseability | 35% | {cp['score']:.0f} | "
                  f"{cp['word_count_no_js']} words without JS, {cp['text_to_markup_pct']}% text ratio |")
        ir = cats["interaction_readiness"]
        md.append(f"| Interaction readiness | 25% | {ir['score']:.0f} | "
                  f"{ir['unlabeled_fields']}/{ir['form_fields']} fields unlabeled, "
                  f"{ir['without_accessible_name']}/{ir['buttons_links']} controls unnamed |")
        ai_if = cats["agent_interfaces"]
        found_names = ", ".join(f["name"] for f in ai_if["found"]) or "none"
        md.append(f"| Agent interfaces | 25% | {ai_if['score']:.0f} | found: {found_names} |")
        ac = cats["access"]
        md.append(f"| Access | 15% | {ac['score']:.0f} | "
                  f"bot wall: {yes_no(ac['bot_wall_detected'])} "
                  f"(bot UA → {ac['bot_ua_status']}, browser UA → {ac['browser_ua_status']}) |")
        md.append("")

    # ---------- On-page SEO ----------
    md.append("## On-page SEO\n")
    md.append(f"- **Title** ({onpage['title']['length']} chars): {onpage['title']['value'] or '_(missing)_'}")
    md.append(f"- **Meta description** ({onpage['meta_description']['length']} chars): {onpage['meta_description']['value'] or '_(missing)_'}")
    md.append(f"- **Headings:** {len(onpage['headings']['h1'])} H1, {onpage['headings']['h2_count']} H2, {onpage['headings']['h3_count']} H3")
    md.append(f"- **Canonical:** {onpage['canonical'] or '_(missing)_'}")
    md.append(f"- **Robots meta:** {onpage['robots_meta'] or '_(none)_'}")
    sc = onpage.get("snippet_controls", {})
    if sc.get("nosnippet") or sc.get("max_snippet") or sc.get("data_nosnippet_blocks"):
        md.append(f"- **Snippet controls:** nosnippet={yes_no(sc.get('nosnippet'))}, "
                  f"{sc.get('max_snippet') or 'no max-snippet'}, "
                  f"{sc.get('data_nosnippet_blocks', 0)} data-nosnippet block(s) — these also limit "
                  "what AI Overviews/AI Mode may quote")
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
    if resp.get("behind_cloudflare"):
        md.append("- **Cloudflare:** yes — Cloudflare blocks AI training crawlers **by default** "
                  "since July 2025 (and mixed-use crawlers on ad-monetized pages from 2026-09-15), "
                  "regardless of robots.txt. Check AI Crawl Control in the dashboard.")
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
    if crawlers.get("core_search_warning"):
        md.append(f"> **WARNING:** {crawlers['core_search_warning']}\n")
    if crawlers.get("content_signals"):
        md.append(f"**Content-Signal lines:** {'; '.join(crawlers['content_signals'])} "
                  "(Cloudflare's machine-readable AI policy)\n")
    if crawlers.get("stale_tokens"):
        for st in crawlers["stale_tokens"]:
            md.append(f"- Stale token `{st['token']}` in robots.txt — {st['note']}")
        md.append("")
    cf = crawlers.get("cloudflare", {})
    if cf.get("behind_cloudflare"):
        md.append(f"> {cf['note']}\n")
    md.append(render_bots_table(crawlers.get("bots", [])))
    md.append("")

    # ---------- Citability ----------
    md.append("## Citability\n")
    if cite.get("passage_count", 0) == 0:
        md.append(f"_{cite.get('note', 'No passages found.')}_\n")
    else:
        md.append(f"- Passages analyzed: **{cite['passage_count']}**")
        md.append(f"- In optimal 100-200 word band: **{cite['passages_in_optimal_band']}**")
        md.append(f"- Average score: **{cite['avg_score']}**")
        md.append(f"- Answer-first: **{yes_no(cite.get('answer_first'))}** — {cite.get('answer_first_note', '')}")
        fm = cite.get("comparison_formats", {})
        md.append(f"- Comparison formats: {fm.get('tables', 0)} table(s), "
                  f"{fm.get('ordered_lists', 0)} ordered list(s)\n")
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
        for dep in schema.get("deprecated_rich_results", []):
            md.append(f"- `{dep['type']}`: {dep['note']}")
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
        md.append(f"- H1: {yes_no(a['starts_with_h1'])} | Blockquote: {yes_no(a['has_summary_blockquote'])} | Sections: {a['section_count']} | Links: {a['link_count']}")
    else:
        md.append(f"- Not present at `{llms['url']}`")
    md.append(f"- llms-full.txt: {yes_no(llms.get('llms_full_present'))}")
    md.append(f"- _{llms.get('value_note', '')}_\n")
    if not llms.get("present"):
        md.append("- Suggested template:\n")
        md.append("```markdown")
        md.append(llms.get("suggested_template", "").rstrip())
        md.append("```\n")

    # ---------- AI Agent Readiness ----------
    md.append("## AI Agent Readiness\n")
    if agent.get("error"):
        md.append(f"_{agent['error']}_\n")
    else:
        cats = agent["categories"]
        ai_if = cats["agent_interfaces"]
        if ai_if["found"]:
            md.append("**Agent interfaces detected:**\n")
            for f in ai_if["found"]:
                note = f" — {f['note']}" if f.get("note") else ""
                md.append(f"- `{f['path']}` ({f['name']}){note}")
            md.append("")
        if cats["interaction_readiness"].get("webmcp"):
            md.append(f"- {cats['interaction_readiness']['webmcp_note']}\n")
        md.append("**What the owner should do for AI agents** (see prioritized list below):\n")
        for r in agent.get("recommendations", [])[:8]:
            md.append(f"- **P{r['priority']}** [{r['category']}] {r['text']}")
        md.append("")

    # ---------- ora.ai ----------
    md.append("## ora.ai Agent Readiness (external)\n")
    if ora.get("score") is not None:
        md.append(f"- **Score:** {ora['score']}/{ora.get('max_score', 100)} — grade **{ora.get('grade')}** "
                  f"(scale: {ora.get('grade_scale', '')})")
        md.append(f"- Scanned: {ora.get('scanned_at', 'unknown')} | Full report: {ora.get('report_url')}")
        md.append("\n| Layer | Score | Failing checks |")
        md.append("|---|---:|---:|")
        for layer in ora.get("layers", []):
            md.append(f"| {layer['name']} | {layer['score']}/{layer['max_score']} | {layer['checks_failing']}/{layer['checks_total']} |")
        if ora.get("top_recommendations"):
            md.append("\n**Top ora.ai recommendations (by estimated score gain):**\n")
            for rec in ora["top_recommendations"][:5]:
                gain = f" (+{rec['est_score_gain']})" if rec.get("est_score_gain") else ""
                md.append(f"- [{rec['layer']}] **{rec['check']}**{gain}: {rec['recommendation']}")
        md.append("")
    elif ora.get("scanned") is False:
        md.append(f"_{ora.get('note', 'Not scanned.')}_\n")
    else:
        md.append(f"_Unavailable: {ora.get('error', 'unknown error')}_\n")

    # ---------- Actions: SEO ----------
    seo_actions: list[tuple[int, str]] = []

    if not onpage["title"]["value"]:
        seo_actions.append((1, "Add a `<title>` (50-60 chars, include entity names)."))
    elif not (30 <= onpage["title"]["length"] <= 60):
        seo_actions.append((2, f"Tighten title to 50-60 chars (currently {onpage['title']['length']})."))
    if not onpage["meta_description"]["value"]:
        seo_actions.append((1, "Add a meta description (140-160 chars, answer-aligned — it doubles as AI citation-card text)."))
    elif not (120 <= onpage["meta_description"]["length"] <= 160):
        seo_actions.append((2, f"Adjust meta description to 140-160 chars (currently {onpage['meta_description']['length']})."))
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
        seo_actions.append((1, "Page has `noindex` — confirm this is intentional (it also removes the page from AI Overviews)."))

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

    if crawlers.get("core_search_blocked"):
        geo_actions.append((1, crawlers["core_search_warning"]))
    vis_blocked = [b for b in crawlers.get("bots", [])
                   if b.get("blocked_root") and b.get("category") in ("search", "user-fetch")]
    if vis_blocked:
        names = ", ".join(b["token"] for b in vis_blocked[:5])
        geo_actions.append((1, f"Search/user-fetch AI bots blocked: {names}. These remove the site "
                               "from AI answers — unblock unless that is deliberate."))
    train_blocked = [b for b in crawlers.get("bots", [])
                     if b.get("blocked_root") and b.get("category") == "training"]
    if train_blocked:
        names = ", ".join(b["token"] for b in train_blocked[:5])
        geo_actions.append((3, f"Training bots blocked: {names}. Legitimate policy choice — just "
                               "confirm it matches your intent (it limits presence in future model knowledge)."))
    for st in crawlers.get("stale_tokens", []):
        geo_actions.append((3, f"Remove stale robots.txt token `{st['token']}` — {st['note']}"))
    if crawlers.get("cloudflare", {}).get("behind_cloudflare"):
        geo_actions.append((2, "Behind Cloudflare: verify AI Crawl Control settings — Cloudflare "
                               "blocks AI training crawlers by default since July 2025, regardless of robots.txt."))
    if not crawlers.get("content_signals"):
        geo_actions.append((3, "Consider adding a `Content-Signal:` line to robots.txt "
                               "(e.g. `search=yes, ai-input=yes, ai-train=no`) to express AI policy machine-readably."))
    if cite.get("passage_count", 0) == 0:
        geo_actions.append((1, "No analyzable passages — page is content-thin or JS-rendered."))
    else:
        if cite.get("passages_in_optimal_band", 0) < 3:
            geo_actions.append((2, "Restructure content into self-contained 100-200 word answer blocks."))
        if not cite.get("answer_first"):
            geo_actions.append((2, "Lead with a direct answer: ~44% of AI citations come from the "
                                   "first 30% of page content, and this page has no strong early passage."))
    if schema["block_count"] == 0:
        geo_actions.append((2, "Add JSON-LD: Organization + WebSite at minimum. Templates in `schema/`."))
    else:
        if "Organization" in schema["common_types_missing"]:
            geo_actions.append((2, "Add Organization schema with `sameAs` links."))
        elif not schema.get("organization_entity_linked"):
            geo_actions.append((2, "Add `sameAs` links (Wikipedia/Wikidata/LinkedIn/GitHub) to the "
                                   "Organization schema — entity linking is how AI engines resolve who you are."))
        for dep in schema.get("deprecated_rich_results", []):
            geo_actions.append((3, f"`{dep['type']}` markup: {dep['note']}"))
    if not llms.get("present"):
        geo_actions.append((3, "Publish `/llms.txt` (agent-readiness signal; not used by Google Search)."))
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
        md.append("_Solid GEO baseline. No high-priority fixes detected._\n")
    else:
        geo_actions.sort(key=lambda x: x[0])
        for prio, text in geo_actions:
            md.append(f"- **{['', 'P1', 'P2', 'P3'][prio]}** — {text}")
        md.append("")

    md.append("## Prioritized actions — AI agents\n")
    agent_actions = agent.get("recommendations", []) if not agent.get("error") else []
    ora_recs = ora.get("top_recommendations", [])[:3] if ora.get("score") is not None else []
    if not agent_actions and not ora_recs:
        md.append("_Solid agent-readiness baseline. No high-priority fixes detected._")
    else:
        for r in agent_actions:
            md.append(f"- **P{r['priority']}** — [{r['category']}] {r['text']}")
        for rec in ora_recs:
            gain = f" (+{rec['est_score_gain']} ora pts)" if rec.get("est_score_gain") else ""
            md.append(f"- **ora.ai** — [{rec['layer']}] {rec['recommendation']}{gain}")

    return "\n".join(md)


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: report.py <url>", file=sys.stderr)
        return 2
    print(build_report(sys.argv[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
