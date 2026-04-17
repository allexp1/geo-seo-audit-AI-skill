---
name: geo
description: Audit a website for both traditional SEO (titles, meta, headings, Open Graph, Twitter, viewport, sitemap, HTTPS, security headers, response time, compression) and Generative Engine Optimization (citability scoring for ChatGPT/Claude/Perplexity/Google AI Overviews, AI crawler access, JSON-LD schema, llms.txt). Outputs a single markdown report with separate GEO and SEO scores plus a composite. Trigger when the user asks to audit a site for SEO, GEO, AI search visibility, llms.txt, AI crawler access, citability, technical SEO, on-page SEO, sitemap, Open Graph, or schema markup.
user-invocable: true
args:
  - name: subcommand
    description: One of audit, crawlers, citability, schema, llmstxt, onpage, technical, report. Defaults to audit.
    required: false
  - name: url
    description: The URL to analyze (https://example.com)
    required: true
---

# GEO Skill

Audits a website for AI-search visibility plus the traditional SEO signals that still matter. Outputs a prioritized markdown report.

## Subcommands

| Subcommand | What it does |
|---|---|
| `audit` / `report` (default) | Run **all** checks and produce the full markdown report (GEO + SEO scores, breakdowns, two prioritized action lists) |
| `onpage` | On-page SEO only: title/meta length, headings, Open Graph, Twitter, viewport, lang, charset, alt coverage, links, word count |
| `technical` | Technical SEO only: HTTPS upgrade, security headers, compression, response time, sitemap.xml, caching headers |
| `crawlers` | Robots.txt analysis for ~22 known AI crawlers |
| `citability` | Score on-page passages for AI citation readiness |
| `schema` | Detect and validate JSON-LD blocks |
| `llmstxt` | Check for `/llms.txt`; if missing, suggest a template |
| `keywords` | Extract target keywords + check Google rankings (via SerpAPI if key set, else DuckDuckGo) |
| `readability` | Flesch-Kincaid, Gunning Fog, AI citation readability |
| `performance` | Google Lighthouse score + Core Web Vitals via PageSpeed Insights |
| `pdf` | Generate a professional PDF audit report with score gauges, competitive analysis, strategic roadmap, and 90-day timeline. Accepts `--keywords kw1,kw2,...` for custom keyword targeting |

## How to run

All scripts live in `scripts/` next to this file. They take a URL and print JSON to stdout. From this skill's directory:

```bash
python3 scripts/fetch_page.py <url>
python3 scripts/onpage_seo.py <url>
python3 scripts/technical_seo.py <url>
python3 scripts/crawler_check.py <url>
python3 scripts/citability.py <url>
python3 scripts/schema_extract.py <url>
python3 scripts/llmstxt.py <url>
python3 scripts/keyword_extract.py <url>
python3 scripts/keyword_rank.py <domain> <kw1> [kw2 ...]
python3 scripts/readability.py <url>
python3 scripts/performance.py <url> [mobile|desktop]
python3 scripts/report.py <url>     # runs all of the above and emits markdown
python3 scripts/generate_pdf.py <url> [output.pdf] [--keywords kw1,kw2,kw3]
```

## PDF generation

For the `pdf` subcommand, run `generate_pdf.py`. It produces a multi-page professional PDF:
- Score gauges (Composite, GEO, SEO, Lighthouse)
- Full breakdowns with auto-wrapping tables
- Keywords + Google rankings (via SerpAPI or DuckDuckGo)
- Competitive analysis: who ranks for each keyword, what they do right, how to outrank
- Strategic roadmap: keyword opportunity matrix, 3-tier content strategy, GEO strategy
- 90-day action timeline

Custom keywords override auto-extraction. Pass them comma-separated:
```bash
python3 scripts/generate_pdf.py https://example.com report.pdf --keywords "wholesale SIP trunking,DID number provider,virtual numbers API"
```

## Environment variables

| Variable | Purpose |
|---|---|
| `SERPAPI_KEY` | Real Google rankings (free 100/month at serpapi.com) |
| `GOOGLE_CSE_KEY` + `GOOGLE_CSE_CX` | Google Custom Search API (free 100/day) |
| `PAGESPEED_API_KEY` | Higher PageSpeed Insights rate limits |

## Workflow

1. Resolve the skill directory: `SKILL_DIR="$(dirname "$(realpath SKILL.md)")"` — or just `cd` to where this file lives.
2. Run the subcommand. For `audit` / `report`, run `report.py` which orchestrates the others.
3. Present the markdown output to the user. If individual sub-scores look concerning, suggest concrete fixes (the report already includes a prioritized action list, but tailor it to what you saw).

## When to suggest schema templates

If `schema_extract.py` reports missing common types (Organization, LocalBusiness, Article), point the user at the matching file in `schema/` and tell them to fill in the placeholder fields.

## Scope and limits

- Static HTML only. JavaScript-rendered content is invisible without a headless browser.
- Brand-mention scanning across YouTube/Reddit/Wikipedia is **not** included — those need API keys and careful rate limiting. Add it later if needed.
- Citability scoring is heuristic, not an industry standard. It rewards passages that are 100–200 words, self-contained, and fact-rich, because those characteristics correlate with the snippets AI assistants quote. Treat scores as directional.

## What this skill does not do

- No CRM/prospect tracking. No proposal generation. No PDF reports. Add separately if you want them.
- No data is written outside this skill directory. Scripts only read.
