# `llms.txt`, `ai.txt`, and AI-crawler directives

Emerging standards for guiding LLM crawlers. These are not yet universally honored — treat them as directional signal + preparation, not enforcement.

## The three files

| File | Status | What it does |
|------|--------|--------------|
| `/llms.txt` | Proposed (Answer.AI, Sep 2024; growing adoption 2025–2026) | Curated, LLM-optimized navigation of your best content for AI to ingest |
| `/llms-full.txt` | Proposed companion | Full-content dump optimized for LLM ingestion (flat, chunkable) |
| `/ai.txt` | Spawning (Spawning.ai) | Opt-out signal for AI training data scraping — legal/policy layer |

## `/llms.txt` — the AI sitemap

Think of it like `sitemap.xml` but written *for* AI consumption. A single markdown file with curated links to the most important, authoritative content, in a structure an LLM can parse.

Structure (per the draft spec):

```markdown
# Your Project Name

> One-sentence description optimized for LLM context.

Optional paragraph of context the LLM should know before consuming deep links.

## Core documentation

- [Getting started](https://example.com/docs/getting-started.md): What it does and the 5-minute path.
- [API reference](https://example.com/docs/api.md): Full endpoints with examples.
- [Pricing](https://example.com/pricing.md): Plan tiers, per-seat pricing, enterprise.

## Optional

- [Blog](https://example.com/blog/): Long-form content, less canonical.
- [Changelog](https://example.com/changelog.md): Version history.
```

Best practices:
- Link to `.md` versions of pages where possible (LLMs prefer clean markdown to scraping HTML)
- Put the most authoritative / up-to-date content first
- Keep the top-level file under ~5KB; use `llms-full.txt` for longer dumps
- Update whenever major pages change

## `/llms-full.txt` — the ingestion dump

A single flat file concatenating all your core content in markdown, ready to be fed into a model's context window.

Pattern:

```markdown
# example.com — full content dump

## /docs/getting-started

[markdown body of the page]

---

## /docs/api

[markdown body]

---

## /pricing

[markdown body]
```

This is what Mintlify, Anthropic docs, and others already ship. It makes the cost of *"hey LLM, read my docs"* effectively zero.

## `/ai.txt` — training opt-out

A robots.txt-shaped file signaling what AI training scrapers can ingest. Spec from Spawning.ai.

```
# /ai.txt
User-Agent: *
Disallow: /
```

Or to allow only specific crawlers:

```
User-Agent: *
Disallow: /

User-Agent: ChatGPT-User
Allow: /
```

Honored by: some responsible AI crawlers (OpenAI respects `User-Agent` rules); ignored by: many scrapers. Treat it as policy-layer signal rather than enforcement.

## AI-crawler directives in `/robots.txt`

Several AI crawlers publish their user-agent strings. Add explicit directives for the ones you care about.

```text
# /robots.txt

# --- OpenAI ---
User-agent: GPTBot
Allow: /                     # for training data ingestion
Disallow: /private/
Disallow: /admin/

User-agent: ChatGPT-User     # real-time browsing when user asks ChatGPT
Allow: /

User-agent: OAI-SearchBot    # ChatGPT search indexing
Allow: /

# --- Anthropic ---
User-agent: ClaudeBot        # general-purpose crawler
Allow: /
User-agent: Claude-Web       # Claude web browsing
Allow: /
User-agent: anthropic-ai     # training data
Allow: /

# --- Google ---
User-agent: Google-Extended  # controls Bard / Gemini training separately from Googlebot
Allow: /

# --- Perplexity ---
User-agent: PerplexityBot
Allow: /

# --- Meta ---
User-agent: Meta-ExternalAgent
Allow: /

# --- Apple ---
User-agent: Applebot-Extended
Allow: /

# --- Bytedance ---
User-agent: Bytespider
Disallow: /                  # frequently blocked; aggressive crawler

# --- Common Crawl (used by many LLMs indirectly) ---
User-agent: CCBot
Allow: /
```

**Posture decisions:**
- If you want to be *cited* by AI → allow all of the above
- If you're selling content / have paywall → disallow training bots, allow search/browse bots (e.g. allow `ChatGPT-User` + `Claude-Web` but disallow `GPTBot` + `ClaudeBot` + `anthropic-ai`)
- If you're strictly defensive → disallow all AI crawlers; recognize you won't be cited

## Cloudflare AI-crawler controls

If you use Cloudflare, you get a supplementary UI for AI bot management:

- **AI Audit** (bot traffic dashboard) — see which AI crawlers are hitting you
- **AI Scraping & Crawlers** rule — block/challenge AI bots at the edge regardless of `robots.txt` compliance
- **Pay-per-crawl** (beta) — monetize AI access

Cloudflare publishes the definitive AI-bot user-agent list at `https://developers.cloudflare.com/radar/investigate/ai-insights/` — check it quarterly for new bots.

## Audit your current posture

```bash
# Check your live robots.txt for AI crawler coverage
curl -s https://example.com/robots.txt | grep -iE "gpt|claude|anthropic|perplexity|bytespider|google-extended|applebot-extended|ccbot|ai"

# Check for llms.txt
curl -I https://example.com/llms.txt
curl -I https://example.com/llms-full.txt
curl -I https://example.com/ai.txt
```

If these all 404, you have no AI-crawler posture at all. That's the default state of ~95% of the web in 2026.

## Recommended 2026 default posture

For most SaaS / content sites that want to be cited by AI:

1. Ship `/llms.txt` with the 5–15 most important links
2. Ship `/llms-full.txt` with full content dump of core pages
3. Add explicit `Allow` for `GPTBot`, `ClaudeBot`, `PerplexityBot`, `Google-Extended` in `robots.txt`
4. Block `Bytespider` (aggressive, low-value)
5. Skip `ai.txt` unless you have a specific legal posture
6. Monitor via Cloudflare / server logs for new AI bots quarterly

## References

- `https://llmstxt.org` — Answer.AI's draft spec
- `https://spawning.ai/ai-txt` — ai.txt spec
- OpenAI crawler docs: `https://platform.openai.com/docs/bots`
- Anthropic crawler docs: `https://support.anthropic.com/en/articles/8896518`
- Google Extended: `https://blog.google/technology/ai/an-update-on-web-publisher-controls/`
