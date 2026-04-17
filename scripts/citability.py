#!/usr/bin/env python3
"""Score on-page passages for AI citation readiness.

Heuristic only. Rewards passages that are:
  - 100-200 words (sweet spot 134-167)
  - self-contained (don't open with vague pronouns or back-references)
  - fact-rich (numbers, dates, percentages, named entities)
  - direct answers (contain answer-shaped phrasing)

The score is 0-100. Treat it as directional, not authoritative.
"""
from __future__ import annotations

import json
import re
import sys

import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (compatible; geo-skill/1.0)"
TIMEOUT = 20

WEAK_OPENERS = {
    "however", "therefore", "thus", "moreover", "furthermore", "additionally",
    "this", "that", "these", "those", "it", "they", "he", "she", "we", "you",
    "also", "but", "and", "so", "then", "meanwhile", "consequently",
}

ANSWER_HINTS = (
    "is a", "is an", "are a", "are the", "refers to", "means that",
    "consists of", "is defined", "is used to", "works by", "allows you",
    "you can", "the best", "the difference", "the main",
)

NOISE_TAGS = {"script", "style", "noscript", "nav", "footer", "aside", "form", "header"}


def extract_passages(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(NOISE_TAGS):
        tag.decompose()

    candidates: list[str] = []
    for tag in soup.find_all(["p", "li"]):
        text = " ".join(tag.get_text(" ", strip=True).split())
        if len(text.split()) >= 30:
            candidates.append(text)
    return candidates


def score_passage(text: str) -> dict:
    words = text.split()
    n = len(words)

    # Length: triangular peak at ~150 words, zero outside 60-260
    if n < 60 or n > 260:
        length_score = 0.0
    else:
        peak = 150.0
        spread = 90.0
        length_score = max(0.0, 1.0 - abs(n - peak) / spread)

    # Self-contained: penalize if first word is a weak opener
    first = re.sub(r"[^a-z]", "", words[0].lower()) if words else ""
    self_contained = 0.0 if first in WEAK_OPENERS else 1.0

    # Fact density: count numbers, percentages, years, capitalized multi-word phrases
    numbers = len(re.findall(r"\b\d[\d,\.]*\b", text))
    percents = len(re.findall(r"\d+\s*%", text))
    years = len(re.findall(r"\b(19|20)\d{2}\b", text))
    proper = len(re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b", text))
    fact_raw = numbers + 2 * percents + 2 * years + proper
    fact_score = min(1.0, fact_raw / 10.0)

    # Direct answer phrasing
    lower = text.lower()
    answer_score = 1.0 if any(h in lower for h in ANSWER_HINTS) else 0.3

    composite = (
        0.40 * length_score
        + 0.20 * self_contained
        + 0.25 * fact_score
        + 0.15 * answer_score
    )
    return {
        "words": n,
        "length_score": round(length_score, 2),
        "self_contained": self_contained,
        "fact_score": round(fact_score, 2),
        "answer_score": answer_score,
        "score": round(composite * 100, 1),
        "preview": text[:180] + ("..." if len(text) > 180 else ""),
    }


def analyze(url: str) -> dict:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT)
    passages = extract_passages(r.text)
    scored = [score_passage(p) for p in passages]
    scored.sort(key=lambda x: x["score"], reverse=True)

    total = len(scored)
    if total == 0:
        return {
            "url": url,
            "passage_count": 0,
            "avg_score": 0,
            "top": [],
            "note": "No paragraphs of 30+ words found. Page may be JS-rendered or content-thin.",
        }

    avg = sum(s["score"] for s in scored) / total
    in_band = sum(1 for s in scored if 100 <= s["words"] <= 200)
    return {
        "url": url,
        "passage_count": total,
        "passages_in_optimal_band": in_band,
        "avg_score": round(avg, 1),
        "top": scored[:5],
        "weakest": scored[-3:],
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: citability.py <url>", file=sys.stderr)
        return 2
    print(json.dumps(analyze(sys.argv[1]), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
