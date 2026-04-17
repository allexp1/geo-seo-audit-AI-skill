# geo-seo-audit

A Claude Code skill that audits any website for **SEO** (traditional search) and **GEO** (AI search — ChatGPT, Perplexity, Claude, Google AI Overviews). Outputs markdown reports or professional PDF reports with competitive analysis, keyword rankings, and a 90-day action plan.

---

## What it does

| Command | Output |
|---|---|
| `/geo audit <url>` | Full markdown report — GEO + SEO scores, breakdowns, keyword rankings, readability, two prioritized action lists |
| `/geo pdf <url> --keywords kw1,kw2` | Professional multi-page PDF with score gauges, competitive analysis, strategic roadmap, 90-day timeline |
| `/geo onpage <url>` | On-page SEO: title/meta length, headings, Open Graph, Twitter Card, viewport, lang, charset, alt coverage, link counts, word count |
| `/geo technical <url>` | Technical SEO: HTTPS, 6 security headers, compression, response time, sitemap.xml, caching |
| `/geo crawlers <url>` | Robots.txt status for 22 known AI crawlers |
| `/geo citability <url>` | Per-passage citation-readiness scoring for AI search |
| `/geo schema <url>` | JSON-LD detection + field completeness check |
| `/geo llmstxt <url>` | Check `/llms.txt` or generate a starter template |
| `/geo keywords <url>` | Extract keywords + check Google rankings |
| `/geo readability <url>` | Flesch-Kincaid, Gunning Fog, AI citation readability |
| `/geo performance <url>` | Lighthouse score + Core Web Vitals via PageSpeed Insights |

---

## Install

### 1. Clone the repo

```bash
git clone https://github.com/allexp1/geo-seo-audit.git
cd geo-seo-audit
```

### 2. Run the installer

```bash
./install.sh
```

This installs two skills:

