#!/usr/bin/env python3
"""Fetch /robots.txt and report which AI crawlers are allowed or blocked.

Bot roster current as of mid-2026. Reports:
  - explicit Allow / Disallow rules per known AI bot
  - whether the wildcard User-agent: * blocks them
  - bots not mentioned at all (default = allowed)
  - bot CATEGORY: blocking a search/user-fetch bot removes you from AI answers;
    blocking a training bot is a policy choice
  - stale tokens (anthropic-ai, claude-web, FacebookBot) that no longer match
    any live crawler
  - Content-Signal lines (Cloudflare's machine-readable AI policy, 2025)
  - whether core search bots (Googlebot/Bingbot) are blocked — that also kills
    AI Overviews / Copilot visibility
  - Cloudflare fingerprint: since July 2025 Cloudflare blocks AI training
    crawlers BY DEFAULT for new zones, regardless of robots.txt
"""
from __future__ import annotations

import json
import sys
from urllib.parse import urlparse

import requests

UA = "Mozilla/5.0 (compatible; geo-skill/2.0)"
TIMEOUT = 15

# (token, vendor, purpose, category)
# category: "search"     — feeds an AI search index; blocking removes you from answers
#           "user-fetch" — fetches on behalf of a live user question; blocking hides you
#           "training"   — model training corpus; blocking is a policy choice
#           "ads"        — ad landing-page validation
#           "other"      — research / knowledge graph
AI_BOTS = [
    ("GPTBot", "OpenAI", "model training", "training"),
    ("OAI-SearchBot", "OpenAI", "ChatGPT search index", "search"),
    ("ChatGPT-User", "OpenAI", "user-triggered fetch", "user-fetch"),
    ("OAI-AdsBot", "OpenAI", "ChatGPT ads landing-page checks", "ads"),
    ("ClaudeBot", "Anthropic", "model training", "training"),
    ("Claude-SearchBot", "Anthropic", "Claude search index", "search"),
    ("Claude-User", "Anthropic", "user-triggered fetch", "user-fetch"),
    ("PerplexityBot", "Perplexity", "search index", "search"),
    ("Perplexity-User", "Perplexity", "user-triggered fetch", "user-fetch"),
    ("Google-Extended", "Google", "Gemini training opt-out token", "training"),
    ("Google-CloudVertexBot", "Google", "Vertex AI site grounding", "training"),
    ("GoogleOther", "Google", "research / experimental", "other"),
    ("Applebot", "Apple", "Siri/Spotlight + Apple Intelligence retrieval", "search"),
    ("Applebot-Extended", "Apple", "Apple Intelligence training opt-out", "training"),
    ("Meta-ExternalAgent", "Meta", "training / indexing", "training"),
    ("Meta-ExternalFetcher", "Meta", "user/agent-triggered fetch", "user-fetch"),
    ("Amazonbot", "Amazon", "Alexa answers / training", "search"),
    ("Bytespider", "ByteDance", "training (Doubao; known to ignore robots.txt)", "training"),
    ("CCBot", "Common Crawl", "shared training corpus", "training"),
    ("DuckAssistBot", "DuckDuckGo", "DuckAssist answers (not training)", "search"),
    ("MistralAI-User", "Mistral", "user-triggered fetch (Le Chat)", "user-fetch"),
    ("Diffbot", "Diffbot", "knowledge graph", "other"),
    ("YouBot", "You.com", "search index", "search"),
]

# Tokens that no longer match any live crawler. Rules that target them are
# dead weight and usually indicate a robots.txt written pre-2025.
STALE_TOKENS = {
    "anthropic-ai": "retired — Anthropic now uses ClaudeBot / Claude-SearchBot / Claude-User",
    "claude-web": "retired — replaced by Claude-User",
    "facebookbot": "legacy — Meta now uses Meta-ExternalAgent / Meta-ExternalFetcher",
}

# Blocking these also removes the site from AI answer surfaces built on the
# classic indexes (AI Overviews / AI Mode run on Googlebot; Copilot on Bingbot).
CORE_SEARCH_BOTS = ["Googlebot", "Bingbot"]


def parse_robots(text: str) -> tuple[dict[str, list[tuple[str, str]]], list[str]]:
    """Return ({agent_token_lower: [(directive, value), ...]}, content_signals).

    A robots.txt 'group' is one or more User-agent lines followed by directives
    until the next User-agent line. Content-Signal lines (Cloudflare, 2025) are
    collected separately.
    """
    groups: dict[str, list[tuple[str, str]]] = {}
    content_signals: list[str] = []
    current_agents: list[str] = []
    expecting_agent_block = True
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if ":" not in line:
            continue
        field, _, value = line.partition(":")
        field = field.strip().lower()
        value = value.strip()
        if field == "content-signal":
            content_signals.append(value)
            continue
        if field == "user-agent":
            if not expecting_agent_block:
                current_agents = []
                expecting_agent_block = True
            current_agents.append(value.lower())
            groups.setdefault(value.lower(), [])
        else:
            expecting_agent_block = False
            for a in current_agents:
                groups.setdefault(a, []).append((field, value))
    return groups, content_signals


