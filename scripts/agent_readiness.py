#!/usr/bin/env python3
"""Score how usable a site is FOR AI AGENTS (browsing agents, answer engines,
and tool-using assistants) — distinct from being cited by them.

Mirrors the checkable parts of:
  - Lighthouse 13.3 "Agentic Browsing" category (Chrome, May 2026):
    accessible names on interactive elements, llms.txt, WebMCP
  - Cloudflare Agent Readiness Score: markdown content negotiation,
    /.well-known/api-catalog (RFC 9727), Web Bot Auth key directory
  - ora.ai Identity/Access layers: no-JS content, MCP discovery, OpenAPI

Four weighted categories → 0-100 score plus a prioritized recommendation
list ("what the owner should do to make the site better for AI agents").

  content_parseability  35%  raw-HTML content, semantic landmarks, headings
  interaction_readiness 25%  labeled forms, accessible names, no div-soup
  agent_interfaces      25%  llms.txt, MCP/OpenAPI/NLWeb endpoints, markdown
  access                15%  no bot-wall between agents and content

Static analysis only — no headless browser. JS-only sites score low on
parseability by design: that is exactly what a non-rendering agent sees.
"""
from __future__ import annotations

import json
import re
import sys
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
BOT_UA = "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; GPTBot/1.2; +https://openai.com/gptbot"
TIMEOUT = 15
MAX_PROBE_BYTES = 65536

CHALLENGE_MARKERS = ("just a moment", "cf-chl", "captcha", "attention required",
                     "access denied", "verify you are human", "enable javascript and cookies")

# (path, name, expect: "text" | "json" | "any", note)
WELL_KNOWN_PROBES = [
    ("/llms.txt", "llms.txt", "text",
     "Curated markdown site map for LLMs. Not used by Google Search, but checked by "
     "Lighthouse Agentic Browsing and fetched by coding/IDE agents."),
    ("/llms-full.txt", "llms-full.txt", "text",
     "Full-content companion to llms.txt for one-shot ingestion."),
    ("/.well-known/mcp.json", "MCP discovery manifest", "json",
     "Lets agents discover the site's MCP server and tools."),
    ("/.well-known/api-catalog", "API catalog (RFC 9727)", "any",
     "Machine-readable index of the site's APIs."),
    ("/.well-known/http-message-signatures-directory", "Web Bot Auth keys", "any",
     "Key directory for signed-agent verification (RFC 9421 / Web Bot Auth)."),
    ("/openapi.json", "OpenAPI spec", "json",
     "Machine-readable API description agents can call directly."),
    ("/api/openapi.json", "OpenAPI spec (under /api)", "json", ""),
]


def fetch(url: str, ua: str, accept: str = "*/*") -> requests.Response | None:
    try:
        return requests.get(url, headers={"User-Agent": ua, "Accept": accept},
                            timeout=TIMEOUT, allow_redirects=True, stream=False)
    except Exception:
        return None


def probe(origin: str, path: str, expect: str) -> bool:
    r = fetch(origin + path, BROWSER_UA)
    if r is None or r.status_code != 200:
        return False
    ctype = r.headers.get("content-type", "").lower()
    body = r.text[:MAX_PROBE_BYTES]
    # SPAs answer 200 + index.html for any path — an HTML body is a miss.
    if "html" in ctype or body.lstrip()[:15].lower().startswith("<!doctype html"):
        return False
    if expect == "json":
        try:
            json.loads(body)
        except Exception:
            return False
    return True


def accessible_name(tag) -> bool:
    if tag.get("aria-label", "").strip() or tag.get("aria-labelledby", "").strip():
        return True
    if tag.get("title", "").strip():
        return True
    if tag.name == "img":
        return bool(tag.get("alt", "").strip())
    text = tag.get_text(strip=True)
    if text:
        return True
    img = tag.find("img")
    if img is not None and img.get("alt", "").strip():
        return True
    return False