- `~/.claude/skills/geo/` — this skill (SKILL.md + scripts/ + schema/)
- `~/.claude/skills/business-idea-validator/` — companion skill from [business-idea-validator-AI-skill](https://github.com/allexp1/business-idea-validator-AI-skill), cloned and installed automatically

After restart you'll have both `/geo` and `/business-idea-validator` available.

### 3. Install Python dependencies

```bash
python3 -m pip install -r requirements.txt
```

Or with a venv:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 4. Restart Claude Code

The skill is loaded on startup. After restarting, try:

```
/geo audit https://example.com
```

---

## API Keys (optional but recommended)

Set these in your `~/.zshrc` (or `~/.bashrc`):

| Variable | Purpose | How to get |
|---|---|---|
| `SERPAPI_KEY` | Real Google keyword rankings | Free 100/month at [serpapi.com](https://serpapi.com) |
| `GOOGLE_CSE_KEY` + `GOOGLE_CSE_CX` | Google Custom Search API | Free 100/day via [Google Cloud Console](https://console.cloud.google.com) |
| `PAGESPEED_API_KEY` | Higher PageSpeed Insights limits | Free at [Google Cloud Console](https://console.cloud.google.com) |

Without any keys, keyword rankings fall back to DuckDuckGo (still useful, just not Google).

```bash
# Add to ~/.zshrc
export SERPAPI_KEY="your-key-here"
```

---

## PDF Reports

Generate professional PDF audit reports with competitive analysis:

```bash
# Auto-extract keywords from the page
python3 scripts/generate_pdf.py https://example.com report.pdf

# Target specific keywords
python3 scripts/generate_pdf.py https://example.com report.pdf \
  --keywords "wholesale SIP trunking,virtual phone numbers,DID provider"
```

The PDF includes:
- Score gauges (Composite, GEO, SEO, Lighthouse)
- Full on-page and technical SEO details
- Keyword extraction + Google rankings
- Competitive analysis per keyword: who ranks #1-3, what they do right, how to outrank them
- Keyword opportunity matrix (difficulty + recommended action)
- 3-tier content strategy (quick wins / new pages / long-term investment)
- GEO strategy for AI citations
- 90-day action timeline

---

## Use scripts standalone (no Claude needed)

Every script is self-contained — takes a URL, prints JSON (or markdown for `report.py`):

```bash
python3 scripts/report.py https://example.com > report.md
python3 scripts/crawler_check.py https://example.com | jq
python3 scripts/citability.py https://example.com | jq
python3 scripts/keyword_extract.py https://example.com | jq
python3 scripts/keyword_rank.py example.com "keyword one" "keyword two" | jq
python3 scripts/keyword_rank.py example.com --from-extract https://example.com | jq
python3 scripts/readability.py https://example.com | jq
python3 scripts/onpage_seo.py https://example.com | jq
python3 scripts/technical_seo.py https://example.com | jq
python3 scripts/performance.py https://example.com mobile | jq
```

---

## Layout

```
geo-seo-audit/
├── SKILL.md                # Claude Code skill definition
├── install.sh              # plain cp into ~/.claude/skills/geo
├── requirements.txt        # requests, beautifulsoup4, ddgs, google-search-results, reportlab
├── scripts/
│   ├── fetch_page.py       # HTML + metadata fetcher
│   ├── onpage_seo.py       # title, meta, OG, Twitter, viewport, alts, links
│   ├── technical_seo.py    # HTTPS, security headers, sitemap, response time
│   ├── crawler_check.py    # robots.txt vs 22 known AI bots
│   ├── citability.py       # passage scoring for AI citation readiness
│   ├── schema_extract.py   # JSON-LD detection + field check
│   ├── llmstxt.py          # /llms.txt check + template generator
│   ├── keyword_extract.py  # keyword extraction (freq + position weighting)
│   ├── keyword_rank.py     # Google rankings (SerpAPI / CSE / DuckDuckGo)
│   ├── readability.py      # Flesch-Kincaid, Gunning Fog, AI readability
│   ├── performance.py      # Lighthouse + Core Web Vitals via PageSpeed Insights
│   ├── report.py           # orchestrator → full markdown report
│   └── generate_pdf.py     # professional PDF report with competitive analysis
└── schema/                 # JSON-LD templates to copy and fill in
    ├── organization.json
    ├── website.json
    ├── article.json
    ├── faq.json
    └── local-business.json
```

---

## Scoring

Two independent scores plus a composite (their average).

**GEO Score (0-100) — AI search readiness:**

| Category | Weight | What it measures |
|---|---|---|
| AI Crawler Access | 35% | Of 22 known AI bots, what fraction are not blocked at root |
| Citability | 35% | Avg passage score (length, self-containment, fact density, answer phrasing) |
| Schema Coverage | 20% | JSON-LD presence + how many high-value types appear |
| llms.txt | 10% | Present and well-formed |

**SEO Score (0-100) — traditional search:**

| Category | Weight | What it measures |
|---|---|---|
| On-Page SEO | 50% | Title, meta, H1, canonical, OG, Twitter, viewport, lang, charset, alt, links |
| Technical SEO | 50% | HTTPS, security headers, compression, speed, sitemap, caching |

**Additional sections (shown but not in composite):**

| Section | Source |
|---|---|
| Keywords + Rankings | Google (SerpAPI) or DuckDuckGo |
| Readability | Flesch-Kincaid, Gunning Fog |
| Performance | Google PageSpeed Insights |
| Competitive Analysis | SerpAPI top 3 per keyword |

---

## What this skill deliberately leaves out

- No `curl | bash` installer — just a plain `cp` script you can read in 10 seconds.
- No CRM, prospect tracking, or persistent data outside the skill folder.
- No paid-community funnel.
- No brand-mention scanning (needs API keys and rate limiting — add separately if needed).
- Scripts only read, never write outside their own output.

---

## Limits

- **Static HTML only.** JS-rendered pages look thin to citability and schema checks.
- **No authentication.** Pages behind login walls return the public version.
- **Heuristic scoring.** Citability is a proxy, not a measurement of actual AI citations.
- **DuckDuckGo != Google.** Without SerpAPI, keyword rankings are directional.
- **PageSpeed Insights** has a daily free quota. Set `PAGESPEED_API_KEY` if you hit 429s.

---

## Uninstall

```bash
rm -rf ~/.claude/skills/geo
rm -rf ~/.claude/skills/business-idea-validator   # if you no longer want the companion
```

That's it. Nothing else was created.

---

## Requirements

- Python 3.8+
- Claude Code CLI
- Git

---

## License

MIT
