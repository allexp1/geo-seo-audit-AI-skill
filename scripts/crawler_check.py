#!/usr/bin/env python3
"""Fetch /robots.txt and report which AI crawlers are allowed or blocked.

Reports:
  - explicit Allow / Disallow rules per known AI bot
  - whether the wildcard User-agent: * blocks them
  - bots that are not mentioned at all (default = allowed)
"""
from __future__ import annotations

import json
import sys
from urllib.parse import urlparse

import requests

UA = "Mozilla/5.0 (compatible; geo-skill/1.0)"
TIMEOUT = 15

# (token, vendor, purpose). Tokens are matched case-insensitively against
# robots.txt User-agent lines.
AI_BOTS = [
    ("GPTBot", "OpenAI", "training"),
    ("ChatGPT-User", "OpenAI", "user-triggered fetch"),
    ("OAI-SearchBot", "OpenAI", "search index"),
    ("ClaudeBot", "Anthropic", "training"),
    ("Claude-Web", "Anthropic", "user-triggered fetch"),
    ("anthropic-ai", "Anthropic", "legacy"),
    ("PerplexityBot", "Perplexity", "search index"),
    ("Perplexity-User", "Perplexity", "user-triggered fetch"),
    ("Google-Extended", "Google", "Gemini training"),
    ("GoogleOther", "Google", "research / experimental"),
    ("Applebot-Extended", "Apple", "Apple Intelligence training"),
    ("Bytespider", "ByteDance", "training (Doubao etc.)"),
    ("CCBot", "Common Crawl", "shared training corpus"),
    ("cohere-ai", "Cohere", "training"),
    ("Diffbot", "Diffbot", "knowledge graph"),
    ("FacebookBot", "Meta", "training"),
    ("Meta-ExternalAgent", "Meta", "training"),
    ("ImagesiftBot", "Hive", "image dataset"),
    ("Omgili", "Webz.io", "dataset"),
    ("YouBot", "You.com", "search index"),
    ("Amazonbot", "Amazon", "Alexa / training"),
    ("Mistral-AI", "Mistral", "training"),
]


def parse_robots(text: str) -> dict[str, list[tuple[str, str]]]:
    """Return {agent_token_lower: [(directive, value), ...]} preserving order.

    A robots.txt 'group' is one or more User-agent lines followed by directives
    until the next User-agent line.
    """
    groups: dict[str, list[tuple[str, str]]] = {}
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
    return groups


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


def check(url: str) -> dict:
    parsed = urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
        parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    out: dict = {"robots_url": robots_url}
    try:
        r = requests.get(robots_url, headers={"User-Agent": UA}, timeout=TIMEOUT)
    except Exception as e:
        out["error"] = str(e)
        return out

    out["status"] = r.status_code
    if r.status_code != 200:
        out["robots_present"] = False
        out["bots"] = [
            {"token": t, "vendor": v, "purpose": p, "blocked_root": False, "source": "no-robots"}
            for t, v, p in AI_BOTS
        ]
        out["summary"] = {"total": len(AI_BOTS), "blocked": 0, "explicit": 0}
        return out

    out["robots_present"] = True
    out["robots_size"] = len(r.text)
    groups = parse_robots(r.text)

    bots = []
    blocked = 0
    explicit = 0
    for token, vendor, purpose in AI_BOTS:
        s = status_for(token, groups)
        if s["source"] == "explicit":
            explicit += 1
        if s["blocked_root"]:
            blocked += 1
        bots.append({"token": token, "vendor": vendor, "purpose": purpose, **s})

    out["bots"] = bots
    out["summary"] = {"total": len(AI_BOTS), "blocked": blocked, "explicit": explicit}
    return out


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: crawler_check.py <url>", file=sys.stderr)
        return 2
    print(json.dumps(check(sys.argv[1]), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
