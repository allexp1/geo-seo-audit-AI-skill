# Link Building and Digital PR

Off-page SEO — the ~40% of ranking weight that lives outside your site. Authoritative backlinks remain the single strongest ranking signal in 2026, and they're nearly as important for AEO (AI engines cite sites they've seen cited elsewhere).

## The principle

Google measures "authority" largely by who links to you. Not "SEO tools telling you Domain Authority 72" — actual editorial links from sites that independently decided you were worth citing. One link from The New York Times or a top-tier industry publication is worth ~1,000 links from directory farms.

## What earns links vs. what wastes time

### Works

1. **Original research / data reports** — "State of X 2026," with downloadable CSVs, drives citations for years
2. **Free tools** — calculators, generators, comparisons that people reference
3. **Expert commentary** — being quotable in journalism (HARO, Qwoted, Connectively)
4. **Newsworthy product launches** — genuinely new, verifiable claims get covered
5. **Controversial / contrarian take pieces** — if grounded in data, earn links via debate
6. **Industry benchmarks** — "we surveyed 500 companies" > "we surveyed 25"
7. **Interactive content** — configurators, quizzes, visualizations get embedded

### Doesn't work anymore

- Guest posts on DA-20 blogs (dilutive; often manual action risk)
- Link directories (decades-dead; penalty risk on paid ones)
- Comment spam
- "Skyscraper" content that's just longer versions of competitors (over-indexed tactic)
- Buying links (manual actions, page-level penalties)
- PBNs (private blog networks; detected + penalized)
- Reciprocal link schemes
- Infographic submission sites (died ~2018)

## The 4 link-building motions

### 1. Digital PR — the long game

Hiring a PR agency or in-house comms person specifically for SEO-relevant earned media. Target publications:

**Tier 1:** NYT, WSJ, Bloomberg, TechCrunch, The Information, Reuters, FT
**Tier 2:** Industry trades (TechRadar, Wired, Fast Company, HBR, category-specific)
**Tier 3:** Mid-tier industry blogs with real editorial

**Tactics:**
- Original research with press release
- Newsworthy product launch
- Expert commentary on current events (HARO / Qwoted / Muck Rack responses)
- Speaker placements at industry conferences (bio often linked)

**Realistic output:** 2-5 Tier 1 mentions / year, 10-20 Tier 2. That's a huge success.

### 2. Link reclamation — the quick wins

Find brand mentions that should link to you but don't, and ask.

```bash
# Find unlinked brand mentions using Google
# (automatable with Ahrefs Content Explorer or similar)
site:*.com "YourBrand" -site:yourbrand.com -site:linkedin.com -site:crunchbase.com
```

For each:
1. Identify it's your actual brand being discussed
2. Find the author's email (Hunter.io, ContactOut)
3. Short polite email: "Hey, you mentioned [Brand] in [article] — we actually have a reference page at [URL] that might be useful for your readers"
4. 10-20% conversion rate with good emails

Also works for:
- Broken-link reclamation: find dead competitor URLs that used to earn links, create replacement content, email the linker
- Image reclamation: find unlinked uses of your images

### 3. Partnerships, integrations, listings

Links from authoritative sources who organically need to reference you:

- **SaaS integration partners** — "Integrations" pages linking bidirectionally (Zapier, n8n, Notion, Slack)
- **Standards bodies** — W3C, ISO, industry associations
- **Educational institutions** — university course syllabi, research citations
- **Government / NGO references** — regulatory filings, policy discussions
- **Open-source contributions** — project README links, docs

These tend to be persistent ("sticky") links that stay live for years.

### 4. Original content that gets cited

Build a small number of "linkable assets" that keep earning links passively:

