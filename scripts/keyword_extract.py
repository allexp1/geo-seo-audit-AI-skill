#!/usr/bin/env python3
"""Extract target keywords from a page.

Scores each term/phrase by:
  1. Raw frequency in body text
  2. Position bonus: appears in title (5x), H1 (4x), H2 (3x), meta description (3x)
  3. N-gram support: single words + 2-grams + 3-grams

Outputs top-ranked keywords as JSON, ready to feed into keyword_rank.py.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter

import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (compatible; geo-skill/1.0)"
TIMEOUT = 20

STOPWORDS = frozenset(
    "a an the and or but if in on at to for of with by from is are was were be "
    "been being have has had do does did will would shall should may might can could "
    "this that these those it its he she they them we you your our his her their "
    "i me my mine us him who what which where when how why not no nor so as up out "
    "about above after again all also am any because before between both each few get "
    "got into just more most much must no only other own same some such than too very "
    "s t d ll ve re m don didn doesn won isn aren wasn weren hasn hasn't couldn "
    "shouldn wouldn let one two three new way go going like make makes made use used using "
    "even still well back also already always another while since then through over "
    "really right here there find found say said see look take come know need want "
    "thing things part work great good best first last long need know try try help "
    "learn read start end next keep every set many much own day time year people "
    "world will just now get way see".split()
)

NOISE_TAGS = {"script", "style", "noscript", "nav", "footer", "header", "form", "button"}


def normalize(text: str) -> list[str]:
    """Lowercase, strip non-alpha, split."""
    return [w for w in re.sub(r"[^a-z0-9\s]", "", text.lower()).split() if w and w not in STOPWORDS and len(w) > 2]


def ngrams(words: list[str], n: int) -> list[str]:
    return [" ".join(words[i : i + n]) for i in range(len(words) - n + 1)]


def extract(url: str) -> dict:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT, allow_redirects=True)
    soup = BeautifulSoup(r.text, "html.parser")

    # Extract positioned text
    title = (soup.title.string.strip() if soup.title and soup.title.string else "")
    md = soup.find("meta", attrs={"name": "description"})
    meta_desc = md["content"].strip() if md and md.get("content") else ""
    h1_text = " ".join(h.get_text(" ", strip=True) for h in soup.find_all("h1"))
    h2_text = " ".join(h.get_text(" ", strip=True) for h in soup.find_all("h2"))
    h3_text = " ".join(h.get_text(" ", strip=True) for h in soup.find_all("h3"))

    # Body text
    for tag in soup.find_all(NOISE_TAGS):
        tag.decompose()
    body_text = soup.body.get_text(" ", strip=True) if soup.body else ""

    body_words = normalize(body_text)
    title_words = normalize(title)
    meta_words = normalize(meta_desc)
    h1_words = normalize(h1_text)
    h2_words = normalize(h2_text)
    h3_words = normalize(h3_text)

    # Count 1-grams, 2-grams, 3-grams from body
    counts: Counter = Counter()
    for n in (1, 2, 3):
        counts.update(ngrams(body_words, n))

    # Position bonuses
    position_bonus: Counter = Counter()
    for n in (1, 2, 3):
        for term in ngrams(title_words, n):
            position_bonus[term] += 5
        for term in ngrams(h1_words, n):
            position_bonus[term] += 4
        for term in ngrams(meta_words, n):
            position_bonus[term] += 3
        for term in ngrams(h2_words, n):
            position_bonus[term] += 3
        for term in ngrams(h3_words, n):
            position_bonus[term] += 2

    # Combine: frequency * (1 + position_bonus)
    scored: dict[str, float] = {}
    for term, freq in counts.items():
        if freq < 2 and term not in position_bonus:
            continue
        bonus = position_bonus.get(term, 0)
        scored[term] = freq * (1 + bonus)

    # Filter out substrings subsumed by longer phrases with higher scores
    ranked = sorted(scored.items(), key=lambda x: x[1], reverse=True)

    # Take top 30 candidates
    top = ranked[:30]

    keywords = []
    for term, score in top:
        freq = counts[term]
        bonus = position_bonus.get(term, 0)
        locations = []
        if any(term in " ".join(ngrams(title_words, len(term.split()))) for _ in [1]):
            if term in " ".join(ngrams(title_words, len(term.split()))):
                locations.append("title")
        if term in " ".join(ngrams(h1_words, len(term.split()))):
            locations.append("h1")
        if term in " ".join(ngrams(meta_words, len(term.split()))):
            locations.append("meta")
        if term in " ".join(ngrams(h2_words, len(term.split()))):
            locations.append("h2")
        keywords.append({
            "keyword": term,
            "score": round(score, 1),
            "frequency": freq,
            "found_in": locations or ["body"],
        })

    return {
        "url": r.url,
        "total_words": len(body_words),
        "unique_terms": len(counts),
        "keywords": keywords[:20],
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: keyword_extract.py <url>", file=sys.stderr)
        return 2
    print(json.dumps(extract(sys.argv[1]), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
