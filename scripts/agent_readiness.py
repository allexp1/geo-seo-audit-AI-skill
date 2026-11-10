#!/usr/bin/env python3
"""Score how usable a site is FOR AI AGENTS (browsing agents, answer engines,
and tool-using assistants) — distinct from being cited by them.

Mirrors the checkable parts of:
  - Lighthouse 13.3 "Agentic Browsing" category (Chrome, May 2026):
    accessible names on interactive elements, llms.txt, WebMCP
  - Cloudflare Agent Readiness Score: markdown content negotiation,
    /.well-known/api-catalog (RFC 9727), Web Bot Auth key directory
  - ora.ai Identity/Access layers: no-JS content, MCP discovery, OpenAPI
  - AgentReady v2.0 (agentready.org, Oct 2026): every externally checkable rule is
    reported under its stable id (AR-FIND-01 ...) with its MUST/SHOULD/MAY level in
    result["agentready"]. The 0-100 score below is unchanged by that checklist.

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
import time
import uuid
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36")
BOT_UA = "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; GPTBot/1.2; +https://openai.com/gptbot"
TIMEOUT = 15
MAX_PROBE_BYTES = 65536
MCP_DEADLINE = 10  # seconds, total, for the MCP initialize handshake

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
    ("/.well-known/ai-catalog.json", "AI Catalog (AgentReady AR-FIND-04)", "json",
     "One manifest listing every agent-facing resource: MCP server card, OpenAPI, llms.txt, skills."),
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


def mcp_handshake(url: str) -> bool:
    """Streamable-HTTP MCP servers may answer a plain GET with a docs page, so send the
    read-only `initialize` request. A JSON-RPC result, or a 401 with WWW-Authenticate
    (an OAuth-gated server), proves a real MCP endpoint."""
    body = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                       "clientInfo": {"name": "geo-audit", "version": "1"}}}
    try:
        resp = requests.post(url, json=body, timeout=TIMEOUT, stream=True, headers={
            "User-Agent": BROWSER_UA, "Accept": "application/json, text/event-stream"})
    except Exception:
        return False
    try:
        return _mcp_reply(resp, url)
    finally:
        resp.close()


def _mcp_reply(resp, url: str) -> bool:
    if resp.status_code == 401:
        # An MCP server gated by OAuth answers with a Bearer challenge naming its protected-resource
        # metadata (RFC 9728), or publishes that metadata. A site-wide Basic login proves nothing.
        challenge = resp.headers.get("www-authenticate", "").lower()
        if not challenge.startswith("bearer"):
            return False
        if "resource_metadata" in challenge:
            return True
        origin = "{0.scheme}://{0.netloc}".format(urlparse(url))
        prm = fetch(origin + "/.well-known/oauth-protected-resource", BROWSER_UA)
        return prm is not None and prm.status_code == 200 and "json" in prm.headers.get("content-type", "")
    if resp.status_code != 200:
        return False
    # Read incrementally (an SSE reply may stay open with keepalives); stop at the first
    # JSON-RPC result, after MAX_PROBE_BYTES, or after MCP_DEADLINE seconds in total.
    deadline = time.monotonic() + MCP_DEADLINE
    seen = ""
    try:
        for chunk in resp.iter_content(chunk_size=1024, decode_unicode=True):
            seen += chunk if isinstance(chunk, str) else chunk.decode("utf-8", "ignore")
            if '"jsonrpc"' in seen and ('"result"' in seen or '"serverInfo"' in seen):
                return True
            if len(seen) > MAX_PROBE_BYTES or time.monotonic() > deadline:
                return False
    except Exception:
        pass
    return '"jsonrpc"' in seen and ('"result"' in seen or '"serverInfo"' in seen)


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
    raw_soup = BeautifulSoup(html, "html.parser")

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

    webmcp = bool(re.search(r"(?:document|navigator)\.modelcontext", html.lower())) or bool(
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
        webmcp_note = "WebMCP hints detected (document.modelContext / tool annotations)."
    else:
        webmcp_note = ""
        rec(3, "interaction", "Consider WebMCP (W3C draft, Chrome origin trial): if agents should "
            "operate this UI, register tools with document.modelContext.registerTool() (feature-detect) "
            "so agents can act through the signed-in page (AgentReady AR-ACT-07).")
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
        hit = resp is not None and resp.status_code in (200, 405) \
            and "json" in resp.headers.get("content-type", "").lower()
        if not hit and path == "/mcp":
            hit = mcp_handshake(origin + path)
        if hit:
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
        rec(3, "interfaces", "Only if agents should complete tasks in the product (not just read "
            "it): expose an MCP server over Streamable HTTP at /mcp, OAuth-gated for account actions, "
            "or a CLI (AgentReady AR-ACT-03/AR-ACT-10), and list it in /.well-known/ai-catalog.json. "
            "Content-heavy sites can use NLWeb (/ask) instead. A read-only site does not need one.")
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
        honest_429 = bot_resp.status_code == 429 and bool(bot_resp.headers.get("retry-after"))
        if bot_resp.status_code in (401, 403, 429, 503) and browser_ok and not honest_429:
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

    agentready = agentready_checks(
        r=r, origin=origin, html=html, raw_soup=raw_soup, word_count=word_count,
        bot_blocked=bot_blocked, bot_status=bot_status, found=found_interfaces,
        webmcp=webmcp, rec=rec)
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
        "agentready": agentready,
        "recommendations": recommendations,
    }


# Hosts where many sites share one origin under different paths (user.github.io/project/),
# so a project site cannot own the origin root.
SHARED_PATH_HOSTS = (".github.io", ".gitlab.io")

PRICE_RE = re.compile(r"(?:[$€£₪¥]\s?\d[\d,]*(?:\.\d{2})?|\b\d[\d,]*(?:\.\d{2})?\s?(?:USD|EUR|GBP|ILS)\b"
                      r"|\bfree\b|\bpricing\b|\bper month\b|/mo\b)", re.I)


def agentready_checks(*, r, origin, html, raw_soup, word_count, bot_blocked, bot_status, found,
                      webmcp, rec) -> dict:
    """AgentReady v2.0 checklist (https://agentready.org, spec/spec.md). Only rules a static
    fetch can verify; each row is pass | fail | review (needs a human: e.g. whether agents
    are meant to act on the product)."""
    rows: list[dict] = []

    def row(rid: str, level: str, status: str, evidence: str) -> None:
        rows.append({"id": rid, "level": level, "status": status, "evidence": evidence})

    head = raw_soup.head
    found_paths = {f["path"] for f in found}
    final = urlparse(r.url)
    segments = [s for s in final.path.split("/") if s]
    shared_host = final.netloc.endswith(SHARED_PATH_HOSTS) and bool(segments)
    # The homepage is the origin root, or the project root on a shared path host (user.github.io/app/).
    is_home = not segments or (shared_host and len(segments) == 1 and final.path.endswith("/"))
    link_header = r.headers.get("link", "")

    # AR-FIND-01 (MUST): robots.txt and the network layer let agents in
    robots_r = fetch(origin + "/robots.txt", BROWSER_UA)
    robots = robots_r.text if robots_r is not None and robots_r.status_code == 200 \
        and "html" not in robots_r.headers.get("content-type", "").lower() else ""
    groups: dict[str, list[str]] = {}
    agents: list[str] = []
    in_rules = False
    for line in robots.splitlines():
        line = line.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        key, val = (s.strip() for s in line.split(":", 1))
        key = key.lower()
        if key == "user-agent":
            if in_rules:
                agents, in_rules = [], False
            agents.append(val.lower())
            for a in agents:
                groups.setdefault(a, [])
        elif key in ("disallow", "allow"):
            in_rules = True
            for a in agents:
                groups[a].append(f"{key}:{val}")
    ai_tokens = ("gptbot", "oai-searchbot", "chatgpt-user", "claudebot", "claude-user",
                 "claude-searchbot", "perplexitybot", "perplexity-user", "google-extended")

    whole_site = {"/", "/*", "/*$", "*"}

    def fully_blocked(rules: list[str]) -> bool:
        kinds = {r.split(":", 1)[0] for r in rules if r.split(":", 1)[1] in whole_site}
        return "disallow" in kinds and "allow" not in kinds
    # A crawler obeys its own group if it has one, else the * group (RFC 9309 2.2.1).
    blocked_ai = [tok for tok in ai_tokens if fully_blocked(groups.get(tok, groups.get("*", [])))]
    ok = not blocked_ai and not bot_blocked
    row("AR-FIND-01", "MUST", "pass" if ok else "fail",
        f"robots.txt {'present' if robots else 'absent'}; fully disallowed: {', '.join(blocked_ai) or 'none'}; "
        f"AI-crawler UA got HTTP {bot_status}" + (" (bot wall)" if bot_blocked else ""))
    if blocked_ai:
        rec(1, "access", f"robots.txt disallows the whole site for {', '.join(blocked_ai)}. AgentReady "
            "AR-FIND-01 (MUST): write one policy for all agents (User-agent: *) and block only "
            "low-value paths.")

    # AR-FIND-03 (SHOULD): sitemap referenced from robots.txt
    sm_urls = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", robots)
    sm_r = fetch(sm_urls[0] if sm_urls else origin + "/sitemap.xml", BROWSER_UA)
    sm_ok = sm_r is not None and sm_r.status_code == 200 and ("<urlset" in sm_r.text[:4000]
                                                             or "<sitemapindex" in sm_r.text[:4000])
    row("AR-FIND-03", "SHOULD", "pass" if sm_ok and sm_urls else "fail",
        f"sitemap {'found' if sm_ok else 'not found'}; referenced from robots.txt: {bool(sm_urls)}")
    if not (sm_ok and sm_urls):
        rec(3, "interfaces", "Publish sitemap.xml and reference it from robots.txt (`Sitemap:` line) "
            "(AgentReady AR-FIND-03).")

    # AR-FIND-04 (MAY): AI Catalog, linked from the homepage head or a Link header
    catalog = "/.well-known/ai-catalog.json" in found_paths
    cat_linked = bool(head and head.find("link", rel=lambda v: v and "ai-catalog" in v)) \
        or "ai-catalog" in link_header
    row("AR-FIND-04", "MAY", "pass" if catalog and cat_linked else "fail",
        f"/.well-known/ai-catalog.json: {catalog}; <link rel=\"ai-catalog\"> or Link header: {cat_linked}")

    # AR-READ-01 (MUST): the answer is in the initial HTML
    row("AR-READ-01", "MUST", "pass" if word_count >= 100 else "fail",
        f"{word_count} words of visible text without JavaScript")

    # AR-READ-02 (MUST): honest status codes (no soft 404)
    miss = fetch(urljoin(r.url, "agentready-probe-" + uuid.uuid4().hex[:10]), BROWSER_UA)
    miss_code = miss.status_code if miss is not None else None
    row("AR-READ-02", "MUST", "pass" if miss_code in (404, 410) else "fail",
        f"a made-up path answered HTTP {miss_code}")
    if miss_code == 200:
        rec(1, "content", "Missing pages answer HTTP 200 (soft 404): agents cannot tell dead URLs from "
            "live ones. Return 404 for unknown paths (AgentReady AR-READ-02, MUST). On a single-page "
            "app, prerender known routes and let the host answer 404 for the rest.")

    # AR-READ-03 (SHOULD): homepage is raw HTML with real links
    links = [a.get("href", "") for a in raw_soup.find_all("a", href=True)]
    host = urlparse(r.url).netloc
    internal = [h for h in links if not re.match(r"(?i)(mailto|tel|javascript|data):|#", h)
                and urlparse(urljoin(r.url, h)).netloc == host]
    if is_home:
        row("AR-READ-03", "SHOULD", "pass" if len(internal) >= 3 else "fail",
            f"{len(internal)} internal <a href> links in the raw HTML")
    else:
        row("AR-READ-03", "SHOULD", "review",
            f"audited a subpage ({len(internal)} internal links); run on the homepage to check this rule")

    # AR-READ-06 / 07 (SHOULD): llms.txt exists and is linked from content agents visit
    llms_hrefs = [h for h in links if "llms.txt" in h] + (
        [l.get("href") for l in head.find_all("link") if "llms" in (l.get("href") or "")] if head else [])
    llms_linked = bool(llms_hrefs) or "llms.txt" in link_header
    has_llms = "/llms.txt" in found_paths
    if not has_llms and llms_hrefs:
        # A site under a path (user.github.io/app/) publishes llms.txt next to its pages; agents
        # reach it through the link, so follow it.
        lr = fetch(urljoin(r.url, llms_hrefs[0]), BROWSER_UA)
        has_llms = lr is not None and lr.status_code == 200 \
            and "html" not in lr.headers.get("content-type", "").lower()
    row("AR-READ-07", "SHOULD", "pass" if has_llms else "fail", f"/llms.txt: {has_llms}")
    row("AR-READ-06", "SHOULD", "pass" if has_llms and llms_linked else "fail",
        f"discovery files linked from the page (footer, <link>, Link header): {llms_linked}")
    if has_llms and not llms_linked:
        rec(2, "interfaces", "llms.txt exists but nothing links to it. 86-100% of agent visits to "
            "discovery files come through links, so add it to the footer and as "
            "<link rel=\"alternate\" type=\"text/plain\" href=\"/llms.txt\"> (AgentReady AR-READ-06).")

    # AR-READ-08 (SHOULD): JSON-LD on the homepage
    ld = raw_soup.find_all("script", type=lambda v: v and "ld+json" in v.lower())
    row("AR-READ-08", "SHOULD", "pass" if ld else ("fail" if is_home else "review"),
        f"{len(ld)} JSON-LD block(s) in the raw HTML" + ("" if is_home else " (subpage; the rule is about the homepage)"))
    if not ld and is_home:
        rec(2, "content", "Add JSON-LD to the homepage (Organization / SoftwareApplication / Product) so "
            "an agent gets key facts in one block, and repeat critical facts in visible text "
            "(AgentReady AR-READ-08).")

    # AR-READ-09 (MAY): markdown mirror advertised
    md_link = bool(head and head.find("link", type=lambda v: v and "markdown" in v.lower())) \
        or "text/markdown" in link_header
    md_nego = any(f["name"] == "Markdown content negotiation" for f in found)
    row("AR-READ-09", "MAY", "pass" if md_link or md_nego else "fail",
        f"<link rel=alternate type=text/markdown>: {md_link}; Accept: text/markdown served: {md_nego}")

    # AR-READ-11 (SHOULD): pricing as text on a first-party page
    text = raw_soup.get_text(" ", strip=True)
    price_hits = sorted({m.group(0) for m in PRICE_RE.finditer(text)})[:5]
    def states_price(words: list[str]) -> bool:
        return any(not re.fullmatch(r"(?i)free|pricing|per month|/mo", w) for w in words)
    priced = states_price(price_hits)
    price_links = []
    for h in (h for h in links if re.search(r"(?i)pric|plans|tarif", h)):
        target = urljoin(r.url, h).split("#", 1)[0]
        if urlparse(target).netloc != final.netloc:
            continue  # not first-party
        if target.rstrip("/") == r.url.split("#", 1)[0].rstrip("/"):
            continue  # an anchor on this same page: its text was checked above
        pr = fetch(target, BROWSER_UA)
        if pr is not None and pr.status_code == 200:
            ptext = BeautifulSoup(pr.text, "html.parser").get_text(" ", strip=True)
            if states_price([m.group(0) for m in PRICE_RE.finditer(ptext)]):
                price_links.append(h)
                break
    row("AR-READ-11", "SHOULD", "pass" if priced or price_links else "review",
        f"price words in the text: {price_hits or 'none'}; pricing links: {price_links[:2] or 'none'}")
    if not (price_hits or price_links):
        rec(2, "content", "No pricing in the page text. If the product charges (or is free), say so in "
            "plain HTML text on a first-party page: agents answered pricing correctly 60% of the time "
            "from the site vs 37% from elsewhere (AgentReady AR-READ-11).")

    # AR-ACT-* (only when agents are meant to act on the product)
    mcp = "/mcp" in found_paths
    prm = fetch(origin + "/.well-known/oauth-protected-resource", BROWSER_UA)
    prm_ok = prm is not None and prm.status_code == 200 and "json" in prm.headers.get("content-type", "")
    openapi = any(p in found_paths for p in ("/openapi.json", "/api/openapi.json"))
    row("AR-ACT-02", "SHOULD*", "pass" if openapi else "review", f"OpenAPI found: {openapi}")
    row("AR-ACT-03", "SHOULD*", "pass" if mcp else "review",
        f"/mcp endpoint: {mcp}; /.well-known/oauth-protected-resource: {prm_ok}")
    row("AR-ACT-07", "SHOULD*", "pass" if webmcp else "review", f"WebMCP in the initial HTML: {webmcp}")
    row("AR-ACT-10", "MUST*", "pass" if mcp else "review",
        "MCP server found" if mcp else "no MCP server found; a CLI can also satisfy it. Required only "
        "if agents are expected to complete tasks in the product")

    if shared_host and not robots and not has_llms:
        rec(2, "interfaces", "The site lives under a path of a shared host, so it cannot publish its own "
            "/robots.txt, /sitemap.xml, /llms.txt or /.well-known/ files at the origin root. A custom domain "
            "fixes that.")
    summary = {
        "spec": "AgentReady 2.0 (agentready.org, October 2026)",
        "must_failed": [x["id"] for x in rows if x["level"] == "MUST" and x["status"] == "fail"],
        "should_failed": [x["id"] for x in rows if x["level"] == "SHOULD" and x["status"] == "fail"],
        "note": "* = applies only when agents should act on the product, not just read it",
    }
    return {"summary": summary, "checks": rows}


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: agent_readiness.py <url>", file=sys.stderr)
        return 2
    print(json.dumps(analyze(sys.argv[1]), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
