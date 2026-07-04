#!/usr/bin/env python3
"""On-page SEO checks parsed from HTML.

Covers:
  - Title length (30-60 chars optimal)
  - Meta description length (120-160 chars optimal)
  - Heading hierarchy (exactly one H1, sensible H2/H3 counts)
  - Open Graph tags (og:title, og:description, og:image, og:url, og:type)
  - Twitter Card tags
  - Mobile viewport meta
  - <html lang="..."> attribute
  - Charset declaration
  - Image alt text coverage
  - Internal vs external link counts
  - Word count
  - Favicon
  - noindex / nofollow detection
"""
from __future__ import annotations

import json
import sys
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (compatible; geo-skill/1.0)"
TIMEOUT = 20

OG_FIELDS = ["og:title", "og:description", "og:image", "og:url", "og:type", "og:site_name"]
TWITTER_FIELDS = ["twitter:card", "twitter:title", "twitter:description", "twitter:image"]


def text_or_empty(tag) -> str:
    if not tag:
        return ""
    if tag.has_attr("content"):
        return tag["content"].strip()
    return tag.get_text(strip=True)


def analyze(url: str) -> dict:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT, allow_redirects=True)
    soup = BeautifulSoup(r.text, "html.parser")
    parsed = urlparse(r.url)
    origin = f"{parsed.scheme}://{parsed.netloc}"

    # Title
    title = (soup.title.string.strip() if soup.title and soup.title.string else "")

    # Meta description
    md = soup.find("meta", attrs={"name": "description"})
    meta_desc = md["content"].strip() if md and md.get("content") else ""

    # Robots meta
    robots_meta = soup.find("meta", attrs={"name": "robots"})
    robots_content = robots_meta["content"].lower() if robots_meta and robots_meta.get("content") else ""

    # Snippet controls: these also govern what Google AI Overviews / AI Mode may
    # quote from the page (Google's AI-optimization guide, 2026).
    snippet_controls = {
        "nosnippet": "nosnippet" in robots_content,
        "max_snippet": next((p.strip() for p in robots_content.split(",") if "max-snippet" in p), ""),
        "data_nosnippet_blocks": len(soup.find_all(attrs={"data-nosnippet": True})),
    }

    # Canonical
    canonical_tag = soup.find("link", rel="canonical")
    canonical = canonical_tag["href"].strip() if canonical_tag and canonical_tag.get("href") else ""

    # Headings
    h1 = [h.get_text(strip=True) for h in soup.find_all("h1")]
    h2 = soup.find_all("h2")
    h3 = soup.find_all("h3")

    # Open Graph
    og = {}
    for f in OG_FIELDS:
        tag = soup.find("meta", attrs={"property": f})
        og[f] = text_or_empty(tag)

    # Twitter
    tw = {}
    for f in TWITTER_FIELDS:
        tag = soup.find("meta", attrs={"name": f})
        tw[f] = text_or_empty(tag)

    # Viewport, lang, charset
    vp = soup.find("meta", attrs={"name": "viewport"})
    viewport = vp["content"].strip() if vp and vp.get("content") else ""

    html_tag = soup.find("html")
    lang = html_tag.get("lang", "").strip() if html_tag else ""

    # Charset: either <meta charset="..."> or <meta http-equiv="Content-Type">
    cs = soup.find("meta", attrs={"charset": True})
    if cs:
        charset = cs["charset"].strip()
    else:
        ct = soup.find("meta", attrs={"http-equiv": lambda v: v and v.lower() == "content-type"})
        charset = ""
        if ct and ct.get("content") and "charset=" in ct["content"].lower():
            charset = ct["content"].lower().split("charset=", 1)[1].strip()

    # Favicon
    fav = soup.find("link", rel=lambda v: v and "icon" in v)
    favicon = fav["href"].strip() if fav and fav.get("href") else ""

    # Images and alt coverage
    images = soup.find_all("img")
    img_total = len(images)
    img_with_alt = sum(1 for i in images if i.get("alt", "").strip())
    img_decorative = sum(1 for i in images if i.has_attr("alt") and not i["alt"].strip())

    # Links: internal vs external
    links = soup.find_all("a", href=True)
    internal = 0
    external = 0
    nofollow = 0
    for a in links:
        href = a["href"].strip()
        if href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
            continue
        rel = (a.get("rel") or [])
        if isinstance(rel, str):
            rel = rel.split()
        if "nofollow" in [x.lower() for x in rel]:
            nofollow += 1
        if href.startswith("/") or origin in href:
            internal += 1
        elif href.startswith("http"):
            external += 1

    # Word count of visible body text (rough)
    for t in soup.find_all(["script", "style", "noscript"]):
        t.decompose()
    body = soup.body
    word_count = len(body.get_text(" ", strip=True).split()) if body else 0

    # Score components
    score = 0
    notes: list[str] = []

    # Title (15 pts) — 2026 guidance: 50-60 chars with entity names
    if 30 <= len(title) <= 60:
        score += 15
        if len(title) < 50:
            notes.append(f"title {len(title)} chars is fine; 50-60 with entity names is ideal")
    elif title:
        score += 8
        notes.append(f"title length {len(title)} (target 50-60)")
    else:
        notes.append("missing <title>")

    # Meta description (15 pts) — doubles as AI Overview citation-card text;
    # 2026 guidance: 140-160 chars, answer-aligned
    if 120 <= len(meta_desc) <= 160:
        score += 15
    elif meta_desc:
        score += 7
        notes.append(f"meta description {len(meta_desc)} chars (target 140-160, answer-aligned)")
    else:
        notes.append("missing meta description")

    # H1 uniqueness (10 pts)
    if len(h1) == 1:
        score += 10
    elif len(h1) > 1:
        score += 4
        notes.append(f"{len(h1)} H1s (should be 1)")
    else:
        notes.append("missing H1")

    # Headings hierarchy (5 pts)
    if len(h2) >= 1:
        score += 5
    else:
        notes.append("no H2s")

    # Canonical (10 pts)
    if canonical:
        score += 10
    else:
        notes.append("missing canonical")

    # Open Graph (10 pts: 2 each for the core 5)
    og_present = sum(1 for f in ["og:title", "og:description", "og:image", "og:url", "og:type"] if og.get(f))
    score += og_present * 2

    # Twitter card (5 pts)
    if tw.get("twitter:card"):
        score += 5
    else:
        notes.append("missing twitter:card")

    # Mobile viewport (10 pts)
    if viewport:
        score += 10
    else:
        notes.append("missing mobile viewport meta")

    # lang attribute (5 pts)
    if lang:
        score += 5
    else:
        notes.append("missing <html lang>")

    # Charset (5 pts)
    if charset:
        score += 5
    else:
        notes.append("missing charset declaration")

    # Image alt coverage (10 pts)
    if img_total == 0:
        score += 10  # no penalty for no images
    else:
        coverage = (img_with_alt + img_decorative) / img_total
        score += int(coverage * 10)
        if coverage < 0.9:
            notes.append(f"only {img_with_alt}/{img_total} images have alt text")

    # noindex penalty
    if "noindex" in robots_content:
        score = max(0, score - 30)
        notes.append("page is noindexed (-30)")

    return {
        "url": r.url,
        "score": score,
        "notes": notes,
        "title": {"value": title, "length": len(title)},
        "meta_description": {"value": meta_desc, "length": len(meta_desc)},
        "robots_meta": robots_content,
        "snippet_controls": snippet_controls,
        "canonical": canonical,
        "headings": {"h1": h1, "h2_count": len(h2), "h3_count": len(h3)},
        "open_graph": og,
        "twitter_card": tw,
        "viewport": viewport,
        "lang": lang,
        "charset": charset,
        "favicon": favicon,
        "images": {"total": img_total, "with_alt": img_with_alt, "decorative": img_decorative},
        "links": {"internal": internal, "external": external, "nofollow": nofollow},
        "word_count": word_count,
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: onpage_seo.py <url>", file=sys.stderr)
        return 2
    print(json.dumps(analyze(sys.argv[1]), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