def analyze(url: str) -> dict:
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
        parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    recommendations: list[dict] = []

    def rec(prio: int, category: str, text: str) -> None:
        recommendations.append({"priority": prio, "category": category, "text": text})

    r = fetch(url, BROWSER_UA)
    if r is None:
        return {"url": url, "error": "Could not fetch page."}
    html = r.text
    soup = BeautifulSoup(html, "html.parser")

    # ---- 1. Content parseability (35%) --------------------------------------
    for t in soup.find_all(["script", "style", "noscript"]):
        t.extract()
    body = soup.body
    visible_text = body.get_text(" ", strip=True) if body else ""
    word_count = len(visible_text.split())
    text_ratio = round(len(visible_text) / max(1, len(html)) * 100, 1)

    landmarks = {name: bool(soup.find(name)) for name in ("main", "nav", "header", "footer")}
    has_article = bool(soup.find(["article", "section"]))
    landmark_count = sum(landmarks.values()) + (1 if has_article else 0)

    h1s = soup.find_all("h1")
    levels = [int(h.name[1]) for h in soup.find_all(re.compile(r"^h[1-6]$"))]
    skipped = any(b - a > 1 for a, b in zip(levels, levels[1:]) if b > a)

    parse_score = 0.0
    if word_count >= 300:
        parse_score += 40
    elif word_count >= 100:
        parse_score += 25
    elif word_count >= 30:
        parse_score += 10
    if word_count < 100:
        rec(1, "content", f"Only {word_count} words of text reach the raw HTML — agents and AI "
            "crawlers that don't execute JavaScript see an almost empty page. Server-side render "
            "or pre-render the main content.")
    if text_ratio >= 5:
        parse_score += 20
    elif text_ratio >= 2:
        parse_score += 10
        rec(3, "content", f"Text-to-markup ratio is {text_ratio}% — heavy markup dilutes "
            "RAG/vector extraction. Aim for 5%+.")
    else:
        rec(2, "content", f"Text-to-markup ratio is only {text_ratio}% — most of the payload is "
            "markup/scripts, which hurts semantic indexing.")
    parse_score += landmark_count * 5  # up to 25
    if landmark_count < 3:
        missing = [n for n, present in landmarks.items() if not present]
        rec(2, "content", f"Add semantic landmarks ({', '.join('<' + m + '>' for m in missing)}"
            f"{', <article>/<section>' if not has_article else ''}) — agents use them to locate "
            "the main content and navigation.")
    if len(h1s) == 1:
        parse_score += 10
    else:
        rec(2, "content", f"Use exactly one <h1> (found {len(h1s)}). Agents anchor summaries on it.")
    if levels and not skipped:
        parse_score += 5
    elif skipped:
        rec(3, "content", "Heading levels skip (e.g. h1→h3) — keep the hierarchy sequential so "
            "chunkers can build a clean outline.")
    parse_score = min(100.0, parse_score)

    # ---- 2. Interaction readiness (25%) --------------------------------------
    inputs = [i for i in soup.find_all(["input", "select", "textarea"])
              if i.get("type", "").lower() not in ("hidden", "submit", "button")]
    label_for = {l.get("for") for l in soup.find_all("label") if l.get("for")}
    unlabeled = []
    for i in inputs:
        if i.get("id") in label_for:
            continue
        if i.get("aria-label", "").strip() or i.get("aria-labelledby", "").strip() or i.get("title", "").strip():
            continue
        if i.find_parent("label") is not None:
            continue
        unlabeled.append(i.get("name") or i.get("id") or i.get("type") or i.name)

    buttons = soup.find_all("button") + soup.find_all("a", href=True)
    unnamed = sum(1 for b in buttons if not accessible_name(b))

    clicky_divs = len([d for d in soup.find_all(["div", "span"], onclick=True) if not d.get("role")])

    webmcp = ("navigator.modelcontext" in html.lower()) or bool(
        soup.find(attrs={"toolname": True}) or soup.find(attrs={"data-tool-name": True}))

    inter_score = 0.0
    if inputs:
        labeled_frac = 1 - len(unlabeled) / len(inputs)
        inter_score += labeled_frac * 40
        if unlabeled:
            rec(1, "interaction", f"{len(unlabeled)}/{len(inputs)} form fields have no programmatic "
                f"label ({', '.join(str(u) for u in unlabeled[:4])}…). Add <label for> or aria-label — "
                "Lighthouse's Agentic Browsing audit fails agents on unlabeled fields.")
    else:
        inter_score += 40  # nothing to label
    if buttons:
        named_frac = 1 - unnamed / len(buttons)
        inter_score += named_frac * 40
        if unnamed:
            rec(2, "interaction", f"{unnamed}/{len(buttons)} buttons/links have no accessible name "
                "(no text, aria-label, or img alt). Agents can't tell what they do.")
    else:
        inter_score += 40
    if clicky_divs == 0:
        inter_score += 10
    else:
        rec(2, "interaction", f"{clicky_divs} <div>/<span> elements carry onclick without a role — "
            "invisible to the accessibility tree agents navigate. Use <button>/<a> or add roles.")
    if webmcp:
        inter_score += 10
        webmcp_note = "WebMCP hints detected (navigator.modelContext / tool annotations)."
    else:
        webmcp_note = ""
        rec(3, "interaction", "Consider WebMCP (W3C draft, Chrome origin trial): expose key forms/"
            "actions as declarative tools via navigator.modelContext so agents can operate them "
            "reliably.")
    inter_score = min(100.0, inter_score)

    # ---- 3. Agent interfaces (25%) -------------------------------------------
    found_interfaces: list[dict] = []
    missing_interfaces: list[str] = []
    seen_openapi = False
    for path, name, expect, note in WELL_KNOWN_PROBES:
        ok = probe(origin, path, expect)
        if ok:
            if name.startswith("OpenAPI"):
                if seen_openapi:
                    continue
                seen_openapi = True
            found_interfaces.append({"path": path, "name": name, "note": note})
        elif not name.startswith("OpenAPI") or path == "/api/openapi.json":
            missing_interfaces.append(name)

    # NLWeb /ask and MCP /mcp are POST endpoints; a GET answered with 405 + JSON
    # (or 200 + JSON) proves a real endpoint rather than a generic error page.
    nlweb = False
    for path, name, note in (
        ("/ask", "NLWeb /ask endpoint", "Natural-language query endpoint (NLWeb)."),
        ("/mcp", "MCP endpoint (/mcp)", "Live MCP server — agents can call the site's tools."),
    ):
        resp = fetch(origin + path, BROWSER_UA)
        if resp is not None and resp.status_code in (200, 405) \
                and "json" in resp.headers.get("content-type", "").lower():
            nlweb = True
            found_interfaces.append({"path": path, "name": name, "note": note})

    md_nego = False
    resp = fetch(origin + "/", BROWSER_UA, accept="text/markdown")
    if resp is not None and "markdown" in resp.headers.get("content-type", "").lower():
        md_nego = True
        found_interfaces.append({"path": "/", "name": "Markdown content negotiation", "note":
                                 "Serves text/markdown on request — the cheapest format for agents."})

    iface_score = min(100.0, len(found_interfaces) * 25.0)
    has_llms = any(f["path"] == "/llms.txt" for f in found_interfaces)
    if not has_llms:
        rec(2, "interfaces", "Publish /llms.txt — a curated markdown map of your key pages. "
            "Google Search ignores it, but Lighthouse's agentic audit checks it and coding/IDE "
            "agents fetch it.")
    if not any("MCP" in f["name"] or "NLWeb" in f["name"] for f in found_interfaces):
        rec(2, "interfaces", "Expose an agent interface: an MCP server advertised at "
            "/.well-known/mcp.json, or NLWeb (/ask) if you already publish Schema.org data. "
            "This is what lets assistants act on your site rather than just read it.")
    if not md_nego:
        rec(3, "interfaces", "Support markdown content negotiation (Accept: text/markdown) or "
            "publish .md twins of key pages — agents parse markdown far more cheaply than HTML.")
    if not seen_openapi and not nlweb:
        rec(3, "interfaces", "If you have a public API, publish its OpenAPI spec at /openapi.json "
            "and index it in /.well-known/api-catalog (RFC 9727) so agents can discover it.")

    # ---- 4. Access (15%) ------------------------------------------------------
    bot_resp = fetch(url, BOT_UA)
    browser_ok = r.status_code == 200
    bot_blocked = False
    bot_status = bot_resp.status_code if bot_resp is not None else None
    if bot_resp is None:
        bot_blocked = True
    else:
        low = bot_resp.text[:4096].lower()
        if bot_resp.status_code in (401, 403, 429, 503) and browser_ok:
            bot_blocked = True
        elif any(m in low for m in CHALLENGE_MARKERS) and bot_resp.status_code != 200:
            bot_blocked = True
    access_score = 100.0
    if bot_blocked:
        access_score = 0.0
        rec(1, "access", f"An AI-crawler user-agent (GPTBot) gets HTTP {bot_status or 'error'} while "
            "a browser gets 200 — a bot wall (WAF/CDN default, e.g. Cloudflare's post-2025 AI "
            "blocking) is cutting agents off regardless of robots.txt. Allowlist the AI bots you "
            "want, or adopt Web Bot Auth to admit verified agents.")

    # Snippet controls limit how much of the page AI answers may quote (informational)
    robots_meta = soup.find("meta", attrs={"name": "robots"})
    robots_content = (robots_meta.get("content", "") if robots_meta else "").lower()
    snippet_controls = {
        "nosnippet": "nosnippet" in robots_content,
        "max_snippet": next((p.strip() for p in robots_content.split(",") if "max-snippet" in p), ""),
        "data_nosnippet_blocks": len(soup.find_all(attrs={"data-nosnippet": True})),
    }
    if snippet_controls["nosnippet"]:
        rec(2, "access", "meta robots 'nosnippet' is set — Google AI Overviews/AI Mode cannot quote "
            "this page at all. Confirm that is intentional.")

    score = round(0.35 * parse_score + 0.25 * inter_score + 0.25 * iface_score + 0.15 * access_score, 1)
    recommendations.sort(key=lambda x: x["priority"])

    return {
        "url": r.url,
        "score": score,
        "categories": {
            "content_parseability": {"score": round(parse_score, 1), "weight": 0.35,
                                     "word_count_no_js": word_count, "text_to_markup_pct": text_ratio,
                                     "landmarks": landmarks, "h1_count": len(h1s),
                                     "heading_levels_skipped": skipped},
            "interaction_readiness": {"score": round(inter_score, 1), "weight": 0.25,
                                      "form_fields": len(inputs), "unlabeled_fields": len(unlabeled),
                                      "buttons_links": len(buttons), "without_accessible_name": unnamed,
                                      "clickable_divs_without_role": clicky_divs,
                                      "webmcp": webmcp, "webmcp_note": webmcp_note},
            "agent_interfaces": {"score": round(iface_score, 1), "weight": 0.25,
                                 "found": found_interfaces, "missing": missing_interfaces,
                                 "markdown_negotiation": md_nego, "nlweb": nlweb},
            "access": {"score": round(access_score, 1), "weight": 0.15,
                       "bot_wall_detected": bot_blocked, "bot_ua_status": bot_status,
                       "browser_ua_status": r.status_code, "snippet_controls": snippet_controls},
        },
        "recommendations": recommendations,
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: agent_readiness.py <url>", file=sys.stderr)
        return 2
    print(json.dumps(analyze(sys.argv[1]), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