def status_for(bot_token: str, groups: dict[str, list[tuple[str, str]]]) -> dict:
    token = bot_token.lower()
    rules = groups.get(token)
    wildcard = groups.get("*", [])

    if rules is not None:
        disallows = [v for f, v in rules if f == "disallow" and v]
        allows = [v for f, v in rules if f == "allow" and v]
        blocked_root = any(d == "/" for d in disallows)
        return {
            "mentioned": True,
            "blocked_root": blocked_root,
            "disallow": disallows,
            "allow": allows,
            "source": "explicit",
        }

    # Fall back to wildcard
    w_disallows = [v for f, v in wildcard if f == "disallow" and v]
    blocked_root = any(d == "/" for d in w_disallows)
    return {
        "mentioned": False,
        "blocked_root": blocked_root,
        "disallow": w_disallows,
        "allow": [v for f, v in wildcard if f == "allow" and v],
        "source": "wildcard" if wildcard else "default-allow",
    }


def detect_cloudflare(origin: str) -> dict:
    """Cloudflare blocks AI training crawlers by default since July 2025, and
    (from 2026-09-15) mixed-use crawlers on ad-monetized pages. robots.txt can
    look permissive while the WAF still 403s AI bots, so surface the fingerprint."""
    out = {"behind_cloudflare": False}
    try:
        r = requests.get(origin, headers={"User-Agent": UA}, timeout=TIMEOUT)
        server = r.headers.get("Server", "").lower()
        if "cloudflare" in server or "cf-ray" in {k.lower() for k in r.headers}:
            out["behind_cloudflare"] = True
            out["note"] = (
                "Site is behind Cloudflare, which blocks AI training crawlers by default "
                "for zones created after July 2025 (and mixed-use crawlers on ad-monetized "
                "pages from 2026-09-15) — even if robots.txt allows them. Verify actual bot "
                "access in the Cloudflare dashboard (AI Crawl Control)."
            )
    except Exception as e:
        out["error"] = str(e)
    return out


def check(url: str) -> dict:
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
        parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    robots_url = f"{origin}/robots.txt"

    out: dict = {"robots_url": robots_url}
    try:
        r = requests.get(robots_url, headers={"User-Agent": UA}, timeout=TIMEOUT)
    except Exception as e:
        out["error"] = str(e)
        return out

    out["status"] = r.status_code
    out["cloudflare"] = detect_cloudflare(origin)

    if r.status_code != 200:
        out["robots_present"] = False
        out["bots"] = [
            {"token": t, "vendor": v, "purpose": p, "category": c,
             "blocked_root": False, "source": "no-robots"}
            for t, v, p, c in AI_BOTS
        ]
        out["summary"] = {
            "total": len(AI_BOTS), "blocked": 0, "explicit": 0,
            "blocked_search": 0, "blocked_user_fetch": 0, "blocked_training": 0,
        }
        out["content_signals"] = []
        out["stale_tokens"] = []
        out["core_search_blocked"] = []
        return out

    out["robots_present"] = True
    out["robots_size"] = len(r.text)
    groups, content_signals = parse_robots(r.text)
    out["content_signals"] = content_signals

    bots = []
    blocked = explicit = 0
    blocked_by_cat = {"search": 0, "user-fetch": 0, "training": 0, "ads": 0, "other": 0}
    for token, vendor, purpose, category in AI_BOTS:
        s = status_for(token, groups)
        if s["source"] == "explicit":
            explicit += 1
        if s["blocked_root"]:
            blocked += 1
            blocked_by_cat[category] += 1
        bots.append({"token": token, "vendor": vendor, "purpose": purpose,
                     "category": category, **s})

    out["bots"] = bots
    out["summary"] = {
        "total": len(AI_BOTS),
        "blocked": blocked,
        "explicit": explicit,
        "blocked_search": blocked_by_cat["search"],
        "blocked_user_fetch": blocked_by_cat["user-fetch"],
        "blocked_training": blocked_by_cat["training"],
    }

    out["stale_tokens"] = [
        {"token": t, "note": note}
        for t, note in STALE_TOKENS.items() if t in groups
    ]

    core_blocked = []
    for token in CORE_SEARCH_BOTS:
        s = status_for(token, groups)
        if s["blocked_root"]:
            core_blocked.append(token)
    out["core_search_blocked"] = core_blocked
    if core_blocked:
        out["core_search_warning"] = (
            f"{', '.join(core_blocked)} blocked at root — this also removes the site "
            "from Google AI Overviews / AI Mode and Microsoft Copilot, which are built "
            "on the classic search indexes."
        )

    return out


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: crawler_check.py <url>", file=sys.stderr)
        return 2
    print(json.dumps(check(sys.argv[1]), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
