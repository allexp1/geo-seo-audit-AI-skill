# GEO Skill v2 — Refactor Design

Date: 2026-07-04
Status: implemented in this branch

## Goal

Update the geo-seo-audit skill to the mid-2026 state of SEO + GEO, add an
**AI Agent Readiness** pillar with owner-facing recommendations in every
report, and integrate **ora.ai** as an external agent-readiness score.

## Approaches considered

1. **Minimal patch** — refresh the bot list, bolt on an ora.ai call.
   Rejected: doesn't deliver the agent-readiness recommendations the user
   asked for, and leaves scoring logic duplicated across two files.
2. **Full rewrite** (plugin architecture, async fetching, shared HTTP cache).
   Rejected: YAGNI; the script-per-check design is a feature (each script is
   standalone and pipeable).
3. **Targeted refactor** (chosen) — keep the script-per-check architecture,
   extract duplicated scoring into a shared `scoring.py`, add two new checks
   (`agent_readiness.py`, `ora_score.py`), refresh every existing check with
   verified 2026 facts, and re-render both reports around three pillars.

## Architecture changes

```
scripts/
├── scoring.py            NEW — single source of truth for all sub-scores +
│                          pillar weights, imported by report.py and generate_pdf.py
├── agent_readiness.py    NEW — static AI-agent readiness checks (see below)
├── ora_score.py          NEW — ora.ai Agent Readiness API client
├── crawler_check.py      UPDATED — 2026 bot roster, bot categories,
│                          Content-Signal parsing, Cloudflare detection,
│                          stale-token flagging, category-aware scoring
├── schema_extract.py     UPDATED — deprecated rich-result flagging,
│                          sameAs/entity-linking emphasis
├── llmstxt.py            UPDATED — llms-full.txt check, honest value caveat
├── onpage_seo.py         UPDATED — 2026 title/meta bands, snippet controls
├── citability.py         UPDATED — answer-first metric, comparison-table bonus
├── technical_seo.py      UPDATED — Cloudflare fingerprint surfaced
├── performance.py        UPDATED — FID marked legacy; thresholds confirmed
├── report.py             UPDATED — 3 pillars + agent action list + ora section
└── generate_pdf.py       UPDATED — same additions in PDF form
```

## Scoring model (v2)

Three pillars, composite = mean of the three:

| Pillar | Components (weights within pillar) |
|---|---|
| **GEO** (AI search visibility) | Crawler access 30% (category-aware), Citability 30%, Schema 20%, llms.txt 10%, Answer-first structure 10% |
| **SEO** (traditional) | On-page 50%, Technical 50% (unchanged) |
| **AGENT** (AI-agent usability, NEW) | Content parseability 35%, Interaction readiness 25%, Agent interfaces 25%, Access/bot-walls 15% |