**Characteristics of a linkable asset:**
- Original data, survey, or benchmark (not opinion)
- Single topic, narrow and deep
- Unique visualizations / chart-worthy numbers
- Updated annually (earns links from each year's "2026 State of X" references)
- Shareable standalone URL
- Schema: `Article` + `Dataset` if applicable

Examples that work: "State of JavaScript 2025," "State of AI 2025," "Distributed Workforce Benchmark 2025," "CMS Market Share Report 2025."

## Link quality heuristics

Before chasing a link, evaluate the source:

| Signal | Strong | Weak |
|--------|--------|------|
| Domain age | 10+ years | <2 years |
| Real editorial team | Named authors, bios | "Guest contributors" |
| Traffic | Ahrefs / Semrush shows real organic | Nothing |
| Topical relevance | Same industry or adjacent | Off-topic |
| Link placement | Body, prose | Footer, sidebar, "sponsors" |
| Outbound link count | <10 per page | >30 per page |
| Follow status | `dofollow` | `nofollow` (still has value for AEO) |

**Nofollow links still matter for AEO.** LLMs don't parse HTML rel attributes when deciding who to cite. A nofollow mention in The New York Times is still valuable for AI citation.

## Outreach — templates and patterns

**Cold outreach conversion rates (2026):** 1-5% for good emails. Don't scale bad outreach — it's counterproductive.

**Good outreach email structure:**

```
Subject: [Specific context — NOT "Link exchange" or "Collaboration opportunity"]

Hi [first name],

Read your piece on [specific article title + publication] — the point
about [specific claim they made] matched what we saw in our [specific data].

We just published [specific asset] that covers [the exact gap in their
article]. It includes [1-2 specific numbers/findings].

Worth mentioning in a future piece? Happy to share the underlying data
if useful.

[Your name]
[Signature with one link to the asset]
```

**Avoid:**
- Any form of "Dear sir/madam"
- Attached docs (spam-looking)
- Mass-merge templates obvious from variable mistakes
- Multiple follow-ups (1 polite follow-up max after 7 days)
- Reciprocal link asks

## The HARO / Qwoted / Connectively loop

Journalists request expert sources. Respond with pull-quote-ready answers and a link often follows.

Daily cadence:
1. 7am — scan the day's requests (2-5 minutes)
2. Respond to 1-3 where you have genuine expertise
3. Keep response under 150 words
4. Include a crisp 1-2-sentence pull quote
5. Bio with site link at the end

Conversion rate: 10-20% of responses get used; ~50% of uses include a link. So ~15 responses/week → 1-3 mentions/month → ~1-2 links/month. Compounds over years.

## Link building for AEO specifically

AI engines don't just weight backlinks — they weight *mentions* (linked or not). Focus on:

- **Authority-domain citations** (mentioned by NYT, Wikipedia, academic papers)
- **Knowledge-graph presence** (see `references/knowledge-graph.md`)
- **Listicle inclusion** (being in "10 best X" articles across many sites)
- **Reddit / Hacker News / Stack Exchange** mentions (AI crawlers index these)

An AI-visibility-optimized link campaign would prioritize:
1. Wikipedia / Wikidata editorial inclusion (zero dollars, high AEO impact)
2. Industry listicle placements (fastest citation-rate move)
3. HARO / Qwoted bylines (compound over years)
4. Digital PR (Tier 1/2 mentions)

Deprioritize:
- Guest posts on small blogs (marginal SEO value, negligible AEO value)
- Paid "sponsored content" with rel=sponsored (Google ignores for ranking; AI ignores for citation)

## Common pitfalls

- Chasing quantity over quality → dilution + manual action risk
- Buying links → ranking penalties
- Guest posting at scale → manual actions
- Ignoring nofollow → missing ~half the AEO value of placed mentions
- Creating "linkable assets" nobody would link to (self-assessed)
- No outreach follow-through → content dies un-distributed
- Not measuring → no idea which motions produce results

## Measurement

Monthly dashboard:

- **Referring domains** — Ahrefs / Semrush; the core authority metric
- **New referring domains last 30 days** — acquisition rate
- **Lost referring domains** — decay rate
- **Referring domain authority distribution** — high-DR share growing?
- **Anchor text distribution** — natural (mix of brand, URL, keyword) vs. over-optimized
- **Unlinked brand mentions** — reclamation opportunity pool

## Budget reality check

Credible link building in a competitive category in 2026 costs:

| Motion | Monthly cost | Realistic output |
|--------|-------------|------------------|
| In-house PR (FTE) | $8-15K | 2-5 Tier 1, 10-20 Tier 2 per year |
| PR agency retainer | $10-25K | Similar |
| Link reclamation (freelancer) | $2-5K | 5-15 recovered links/month |
| Linkable-asset creation (agency) | $5-15K per asset | 1 asset, ongoing earns |
| HARO specialist (freelancer) | $1-3K | 2-6 placements/month |

Cheap link building doesn't exist for real results. Sub-$1K/month "link building" services typically mean PBN links or guest posts on sites that don't move the needle.

## Audit checklist

- [ ] Current referring-domain count tracked monthly
- [ ] Linkable-asset inventory identified (0-3 for most sites)
- [ ] HARO / Qwoted subscriptions active
- [ ] Link reclamation queue (unlinked mentions) checked quarterly
- [ ] At least one digital-PR motion running (agency or in-house)
- [ ] Wikipedia / Wikidata entry established
- [ ] Industry listicle tracker (10 best X lists we should be in)
- [ ] Integration / partnership page linked reciprocally
- [ ] No paid / bought link dependencies
