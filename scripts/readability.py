#!/usr/bin/env python3
"""Readability analysis of a page's visible text.

Computes:
  - Flesch Reading Ease (0-100, higher = easier)
  - Flesch-Kincaid Grade Level (US school grade)
  - Gunning Fog Index
  - Average sentence length (words)
  - Average word length (syllables)
  - Percentage of complex words (3+ syllables)
"""
from __future__ import annotations

import json
import re
import sys

import requests
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (compatible; geo-skill/1.0)"
TIMEOUT = 20

NOISE_TAGS = {"script", "style", "noscript", "nav", "footer", "header", "form"}


def count_syllables(word: str) -> int:
    """Approximate syllable count using vowel-group heuristic."""
    word = word.lower().strip()
    if not word:
        return 0
    if len(word) <= 3:
        return 1
    # Remove trailing silent e
    if word.endswith("e"):
        word = word[:-1]
    # Count vowel groups
    groups = re.findall(r"[aeiouy]+", word)
    count = len(groups)
    return max(1, count)


def split_sentences(text: str) -> list[str]:
    """Split text into sentences (simple heuristic)."""
    # Split on sentence-ending punctuation followed by space/newline and capital
    raw = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
    return [s.strip() for s in raw if s.strip() and len(s.split()) >= 3]


def analyze(url: str) -> dict:
    r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT, allow_redirects=True)
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup.find_all(NOISE_TAGS):
        tag.decompose()

    body = soup.body
    text = body.get_text(" ", strip=True) if body else ""

    # Clean up: collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    sentences = split_sentences(text)
    if not sentences:
        return {
            "url": r.url,
            "error": "No sentences detected. Page may be JS-rendered or content-thin.",
        }

    words_all: list[str] = []
    for s in sentences:
        words_all.extend(re.findall(r"[a-zA-Z]+", s))

    total_words = len(words_all)
    total_sentences = len(sentences)
    total_syllables = sum(count_syllables(w) for w in words_all)

    if total_words == 0 or total_sentences == 0:
        return {
            "url": r.url,
            "error": "Not enough content for readability analysis.",
        }

    avg_words_per_sentence = total_words / total_sentences
    avg_syllables_per_word = total_syllables / total_words

    # Complex words: 3+ syllables, excluding common suffixes
    complex_words = [w for w in words_all if count_syllables(w) >= 3]
    pct_complex = len(complex_words) / total_words * 100

    # Flesch Reading Ease
    fre = 206.835 - (1.015 * avg_words_per_sentence) - (84.6 * avg_syllables_per_word)
    fre = max(0, min(100, fre))

    # Flesch-Kincaid Grade Level
    fkgl = (0.39 * avg_words_per_sentence) + (11.8 * avg_syllables_per_word) - 15.59

    # Gunning Fog Index
    fog = 0.4 * (avg_words_per_sentence + pct_complex)

    # Interpret
    if fre >= 80:
        level = "very easy (6th grade)"
    elif fre >= 70:
        level = "easy (7th grade)"
    elif fre >= 60:
        level = "standard (8th-9th grade)"
    elif fre >= 50:
        level = "fairly difficult (10th-12th grade)"
    elif fre >= 30:
        level = "difficult (college)"
    else:
        level = "very difficult (college graduate)"

    # AI search note: Perplexity and ChatGPT tend to cite passages at 8th-10th grade level
    ai_friendly = 50 <= fre <= 70

    return {
        "url": r.url,
        "total_words": total_words,
        "total_sentences": total_sentences,
        "avg_words_per_sentence": round(avg_words_per_sentence, 1),
        "avg_syllables_per_word": round(avg_syllables_per_word, 2),
        "complex_word_pct": round(pct_complex, 1),
        "flesch_reading_ease": round(fre, 1),
        "flesch_kincaid_grade": round(fkgl, 1),
        "gunning_fog": round(fog, 1),
        "level": level,
        "ai_citation_friendly": ai_friendly,
        "note": (
            "Sweet spot for AI citations is 8th-10th grade (Flesch 50-70). "
            + ("You're in the sweet spot." if ai_friendly else
               "Consider simplifying." if fre < 50 else
               "Content is very simple — add more specific facts and terminology to boost credibility.")
        ),
    }


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: readability.py <url>", file=sys.stderr)
        return 2
    print(json.dumps(analyze(sys.argv[1]), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