The **ora.ai score is displayed alongside** as external validation, not
folded into the composite (it may be missing for unscanned domains and its
scale/weights are ora's own).

### Crawler scoring becomes category-aware

Blocking a **search-index or user-fetch bot** (OAI-SearchBot, Claude-SearchBot,
PerplexityBot, ChatGPT-User…) removes the site from AI answers → heavy penalty.
Blocking a **training bot** (GPTBot, ClaudeBot, CCBot…) is a legitimate policy
choice → reported, tiny penalty only. Blocking Googlebot/Bingbot also kills AI
Overviews/Copilot → explicit P1 warning.

## agent_readiness.py checks (all static-HTML/HTTP)

Mirrors Lighthouse 13.3 "Agentic Browsing" (May 2026), Cloudflare's Agent
Readiness Score dimensions, and ora.ai's Identity/Access layers:

1. **Content parseability** — meaningful text in raw HTML (SSR), text-to-markup
   ratio, semantic landmarks (`main/nav/header/footer/article`), heading
   hierarchy (one H1, no skipped levels).
2. **Interaction readiness** — form inputs with `<label for>`/`aria-label`,
   buttons/links with accessible names, no div-soup click targets
   (`div onclick` without role), WebMCP hints (`navigator.modelContext`).
3. **Agent interfaces** — `/llms.txt`, `/llms-full.txt`,
   `/.well-known/mcp.json`, `/.well-known/api-catalog` (RFC 9727),
   `/.well-known/http-message-signatures-directory` (Web Bot Auth),
   `/openapi.json` (+`/api/openapi.json`), NLWeb `/ask`+`/mcp`, markdown
   content negotiation (`Accept: text/markdown`).
4. **Access** — bot-wall detection: fetch with a browser UA vs `GPTBot` UA and
   compare status/challenge markers (Cloudflare "Just a moment", cf-mitigated).
5. **Snippet controls** — `nosnippet`/`max-snippet`/`data-nosnippet` reported
   (they limit AI Overview usage of the page).

Output includes a prioritized `recommendations` list — this feeds the new
**"Make this site better for AI agents"** section in both reports.

## ora.ai integration

- `GET https://ora.ai/api/score/{domain}` — free, keyless, ~10 req/min/IP.
- On 404 (never scanned) the script does **not** auto-scan: a fresh
  `POST /api/scan` publishes the domain on ora's public leaderboard, so
  scanning is opt-in via `--scan`.
- Report renders: score/grade, 5-layer breakdown, top recommendations sorted
  by `estScoreGain`, link to the full ora report.

## Facts encoded (verified 2026-07-04)

- Core Web Vitals thresholds unchanged: LCP ≤2.5s, INP ≤200ms, CLS ≤0.1.
  (Claims of 2026 threshold changes are content-farm fabrications.)
- FAQ rich results removed May 2026; HowTo dead since 2023; June 2025 retired:
  Book Actions, Course Info, Claim Review, Estimated Salary, Learning Video,
  Special Announcement, Vehicle Listing. FAQPage markup still aids AI parsing.
- llms.txt: not consumed by Google Search; IS checked by Lighthouse Agentic
  Browsing and consumed by coding agents. Low-weight agent signal, say so.
- Retired robots tokens: `anthropic-ai`, `claude-web`, `FacebookBot` → flag as
  stale if present in robots.txt.
- New bots: `OAI-AdsBot`, `Claude-SearchBot`, `Meta-ExternalFetcher`,
  `DuckAssistBot`, `MistralAI-User`, `Google-CloudVertexBot`.
- Cloudflare blocks AI training crawlers by default since July 2025; from
  2026-09-15 blocks mixed-use crawlers on ad-monetized pages by default.
  `Content-Signal:` lines in robots.txt (search / ai-input / ai-train).
- 44% of LLM citations come from the first 30% of page content → answer-first
  check. Google-Extended does NOT control AI Overviews; snippet controls do.

## Addendum: self-updating knowledge layer

After the v2 implementation, the skill was retrofitted with the skill-evolver
architecture: time-sensitive facts moved from SKILL.md into `KNOWLEDGE.md`
(`last_updated` / `review_interval_days: 14` frontmatter), trusted refresh
sources in `sources.md` (PRIMARY/SECONDARY tiers), and an audit log in
`CHANGELOG.md`. SKILL.md gained a staleness gate (checked every invocation)
and a Refresh Protocol that may modify only KNOWLEDGE.md and CHANGELOG.md —
never SKILL.md, sources.md, or scripts. Facts that surface in script constants
are mapped in KNOWLEDGE.md → "Where facts live in code"; refreshes propose
those code changes to the user instead of applying them. `install.sh` seeds
the knowledge files on first install but never clobbers a refreshed copy.

## Out of scope (unchanged limits)

- No headless browser; JS-rendered content remains invisible (reported as such).
- No brand-mention / share-of-voice tracking (Profound/Otterly territory —
  ora.ai's Discovery layer partially covers it externally).
- No CRM, no writes outside the skill directory.
