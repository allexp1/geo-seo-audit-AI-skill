#!/usr/bin/env python3
"""Generate a professional PDF audit report.

Usage:
  python3 generate_pdf.py <url> [output.pdf]

Collects all audit data and renders a styled PDF with score gauges,
color-coded tables, and prioritized action lists.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from urllib.parse import urlparse

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether,
)
from reportlab.graphics.shapes import Drawing, Rect, String, Circle, Wedge
from reportlab.graphics import renderPDF

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

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
CLR_PRIMARY = colors.HexColor("#1a1a2e")
CLR_ACCENT = colors.HexColor("#0f3460")
CLR_HIGHLIGHT = colors.HexColor("#e94560")
CLR_GREEN = colors.HexColor("#27ae60")
CLR_YELLOW = colors.HexColor("#f39c12")
CLR_RED = colors.HexColor("#e74c3c")
CLR_LIGHT_BG = colors.HexColor("#f8f9fa")
CLR_WHITE = colors.white
CLR_DARK_TEXT = colors.HexColor("#2c3e50")
CLR_MID_TEXT = colors.HexColor("#555555")
CLR_HEADER_BG = colors.HexColor("#1a1a2e")
CLR_ROW_ALT = colors.HexColor("#f0f3f7")

WIDTH, HEIGHT = A4


def score_color(score: float) -> colors.Color:
    if score >= 75:
        return CLR_GREEN
    elif score >= 50:
        return CLR_YELLOW
    return CLR_RED


def score_label(score: float) -> str:
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Fair"
    return "Poor"


# ---------------------------------------------------------------------------
# Score gauge drawing
# ---------------------------------------------------------------------------
def make_score_gauge(score: float, label: str, size: float = 80) -> Drawing:
    d = Drawing(size + 40, size + 30)
    cx, cy = (size + 40) / 2, size / 2 + 15
    radius = size / 2 - 4

    # Background arc
    d.add(Wedge(cx, cy, radius, 0, 360, fillColor=colors.HexColor("#e0e0e0"), strokeColor=None))
    # Score arc
    angle = score / 100 * 360
    if angle > 0:
        d.add(Wedge(cx, cy, radius, 90, 90 - angle, fillColor=score_color(score), strokeColor=None))
    # White center
    d.add(Circle(cx, cy, radius * 0.7, fillColor=CLR_WHITE, strokeColor=None))
    # Score text
    d.add(String(cx, cy - 5, f"{score:.0f}", fontSize=18, fontName="Helvetica-Bold",
                 fillColor=CLR_DARK_TEXT, textAnchor="middle"))
    # Label
    d.add(String(cx, 4, label, fontSize=8, fontName="Helvetica",
                 fillColor=CLR_MID_TEXT, textAnchor="middle"))
    return d


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
def get_styles():
    ss = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle("Title", parent=ss["Title"], fontSize=22,
                                textColor=CLR_PRIMARY, spaceAfter=2 * mm),
        "subtitle": ParagraphStyle("Subtitle", parent=ss["Normal"], fontSize=11,
                                   textColor=CLR_MID_TEXT, spaceAfter=6 * mm),
        "h1": ParagraphStyle("H1", parent=ss["Heading1"], fontSize=16,
                             textColor=CLR_PRIMARY, spaceBefore=8 * mm, spaceAfter=3 * mm),
        "h2": ParagraphStyle("H2", parent=ss["Heading2"], fontSize=13,
                             textColor=CLR_ACCENT, spaceBefore=6 * mm, spaceAfter=2 * mm),
        "body": ParagraphStyle("Body", parent=ss["Normal"], fontSize=9,
                               textColor=CLR_DARK_TEXT, leading=13),
        "body_small": ParagraphStyle("BodySmall", parent=ss["Normal"], fontSize=8,
                                     textColor=CLR_MID_TEXT, leading=11),
        "bullet": ParagraphStyle("Bullet", parent=ss["Normal"], fontSize=9,
                                 textColor=CLR_DARK_TEXT, leftIndent=10, leading=13),
        "p1": ParagraphStyle("P1", parent=ss["Normal"], fontSize=9,
                             textColor=CLR_RED, leftIndent=10, leading=13),
        "p2": ParagraphStyle("P2", parent=ss["Normal"], fontSize=9,
                             textColor=CLR_YELLOW, leftIndent=10, leading=13),
        "p3": ParagraphStyle("P3", parent=ss["Normal"], fontSize=9,
                             textColor=CLR_GREEN, leftIndent=10, leading=13),
        "footer": ParagraphStyle("Footer", parent=ss["Normal"], fontSize=7,
                                 textColor=CLR_MID_TEXT, alignment=1),
    }
    return styles


# ---------------------------------------------------------------------------
# Table helpers
# ---------------------------------------------------------------------------
BASE_TABLE_STYLE = [
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 8),
    ("TEXTCOLOR", (0, 0), (-1, 0), CLR_WHITE),
    ("BACKGROUND", (0, 0), (-1, 0), CLR_HEADER_BG),
    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
]


_CELL_STYLE = ParagraphStyle("Cell", fontName="Helvetica", fontSize=8,
                              leading=10, textColor=CLR_DARK_TEXT)
_CELL_HEADER = ParagraphStyle("CellH", fontName="Helvetica-Bold", fontSize=8,
                               leading=10, textColor=CLR_WHITE)
_CELL_RIGHT = ParagraphStyle("CellR", parent=_CELL_STYLE, alignment=2)
_CELL_HEADER_RIGHT = ParagraphStyle("CellHR", parent=_CELL_HEADER, alignment=2)


def _wrap_cell(val, is_header=False, right=False):
    """Wrap a cell value in a Paragraph so long text auto-wraps."""
    if isinstance(val, Paragraph):
        return val
    text = str(val).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    if is_header:
        return Paragraph(f"<b>{text}</b>", _CELL_HEADER_RIGHT if right else _CELL_HEADER)
    return Paragraph(text, _CELL_RIGHT if right else _CELL_STYLE)


def styled_table(data, col_widths=None, right_align_cols=None):
    right_cols = set(right_align_cols or [])
    wrapped = []
    for row_idx, row in enumerate(data):
        is_header = (row_idx == 0)
        wrapped.append([
            _wrap_cell(cell, is_header=is_header, right=(col_idx in right_cols))
            for col_idx, cell in enumerate(row)
        ])
    t = Table(wrapped, colWidths=col_widths, repeatRows=1)
    style = list(BASE_TABLE_STYLE)
    # Override font settings — Paragraphs handle their own fonts
    style = [s for s in style if s[0] not in ("FONTNAME", "FONTSIZE", "TEXTCOLOR")]
    style.append(("TEXTCOLOR", (0, 0), (-1, 0), CLR_WHITE))
    style.append(("BACKGROUND", (0, 0), (-1, 0), CLR_HEADER_BG))
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), CLR_ROW_ALT))
    t.setStyle(TableStyle(style))
    return t


def yes_no(v) -> str:
    return "Yes" if v else "No"


def trunc(s: str, n: int = 60) -> str:
    return s[:n] + "..." if len(s) > n else s


# ---------------------------------------------------------------------------
# Build PDF
# ---------------------------------------------------------------------------
def build_pdf(url: str, output: str, custom_keywords: list[str] | None = None):
    print(f"Collecting data for {url}...")

    page = fetch(url)
    crawlers = check_crawlers(url)
    cite = analyze_citability(url)
    schema = analyze_schema(url)
    llms = check_llmstxt(url)
    onpage = analyze_onpage(url)
    technical = analyze_technical(url)
    keywords = extract_keywords(url)
    read = analyze_readability(url)
    perf = analyze_performance(url)

    parsed = urlparse(page["final_url"])
    domain = parsed.netloc.lstrip("www.")

    # Keyword rankings — use custom keywords if provided, otherwise auto-extract
    if custom_keywords:
        kw_list = custom_keywords
    else:
        kw_list = [k["keyword"] for k in keywords.get("keywords", []) if " " in k["keyword"]][:3]
        kw_list += [k["keyword"] for k in keywords.get("keywords", []) if " " not in k["keyword"]][:2]
        kw_list = kw_list[:5]
    rankings = check_rankings(domain, kw_list) if kw_list else None

    print("Generating PDF...")

    # Scores
    s_crawl = 100.0 if not crawlers.get("robots_present") else (1 - crawlers.get("summary", {}).get("blocked", 0) / max(1, crawlers.get("summary", {}).get("total", 1))) * 100
    s_cite = float(cite.get("avg_score", 0)) if cite.get("passage_count", 0) > 0 else 0.0
    found_types = schema.get("types_found", [])
    hv = len(set(found_types) & {"Organization", "WebSite", "Article", "BlogPosting", "Product", "LocalBusiness", "FAQPage", "BreadcrumbList"})
    s_schema = min(100.0, 20 + hv * 15) if found_types else 0.0
    s_llms = 100.0 if llms.get("present") and llms.get("analysis", {}).get("valid_shape") else (60.0 if llms.get("present") else 0.0)
    geo = 0.35 * s_crawl + 0.35 * s_cite + 0.20 * s_schema + 0.10 * s_llms

    s_onpage = float(onpage.get("score", 0))
    # Technical score
    tech_score = 0
    if technical.get("https", {}).get("http_to_https_redirect"):
        tech_score += 20
    sec_count = technical.get("response", {}).get("security_headers_present", 0)
    tech_score += min(25, sec_count * 5)
    if technical.get("response", {}).get("content_encoding") in ("gzip", "br", "deflate", "zstd"):
        tech_score += 10
    elapsed = technical.get("response", {}).get("elapsed_ms", 0)
    if elapsed and elapsed < 800:
        tech_score += 15
    elif elapsed and elapsed < 2000:
        tech_score += 8
    cache = technical.get("response", {}).get("cache_headers", {})
    if cache.get("Cache-Control") or cache.get("ETag"):
        tech_score += 10
    sm = technical.get("sitemap", {})
    if sm.get("present"):
        tech_score += 15
        if sm.get("referenced_in_robots"):
            tech_score += 5
    s_tech = float(min(100, tech_score))
    seo = 0.5 * s_onpage + 0.5 * s_tech
    composite = (geo + seo) / 2

    styles = get_styles()
    story = []

    # ===== COVER / HEADER =====
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph(f"GEO + SEO Audit Report", styles["title"]))
    story.append(Paragraph(f"{parsed.netloc}", ParagraphStyle("Domain", parent=styles["title"],
                           fontSize=18, textColor=CLR_HIGHLIGHT)))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(f"URL: {page['final_url']}  |  Status: {page['status']}  |  "
                           f"Size: {page['html_bytes']:,} bytes  |  "
                           f"Date: {datetime.now().strftime('%B %d, %Y')}", styles["body_small"]))
    story.append(Spacer(1, 3 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=CLR_ACCENT))
    story.append(Spacer(1, 6 * mm))

    # ===== SCORE GAUGES =====
    gauge_table = Table([
        [make_score_gauge(composite, "Composite"),
         make_score_gauge(geo, "GEO"),
         make_score_gauge(seo, "SEO"),
         make_score_gauge(perf.get("lighthouse_score", 0) if perf.get("lighthouse_score") is not None else 0, "Lighthouse")]
    ], colWidths=[120, 120, 120, 120])
    gauge_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(gauge_table)
    story.append(Spacer(1, 6 * mm))

    # Score summary table
    score_data = [
        ["", "Score", "Rating", "Components"],
        ["Composite", f"{composite:.0f}/100", score_label(composite), ""],
        ["GEO (AI Search)", f"{geo:.0f}/100", score_label(geo), "Crawlers, Citability, Schema, llms.txt"],
        ["SEO (Traditional)", f"{seo:.0f}/100", score_label(seo), "On-Page, Technical"],
    ]
    if perf.get("lighthouse_score") is not None:
        score_data.append(["Performance", f"{perf['lighthouse_score']}/100",
                          score_label(perf["lighthouse_score"]), "Lighthouse Mobile"])
    story.append(styled_table(score_data, col_widths=[100, 60, 60, 260], right_align_cols=[1]))

    # ===== GEO BREAKDOWN =====
    story.append(Paragraph("GEO Breakdown", styles["h1"]))
    geo_data = [
        ["Category", "Weight", "Score", "Notes"],
        ["AI Crawler Access", "35%", f"{s_crawl:.0f}", f"{crawlers.get('summary', {}).get('blocked', 0)}/{crawlers.get('summary', {}).get('total', 22)} bots blocked"],
        ["Citability", "35%", f"{s_cite:.0f}", f"Avg across {cite.get('passage_count', 0)} passages"],
        ["Schema Coverage", "20%", f"{s_schema:.0f}", f"{len(found_types)} type(s), {hv} high-value"],
        ["llms.txt", "10%", f"{s_llms:.0f}", "Present" if llms.get("present") else "Not present"],
    ]
    story.append(styled_table(geo_data, col_widths=[110, 50, 50, 270], right_align_cols=[1, 2]))

    # ===== SEO BREAKDOWN =====
    story.append(Paragraph("SEO Breakdown", styles["h1"]))
    seo_data = [
        ["Category", "Weight", "Score", "Notes"],
        ["On-Page SEO", "50%", f"{s_onpage:.0f}", "; ".join(onpage.get("notes", [])[:2]) or "All basics present"],
        ["Technical SEO", "50%", f"{s_tech:.0f}", f"{sec_count}/6 security headers, {elapsed}ms response"],
    ]
    story.append(styled_table(seo_data, col_widths=[110, 50, 50, 270], right_align_cols=[1, 2]))

    # ===== ON-PAGE SEO DETAIL =====
    story.append(Paragraph("On-Page SEO Details", styles["h1"]))
    op = onpage
    op_data = [
        ["Element", "Value", "Status"],
        ["Title", op["title"]["value"] or "(missing)", f"{op['title']['length']} chars"],
        ["Meta Description", op["meta_description"]["value"] or "(missing)", f"{op['meta_description']['length']} chars"],
        ["H1", str(op["headings"]["h1"][0])[:50] if op["headings"]["h1"] else "(missing)", f"{len(op['headings']['h1'])} H1(s)"],
        ["Headings", f"H2: {op['headings']['h2_count']}, H3: {op['headings']['h3_count']}", ""],
        ["Canonical", op["canonical"] or "(missing)", ""],
        ["Lang / Charset", f"{op['lang'] or '(missing)'} / {op['charset'] or '(missing)'}", ""],
        ["Viewport", op["viewport"][:50] if op["viewport"] else "(missing)", ""],
        ["Open Graph", f"{sum(1 for v in op['open_graph'].values() if v)}/6 fields", ""],
        ["Twitter Card", f"{sum(1 for v in op['twitter_card'].values() if v)}/4 fields", ""],
        ["Images", f"{op['images']['total']} total, {op['images']['with_alt']} with alt", ""],
        ["Links", f"{op['links']['internal']} int, {op['links']['external']} ext, {op['links']['nofollow']} nofollow", ""],
        ["Word Count", str(op["word_count"]), ""],
    ]
    story.append(styled_table(op_data, col_widths=[100, 250, 130], right_align_cols=[2]))

    # ===== TECHNICAL SEO DETAIL =====
    story.append(Paragraph("Technical SEO Details", styles["h1"]))
    resp = technical.get("response", {})
    sec = resp.get("security_headers", {})
    tech_data = [
        ["Check", "Result"],
        ["HTTPS Redirect", yes_no(technical.get("https", {}).get("http_to_https_redirect"))],
        ["Response Time", f"{resp.get('elapsed_ms', '?')} ms"],
        ["Compression", resp.get("content_encoding") or "(none)"],
        ["Server", resp.get("server") or "(hidden)"],
    ]
    for h, v in sec.items():
        tech_data.append([h, "Present" if v else "MISSING"])
    sm = technical.get("sitemap", {})
    tech_data.append(["Sitemap", f"{sm.get('url', 'Not found')} ({sm.get('type', '')})" if sm.get("present") else "Not found"])
    tech_data.append(["Sitemap in robots.txt", yes_no(sm.get("referenced_in_robots")) if sm.get("present") else "N/A"])
    story.append(styled_table(tech_data, col_widths=[160, 320]))

    # ===== PAGE BREAK =====
    story.append(PageBreak())

    # ===== KEYWORDS =====
    story.append(Paragraph("Keywords", styles["h1"]))
    story.append(Paragraph("Extracted from Page", styles["h2"]))
    kw_data = [["Keyword", "Score", "Freq", "Found In"]]
    for k in keywords.get("keywords", [])[:15]:
        loc = ", ".join(k["found_in"]) if k["found_in"] else "body"
        kw_data.append([k["keyword"], str(k["score"]), str(k["frequency"]), loc])
    story.append(styled_table(kw_data, col_widths=[150, 60, 50, 220], right_align_cols=[1, 2]))

    if rankings and rankings.get("results"):
        story.append(Paragraph(f"Search Rankings ({rankings.get('method', 'search engine')})", styles["h2"]))
        rank_data = [["Keyword", "Position", "Top 3 Competitors"]]
        for r in rankings["results"]:
            pos = r.get("top_position")
            pos_str = f"#{pos}" if pos else "Not in top 30"
            top3 = ", ".join(urlparse(t["url"]).netloc.lstrip("www.") for t in r.get("top_3", []))
            rank_data.append([r["keyword"], pos_str, top3])
        story.append(styled_table(rank_data, col_widths=[140, 80, 260], right_align_cols=[1]))

        summ = rankings.get("summary", {})
        if summ.get("not_in_results"):
            story.append(Spacer(1, 2 * mm))
            story.append(Paragraph(
                f"<b>Not ranking for:</b> {', '.join(summ['not_in_results'])}",
                styles["body"]))

    # ===== READABILITY =====
    story.append(Paragraph("Readability", styles["h1"]))
    if read.get("error"):
        story.append(Paragraph(read["error"], styles["body"]))
    else:
        read_data = [
            ["Metric", "Value", "Assessment"],
            ["Flesch Reading Ease", str(read["flesch_reading_ease"]), read["level"]],
            ["Flesch-Kincaid Grade", str(read["flesch_kincaid_grade"]), ""],
            ["Gunning Fog Index", str(read["gunning_fog"]), ""],
            ["Avg Sentence Length", f"{read['avg_words_per_sentence']} words", ""],
            ["Complex Words", f"{read['complex_word_pct']}%", ""],
            ["AI Citation Friendly", yes_no(read["ai_citation_friendly"]),
             "Target: Flesch 50-70"],
        ]
        story.append(styled_table(read_data, col_widths=[140, 100, 240], right_align_cols=[1]))

    # ===== PERFORMANCE =====
    if perf.get("lighthouse_score") is not None:
        story.append(Paragraph("Performance (Lighthouse)", styles["h1"]))
        story.append(Paragraph(
            f"Score: {perf['lighthouse_score']}/100 ({perf.get('strategy', 'mobile')})",
            styles["body"]))

        fd = perf.get("field_data")
        if isinstance(fd, dict) and fd:
            story.append(Paragraph("Core Web Vitals (Field Data)", styles["h2"]))
            cwv_data = [["Metric", "Value", "Rating"]]
            for key, info in fd.items():
                val = info.get("value", "")
                unit = " ms" if key.endswith("_ms") else ""
                cat = {"good": "GOOD", "needs_improvement": "NEEDS WORK", "poor": "POOR"}.get(
                    info.get("category", ""), info.get("category", ""))
                cwv_data.append([info.get("label", key), f"{val}{unit}", cat])
            story.append(styled_table(cwv_data, col_widths=[180, 100, 200], right_align_cols=[1]))

        opps = perf.get("opportunities", [])
        if opps:
            story.append(Paragraph("Top Opportunities", styles["h2"]))
            for o in opps:
                story.append(Paragraph(
                    f"• <b>{o['audit']}</b> — save ~{o['savings_ms']} ms",
                    styles["bullet"]))

    # ===== AI CRAWLERS =====
    story.append(Paragraph("AI Crawler Access", styles["h1"]))
    blocked_bots = [b for b in crawlers.get("bots", []) if b.get("blocked_root")]
    allowed_explicit = [b for b in crawlers.get("bots", []) if b.get("source") == "explicit" and not b.get("blocked_root")]
    total = crawlers.get("summary", {}).get("total", 22)
    story.append(Paragraph(
        f"<b>{total - len(blocked_bots)}/{total}</b> AI bots allowed  |  "
        f"<b>{len(blocked_bots)}</b> blocked  |  "
        f"<b>{len(allowed_explicit)}</b> explicitly allowed",
        styles["body"]))
    story.append(Spacer(1, 2 * mm))

    bot_data = [["Bot", "Vendor", "Status"]]
    for b in crawlers.get("bots", []):
        if b.get("blocked_root"):
            status = "BLOCKED"
        elif b.get("source") == "explicit":
            status = "Explicitly allowed"
        else:
            status = "Allowed (wildcard)"
        bot_data.append([b["token"], b["vendor"], status])
    story.append(styled_table(bot_data, col_widths=[130, 100, 250]))

    # ===== CITABILITY =====
    story.append(PageBreak())
    story.append(Paragraph("Citability Analysis", styles["h1"]))
    if cite.get("passage_count", 0) == 0:
        story.append(Paragraph(
            "No analyzable passages found. Page may be JS-rendered or content-thin.",
            styles["body"]))
    else:
        story.append(Paragraph(
            f"Passages: <b>{cite['passage_count']}</b>  |  "
            f"In optimal band (100-200 words): <b>{cite['passages_in_optimal_band']}</b>  |  "
            f"Average score: <b>{cite['avg_score']}</b>",
            styles["body"]))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph("Top Citable Passages", styles["h2"]))
        for i, p in enumerate(cite.get("top", [])[:5], 1):
            story.append(Paragraph(
                f"<b>#{i}</b> (score {p['score']}, {p['words']} words): "
                f"<i>{p['preview']}</i>",
                styles["body_small"]))
            story.append(Spacer(1, 1.5 * mm))

    # ===== SCHEMA =====
    story.append(Paragraph("Schema (JSON-LD)", styles["h1"]))
    if schema["block_count"] == 0:
        story.append(Paragraph("No JSON-LD blocks found.", styles["body"]))
    else:
        story.append(Paragraph(
            f"Blocks: <b>{schema['block_count']}</b>  |  "
            f"Types: {', '.join(schema['types_found'])}",
            styles["body"]))
        if schema["common_types_missing"]:
            story.append(Paragraph(
                f"Missing high-value types: <b>{', '.join(schema['common_types_missing'])}</b>",
                styles["body"]))

    # ===== LLMS.TXT =====
    story.append(Paragraph("llms.txt", styles["h1"]))
    if llms.get("present"):
        a = llms["analysis"]
        story.append(Paragraph(
            f"Present ({a['size']} bytes)  |  H1: {yes_no(a['starts_with_h1'])}  |  "
            f"Sections: {a['section_count']}  |  Links: {a['link_count']}",
            styles["body"]))
    else:
        story.append(Paragraph("Not present. Recommended to publish /llms.txt.", styles["body"]))

    # ===== COMPETITIVE ANALYSIS =====
    if rankings and rankings.get("results"):
        story.append(PageBreak())
        story.append(Paragraph("Competitive Analysis", styles["h1"]))
        story.append(HRFlowable(width="100%", thickness=1, color=CLR_ACCENT))
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph(
            f"Who currently outranks <b>{domain}</b> on Google — and how to take their position.",
            styles["body"]))
        story.append(Spacer(1, 4 * mm))

        for r in rankings["results"]:
            kw = r["keyword"]
            pos = r.get("top_position")
            top3 = r.get("top_3", [])
            if not top3:
                continue

            # Section header per keyword
            pos_label = f"#{pos}" if pos else "Not in top 30"
            story.append(Paragraph(
                f'Keyword: "<b>{kw}</b>"  —  Your position: <b>{pos_label}</b>',
                ParagraphStyle("KWHeader", parent=styles["body"], fontSize=10,
                               textColor=CLR_PRIMARY, spaceBefore=5 * mm, spaceAfter=2 * mm)))

            # Competitors table
            comp_data = [["Rank", "Competitor", "Page Title", "What They Do Right"]]
            for t in top3:
                comp_domain = urlparse(t["url"]).netloc.lstrip("www.")
                title = t.get("title", "")
                snippet = t.get("snippet", "")

                # Derive competitive edge from snippet + domain
                edge = ""
                if "wikipedia" in comp_domain:
                    edge = "Authoritative encyclopedia entry — hard to outrank directly, but your content can appear alongside"
                elif "reddit" in comp_domain:
                    edge = "User-generated trust. Create content that answers the same questions with more authority"
                elif snippet:
                    # Analyze snippet for patterns
                    snip_lower = snippet.lower()
                    edges = []
                    if any(w in snip_lower for w in ["guide", "what is", "how to", "learn"]):
                        edges.append("educational content")
                    if any(w in snip_lower for w in ["best", "top", "compare", "vs", "review"]):
                        edges.append("comparison/listicle format")
                    if any(w in snip_lower for w in ["free", "trial", "start", "sign up", "get"]):
                        edges.append("strong CTA + free offering")
                    if any(w in snip_lower for w in ["pricing", "$", "month", "plan"]):
                        edges.append("transparent pricing")
                    if any(w in snip_lower for w in ["api", "developer", "documentation", "sdk"]):
                        edges.append("developer-focused content")
                    if any(w in snip_lower for w in ["enterprise", "business", "scale"]):
                        edges.append("enterprise positioning")
                    edge = "; ".join(edges) if edges else "Established domain + targeted landing page"
                else:
                    edge = "Established domain authority"

                comp_data.append([
                    f"#{t['rank']}",
                    comp_domain,
                    title,
                    edge,
                ])

            story.append(styled_table(comp_data, col_widths=[35, 110, 150, 185], right_align_cols=[0]))
            story.append(Spacer(1, 2 * mm))

            # How to outrank — specific recommendation
            top1_domain = urlparse(top3[0]["url"]).netloc.lstrip("www.") if top3 else ""
            top1_snippet = top3[0].get("snippet", "").lower() if top3 else ""

            # Generate targeted strategy
            strategies = []
            if "wikipedia" in top1_domain:
                strategies.append(f"Create a definitive guide page at /{kw.replace(' ', '-')} that's more actionable than Wikipedia.")
                strategies.append("Add FAQ schema — Google often shows FAQ results alongside Wikipedia.")
            elif "reddit" in top1_domain:
                strategies.append(f"Write an authoritative answer page for \"{kw}\" — Google promotes Reddit when no expert content exists.")
                strategies.append("Include real customer testimonials and case studies to match Reddit's authenticity signal.")
            else:
                if any(w in top1_snippet for w in ["guide", "what is", "how to"]):
                    strategies.append(f"Create a comprehensive guide: \"What is {kw.title()}? Complete Guide for Businesses\".")
                elif any(w in top1_snippet for w in ["best", "top", "compare"]):
                    strategies.append(f"Publish a comparison page or get listed in existing \"{kw}\" roundup articles.")
                else:
                    strategies.append(f"Create a dedicated landing page at /{kw.replace(' ', '-')} with 800+ words.")

            strategies.append(f"Target snippet length: 134-167 words answering \"{kw}\" directly in the first paragraph.")
            strategies.append("Add JSON-LD FAQPage schema with 5+ Q&A pairs related to this keyword.")

            story.append(Paragraph("<b>How to outrank:</b>", styles["body"]))
            for s in strategies:
                story.append(Paragraph(f"→ {s}", styles["bullet"]))
            story.append(Spacer(1, 2 * mm))

        # Summary box
        story.append(Spacer(1, 4 * mm))
        story.append(HRFlowable(width="100%", thickness=0.5, color=CLR_MID_TEXT))
        story.append(Spacer(1, 3 * mm))

        summ = rankings.get("summary", {})
        not_ranking = summ.get("not_in_results", [])
        total_kw = rankings.get("keywords_checked", 0)
        ranking_kw = rankings.get("keywords_ranking", 0)

        summary_items = []
        summary_items.append(f"Keywords checked: <b>{total_kw}</b>")
        summary_items.append(f"Ranking in top 30: <b>{ranking_kw}/{total_kw}</b>")
        if summ.get("best_position"):
            summary_items.append(f"Best position: <b>#{summ['best_position']}</b>")
        if not_ranking:
            summary_items.append(f"Not ranking for: <b>{', '.join(not_ranking)}</b>")

        story.append(Paragraph("Competitive Summary", styles["h2"]))
        for item in summary_items:
            story.append(Paragraph(f"• {item}", styles["body"]))

        if not_ranking:
            story.append(Spacer(1, 3 * mm))
            story.append(Paragraph(
                "<b>Key insight:</b> Every keyword where you don't rank is a keyword where competitors "
                "capture 100% of search traffic. Each dedicated landing page you create is a new entry "
                "point from Google. Prioritize keywords by business value, not search volume.",
                ParagraphStyle("Insight", parent=styles["body"], fontSize=9,
                               textColor=CLR_ACCENT, backColor=CLR_LIGHT_BG,
                               borderPadding=8, leftIndent=5, rightIndent=5)))

    # ===== ACTION PLAN =====
    story.append(PageBreak())
    story.append(Paragraph("Prioritized Action Plan", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=CLR_ACCENT))
    story.append(Spacer(1, 3 * mm))

    # SEO Actions
    seo_actions: list[tuple[int, str]] = []
    if not op["title"]["value"]:
        seo_actions.append((1, "Add a <title> tag (30-60 chars)."))
    elif not (30 <= op["title"]["length"] <= 60):
        seo_actions.append((2, f"Adjust title to 30-60 chars (currently {op['title']['length']})."))
    if not op["meta_description"]["value"]:
        seo_actions.append((1, "Add a meta description (120-160 chars)."))
    elif not (120 <= op["meta_description"]["length"] <= 160):
        seo_actions.append((2, f"Adjust meta description to 120-160 chars (currently {op['meta_description']['length']})."))
    if len(op["headings"]["h1"]) != 1:
        seo_actions.append((1, f"Use exactly one H1 (currently {len(op['headings']['h1'])})."))
    if not op["canonical"]:
        seo_actions.append((2, "Add a canonical link."))
    if not op["viewport"]:
        seo_actions.append((1, "Add a mobile viewport meta tag."))
    if not technical.get("https", {}).get("http_to_https_redirect"):
        seo_actions.append((1, "Force HTTP to HTTPS redirect."))
    missing_sec = [h for h in ["Strict-Transport-Security", "X-Content-Type-Options", "Content-Security-Policy"] if not sec.get(h)]
    if missing_sec:
        seo_actions.append((2, f"Add security headers: {', '.join(missing_sec)}."))
    if resp.get("content_encoding") not in ("gzip", "br", "deflate", "zstd"):
        seo_actions.append((1, "Enable gzip or brotli compression."))
    if not sm.get("present"):
        seo_actions.append((2, "Publish a sitemap.xml and reference in robots.txt."))
    if rankings:
        not_ranking = rankings.get("summary", {}).get("not_in_results", [])
        if not_ranking:
            seo_actions.append((2, f"Not ranking for: {', '.join(not_ranking[:3])}. Create dedicated pages."))
    if not read.get("error") and read.get("flesch_reading_ease", 100) < 40:
        seo_actions.append((3, f"Content is hard to read (Flesch {read['flesch_reading_ease']}). Simplify."))

    # GEO Actions
    geo_actions: list[tuple[int, str]] = []
    if blocked_bots:
        names = ", ".join(b["token"] for b in blocked_bots[:5])
        geo_actions.append((1, f"AI bots blocked: {names}. Review robots.txt."))
    if cite.get("passage_count", 0) == 0:
        geo_actions.append((1, "No analyzable text passages — add substantive content."))
    elif cite.get("passages_in_optimal_band", 0) < 3:
        geo_actions.append((2, "Restructure content into 100-200 word answer blocks."))
    if schema["block_count"] == 0:
        geo_actions.append((2, "Add JSON-LD: Organization + WebSite at minimum."))
    if not llms.get("present"):
        geo_actions.append((3, "Publish /llms.txt."))
    elif llms.get("analysis", {}).get("link_count", 0) == 0:
        geo_actions.append((2, "llms.txt has no links — add markdown links to key pages."))
    if not read.get("error") and not read.get("ai_citation_friendly"):
        if read.get("flesch_reading_ease", 100) < 50:
            geo_actions.append((3, "Simplify content for AI citation (target Flesch 50-70)."))

    prio_labels = {1: "P1 — Critical", 2: "P2 — Important", 3: "P3 — Nice to have"}
    prio_styles = {1: styles["p1"], 2: styles["p2"], 3: styles["p3"]}

    story.append(Paragraph("SEO Actions", styles["h2"]))
    if seo_actions:
        seo_actions.sort(key=lambda x: x[0])
        for prio, text in seo_actions:
            story.append(Paragraph(f"<b>[{prio_labels[prio]}]</b> {text}", prio_styles[prio]))
            story.append(Spacer(1, 1 * mm))
    else:
        story.append(Paragraph("No SEO issues found.", styles["body"]))

    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("GEO Actions", styles["h2"]))
    if geo_actions:
        geo_actions.sort(key=lambda x: x[0])
        for prio, text in geo_actions:
            story.append(Paragraph(f"<b>[{prio_labels[prio]}]</b> {text}", prio_styles[prio]))
            story.append(Spacer(1, 1 * mm))
    else:
        story.append(Paragraph("No GEO issues found.", styles["body"]))

    # ===== STRATEGIC ROADMAP =====
    if rankings and rankings.get("results"):
        story.append(PageBreak())
        story.append(Paragraph("Strategic SEO + GEO Roadmap", styles["h1"]))
        story.append(HRFlowable(width="100%", thickness=1, color=CLR_HIGHLIGHT))
        story.append(Spacer(1, 4 * mm))

        ranked_kws = [r for r in rankings["results"] if r.get("top_position") is not None]
        unranked_kws = [r for r in rankings["results"] if r.get("top_position") is None and "error" not in r]
        total_kw = rankings.get("keywords_checked", 0)

        # Overview
        story.append(Paragraph(
            f"<b>{domain}</b> ranks for <b>{len(ranked_kws)}/{total_kw}</b> target keywords on Google. "
            f"{'This is a strong foundation to build on.' if len(ranked_kws) > total_kw / 2 else 'Significant opportunity gap — most target keywords have no ranking presence.'}",
            ParagraphStyle("RoadmapIntro", parent=styles["body"], fontSize=10,
                           textColor=CLR_PRIMARY, spaceAfter=4 * mm)))

        # Keyword opportunity matrix
        story.append(Paragraph("Keyword Opportunity Matrix", styles["h2"]))
        matrix_data = [["Keyword", "Position", "Difficulty", "Recommended Action"]]

        for r in rankings["results"]:
            kw = r["keyword"]
            pos = r.get("top_position")
            top3 = r.get("top_3", [])
            total_res = r.get("total_google_results", 0)

            if pos is not None:
                pos_str = f"#{pos}"
                if pos <= 3:
                    difficulty = "Defend"
                    action = "Maintain — optimize existing page, add fresh content quarterly"
                elif pos <= 10:
                    difficulty = "Easy win"
                    action = "Push to top 3 — add FAQ schema, internal links, backlinks"
                else:
                    difficulty = "Medium"
                    action = "Improve content depth, add structured data, earn backlinks"
            else:
                pos_str = "Not ranked"
                # Judge difficulty by who's ranking
                top_domains = [urlparse(t["url"]).netloc.lstrip("www.") for t in top3]
                has_wikipedia = any("wikipedia" in d for d in top_domains)
                has_giants = any(g in " ".join(top_domains) for g in ["twilio", "ringcentral", "google", "microsoft", "amazon"])

                if has_wikipedia and has_giants:
                    difficulty = "Very hard"
                    action = "Long-tail variation — target more specific phrase"
                elif has_giants:
                    difficulty = "Hard"
                    action = "Create 1500+ word guide with unique data/case studies"
                else:
                    difficulty = "Medium"
                    action = "Create dedicated landing page with 800+ words"

            matrix_data.append([kw, pos_str, difficulty, action])

        story.append(styled_table(matrix_data, col_widths=[120, 65, 65, 230], right_align_cols=[1]))
        story.append(Spacer(1, 6 * mm))

        # Content strategy by tier
        story.append(Paragraph("Content Strategy — 3 Tiers", styles["h2"]))

        # Tier 1: Quick wins (already ranking or easy keywords)
        quick_wins = [r for r in rankings["results"]
                      if r.get("top_position") is not None and r["top_position"] <= 20]
        if quick_wins:
            story.append(Paragraph("<b>Tier 1: Quick Wins (already ranking — push higher)</b>",
                                   ParagraphStyle("Tier", parent=styles["body"], fontSize=10,
                                                  textColor=CLR_GREEN, spaceBefore=3 * mm)))
            for r in quick_wins:
                url_ranking = r["appearances"][0]["url"] if r["appearances"] else ""
                story.append(Paragraph(
                    f"→ <b>\"{r['keyword']}\"</b> (#{r['top_position']}) — "
                    f"Page: {url_ranking}. "
                    f"Add FAQ schema, improve content depth, build 3-5 internal links to this page.",
                    styles["bullet"]))
            story.append(Spacer(1, 2 * mm))

        # Tier 2: New pages needed (unranked but medium difficulty)
        medium_kws = []
        hard_kws = []
        for r in unranked_kws:
            top_domains = [urlparse(t["url"]).netloc.lstrip("www.") for t in r.get("top_3", [])]
            has_giants = any(g in " ".join(top_domains) for g in ["twilio", "ringcentral", "google", "microsoft", "bandwidth"])
            if has_giants:
                hard_kws.append(r)
            else:
                medium_kws.append(r)

        if medium_kws:
            story.append(Paragraph("<b>Tier 2: Create Landing Pages (medium difficulty)</b>",
                                   ParagraphStyle("Tier", parent=styles["body"], fontSize=10,
                                                  textColor=CLR_YELLOW, spaceBefore=3 * mm)))
            for r in medium_kws:
                slug = r["keyword"].replace(" ", "-").lower()
                top1 = urlparse(r["top_3"][0]["url"]).netloc.lstrip("www.") if r.get("top_3") else "unknown"
                story.append(Paragraph(
                    f"→ <b>\"{r['keyword']}\"</b> — Create /{slug} page. "
                    f"Current #1: {top1}. Write 800+ word guide with comparison tables, "
                    f"pricing info, and case studies. Add FAQPage schema.",
                    styles["bullet"]))
            story.append(Spacer(1, 2 * mm))

        if hard_kws:
            story.append(Paragraph("<b>Tier 3: Long-term Content Investment (hard — major competitors)</b>",
                                   ParagraphStyle("Tier", parent=styles["body"], fontSize=10,
                                                  textColor=CLR_RED, spaceBefore=3 * mm)))
            for r in hard_kws:
                slug = r["keyword"].replace(" ", "-").lower()
                competitors = ", ".join(urlparse(t["url"]).netloc.lstrip("www.") for t in r.get("top_3", [])[:2])
                story.append(Paragraph(
                    f"→ <b>\"{r['keyword']}\"</b> — Competing with: {competitors}. "
                    f"Create a definitive 1500+ word resource with unique data, customer testimonials, "
                    f"and technical depth they can't match. Target long-tail variations first.",
                    styles["bullet"]))
            story.append(Spacer(1, 2 * mm))

        # GEO-specific strategy
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph("GEO Strategy — Getting Cited by AI", styles["h2"]))
        story.append(Paragraph(
            "AI search engines (ChatGPT, Perplexity, Claude, Google AI Overviews) don't rank pages — "
            "they <b>cite passages</b>. The goal isn't position #1, it's being the passage that gets quoted.",
            styles["body"]))
        story.append(Spacer(1, 3 * mm))

        geo_strategies = [
            ("Write answer-first content",
             "Every page should open with a 134-167 word paragraph that directly answers "
             "the keyword's implicit question. No preamble, no \"In today's world...\" — just the answer. "
             "This is the passage AI assistants quote."),
            ("Add FAQPage schema everywhere",
             "Each product/landing page should have 5-8 FAQ questions in JSON-LD. "
             "AI assistants often pull directly from FAQ schema because the Q&A format "
             "matches how users ask questions."),
            ("Publish /llms.txt" if not llms.get("present") else "Improve /llms.txt",
             "This file tells AI crawlers what your site is about and where to find key pages. "
             + ("Create it with links to all product pages, API docs, and key content." if not llms.get("present")
                else "Add more links and ensure every section has 3-5 URLs.")),
            ("Build entity authority",
             "AI assistants cite entities they recognize. Add Organization schema with sameAs "
             "links to LinkedIn, Crunchbase, Wikipedia (if applicable). Get mentioned on "
             "industry comparison pages, review sites, and partner pages."),
            ("Target AI-friendly readability",
             f"Current Flesch score: {read.get('flesch_reading_ease', 'N/A')}. "
             f"Target: 50-70 (8th-10th grade). "
             f"{'Content is too complex — simplify sentences and reduce jargon.' if read.get('flesch_reading_ease', 100) < 50 else 'Readability is in a good range.' if read.get('flesch_reading_ease', 0) >= 50 else ''}"),
        ]

        for title, desc in geo_strategies:
            story.append(Paragraph(f"<b>{title}</b>",
                                   ParagraphStyle("GeoTitle", parent=styles["body"], fontSize=9,
                                                  textColor=CLR_ACCENT, spaceBefore=3 * mm)))
            story.append(Paragraph(desc, styles["body_small"]))

        # 90-day action timeline
        story.append(PageBreak())
        story.append(Paragraph("90-Day Action Timeline", styles["h1"]))
        story.append(HRFlowable(width="100%", thickness=1, color=CLR_ACCENT))
        story.append(Spacer(1, 4 * mm))

        timeline_data = [["Week", "Action", "Expected Impact"]]

        # Week 1-2: Technical fixes
        tech_fixes = []
        if not op["canonical"]:
            tech_fixes.append("canonical link")
        missing_headers = [h for h, v in sec.items() if not v]
        if missing_headers:
            tech_fixes.append(f"{len(missing_headers)} security headers")
        if schema["block_count"] == 0:
            tech_fixes.append("JSON-LD Organization + WebSite schema")
        if not llms.get("present"):
            tech_fixes.append("/llms.txt")

        if tech_fixes:
            timeline_data.append(["1-2", f"Technical: Add {', '.join(tech_fixes[:3])}", "SEO +5-10 pts"])

        # Week 3-4: Quick win content
        if quick_wins:
            kw_names = ", ".join(f'"{r["keyword"]}"' for r in quick_wins[:2])
            timeline_data.append(["3-4", f"Optimize existing pages for {kw_names}", f"Push to top 3"])

        # Week 3-6: New landing pages
        new_pages = medium_kws[:3]
        if new_pages:
            kw_names = ", ".join(f'"{r["keyword"]}"' for r in new_pages[:2])
            timeline_data.append(["3-6", f"Create landing pages: {kw_names}", "New rankings in 4-8 weeks"])

        # Week 4-8: Content depth
        if hard_kws:
            timeline_data.append(["4-8", "Write in-depth guides for competitive keywords", "Build topical authority"])

        # Week 5-8: Schema + GEO
        timeline_data.append(["5-8", "Add FAQPage schema to all product pages", "GEO +15-20 pts"])

        # Week 6-10: Readability
        if read.get("flesch_reading_ease", 100) < 50:
            timeline_data.append(["6-10", f"Rewrite content for readability (Flesch {read.get('flesch_reading_ease', '?')} → 55+)", "Better AI citations + engagement"])

        # Week 8-12: Link building + monitoring
        timeline_data.append(["8-12", "Earn backlinks via industry directories, partner pages, guest posts", "Domain authority growth"])
        timeline_data.append(["12+", "Monitor rankings monthly, refresh content quarterly", "Sustained growth"])

        story.append(styled_table(timeline_data, col_widths=[50, 280, 150]))

    # ===== FOOTER =====
    story.append(Spacer(1, 15 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=CLR_MID_TEXT))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  geo-skill audit tool",
        styles["footer"]))

    # Build
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )
    doc.build(story)
    print(f"PDF saved to: {output}")


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: generate_pdf.py <url> [output.pdf] [--keywords kw1,kw2,kw3,...]", file=sys.stderr)
        return 2
    url = sys.argv[1]
    parsed = urlparse(url)
    domain = (parsed.netloc or parsed.path).lstrip("www.").replace(".", "-")

    # Parse args
    output = None
    custom_keywords = None
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--keywords" and i + 1 < len(sys.argv):
            custom_keywords = [k.strip() for k in sys.argv[i + 1].split(",") if k.strip()]
            i += 2
        elif not output and not sys.argv[i].startswith("--"):
            output = sys.argv[i]
            i += 1
        else:
            i += 1

    if not output:
        output = f"{domain}-audit-{datetime.now().strftime('%Y%m%d')}.pdf"

    build_pdf(url, output, custom_keywords=custom_keywords)
    return 0


if __name__ == "__main__":
    sys.exit(main())
