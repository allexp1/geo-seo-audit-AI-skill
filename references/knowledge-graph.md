# Knowledge Graph + Entity Optimization

The single most underleveraged AEO action for B2B and public-facing brands. AI engines heavily cite Wikipedia, Wikidata, Crunchbase, LinkedIn Company Pages, and OpenAlex — the "knowledge graph" layer of the web. If your entity doesn't exist in these sources, or exists with stale / wrong information, AI will either not cite you, cite competitors instead, or cite you with bad facts.

## The entity-first mental model

Old SEO: optimize a *page* for a *keyword*.
Entity SEO: optimize an *entity* across the web so search + AI understand who you are.

Google and LLMs both think in entities, not keywords. "DIDWW" is an entity — a company. The entity has attributes (founded 2004, Dublin, CEO Karolis Jurys, SIP trunking, 29 countries licensed). Those attributes need to be consistent and machine-readable everywhere your entity appears.

## The knowledge graph pyramid

From highest to lowest authority for AI citation:

```
┌────────────────────────────────────────┐
│ Wikipedia (English + relevant langs)   │  ← highest, hardest to get
├────────────────────────────────────────┤
│ Wikidata (structured data behind Wiki) │  ← highest, easier than Wiki
├────────────────────────────────────────┤
│ Crunchbase (companies + people)        │  ← high for B2B
├────────────────────────────────────────┤
│ LinkedIn Company / personal            │  ← high, easy to claim
├────────────────────────────────────────┤
│ Industry-specific databases            │  ← category-dependent
├────────────────────────────────────────┤
│ Google Business Profile                │  ← local businesses
├────────────────────────────────────────┤
│ Your own structured data (schema.org)  │  ← lowest authority (self-reported)
└────────────────────────────────────────┘
```

AI engines cross-check facts across the stack. If your Wikipedia says you were founded in 2004, Wikidata says 2004, Crunchbase says 2004, LinkedIn says 2004, and your own site says 2004 — AI confidently cites "founded 2004." If one says 2002 and four say 2004, AI either picks 2004, omits the fact, or cites the contradiction.

## Wikidata — the quickest real win

Wikidata is structured data. Editing is dramatically easier than Wikipedia. And every entity on Wikipedia is backed by a Wikidata item.

### Check if you have an entry

1. Go to `https://www.wikidata.org`
2. Search for your brand
3. If an item exists, note the Q-number (e.g., `Q12345`)

### Create or update

Required properties for a company:

| Property | Example | Why AI cares |
|----------|---------|--------------|
| `instance of` (P31) | business, software company | Category placement |
| `inception` (P571) | 2004 | Founding year fact |
| `country` (P17) | Ireland | Geographic fact |
| `headquarters location` (P159) | Dublin | Specific location |
| `founded by` (P112) | [founder names] | Attribution |
| `industry` (P452) | telecommunications | Category |
| `official website` (P856) | https://didww.com | Canonical URL link |
| `CEO` (P169) | [current CEO] | Leadership fact |
| `subsidiary` / `parent organization` | [relationships] | Entity graph |
| `NAICS code` / `ISIC code` | [codes] | Formal classification |
| `official name` (P1448) | [legal entity name] | Name disambiguation |

Wikidata requires **references**. Every fact must cite a reliable source (company about page, press release, SEC filing). Citations from the company's own site are fine for basic facts (founding year, CEO); third-party sources are required for more sensitive facts.

### The Wikidata → Wikipedia pipeline

Wikidata is the substrate; Wikipedia is the article layer. You cannot just "create your own Wikipedia article" — notability rules require third-party coverage. But you can:

1. Build out your Wikidata entry rigorously
2. Earn credible press coverage over time (TechCrunch, industry publications)
3. A neutral editor (not you) eventually writes a Wikipedia stub
4. You cannot edit your own Wikipedia article (conflict of interest), but you can correct factual errors via the article's talk page

## Crunchbase

For B2B / startups, Crunchbase is nearly as important as Wikipedia for AI citation.

**Action list:**

1. Claim your company profile at `crunchbase.com`
2. Pay for Crunchbase Pro (~$49/mo) if you want to edit aggressively; free tier has limits
3. Fill every field: founding date, HQ, description, logo, employee count, funding rounds, investors, founders
4. Keep it current — every funding round, acquisition, product launch gets added
5. Link to your LinkedIn, Twitter, website consistently

## LinkedIn Company Page

Effectively free and essential for B2B AEO.

**Key fields AI reads:**
- Tagline (should match your homepage meta description tone)
- About section (keyword-rich but natural — 150–2000 characters; AI favors first 200)
- Founded year
- Industry + specialties (pick 5-10 specific)
- Headquarters
- Website link
- Employee count — even rough range affects credibility

**Posting cadence matters for AEO** — LLMs weight recent activity. 2-4 posts/week > dormant page. Posts should reference your brand name + industry naturally.

## Google Knowledge Panel

When your entity has enough authority, Google surfaces a Knowledge Panel on branded searches (right side desktop, top mobile). This panel is pulled from the above sources + Google's own crawl.

**How to get a Knowledge Panel:**

1. Have a Wikipedia or Wikidata entry (usually requisite)
2. Have consistent entity information across the pyramid
3. Optionally: apply via Google Knowledge Graph Search API (enterprise-only in practice)

**How to claim and edit an existing Knowledge Panel:**

1. Search your brand on Google
2. Scroll down the panel → "Claim this knowledge panel"
3. Verify via Search Console or your official social
4. Once verified, you can suggest edits to the panel

## `sameAs` — your entity's rosetta stone

Add a comprehensive `sameAs` array to your `Organization` schema. This is the single cheapest entity-disambiguation signal you can ship.

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "@id": "https://example.com/#organization",
  "name": "Example Corp",
  "url": "https://example.com",
  "logo": "https://example.com/logo.png",
  "sameAs": [
    "https://en.wikipedia.org/wiki/Example_Corp",
    "https://www.wikidata.org/wiki/Q12345",
    "https://www.crunchbase.com/organization/example-corp",
    "https://www.linkedin.com/company/example-corp",
    "https://twitter.com/examplecorp",
    "https://www.facebook.com/examplecorp",
    "https://github.com/examplecorp",
    "https://www.youtube.com/@examplecorp",
    "https://stackoverflow.com/jobs/companies/example-corp"
  ]
}
</script>
```

Each URL in `sameAs` tells search engines and AI: *"the same entity that owns this page also owns those URLs."* That builds the entity graph.

## Personal-brand entity optimization (founders, authors)

Same principles apply to people:

1. Wikidata item for yourself (P31 → human)
2. LinkedIn profile optimized with founded-companies, education, previous roles (each linking to other Wikidata-visible entities)
3. Personal site with `Person` schema
4. Author-schema bylines on every piece of content you write
5. `sameAs` linking LinkedIn, Twitter, GitHub, your personal site, any publications

Founders should have their own entity; AI cites them individually when asked about leadership.

## Auditing your entity presence

### Quick check (15 minutes)

```bash
# 1. Wikidata
open "https://www.wikidata.org/w/index.php?search=YOUR_BRAND"

# 2. Wikipedia
open "https://en.wikipedia.org/wiki/Special:Search?search=YOUR_BRAND"

# 3. Crunchbase
open "https://www.crunchbase.com/search/organization.companies/field/organization_all/title/YOUR_BRAND"

# 4. Google Knowledge Panel
open "https://www.google.com/search?q=YOUR_BRAND"

# 5. Your own schema
curl -s https://YOUR_SITE.com | grep -oE '<script type="application/ld\+json">[^<]*</script>' | head -1

# 6. Test AI citation directly
node scripts/ai-citation-test.mjs --brand=YOUR_BRAND --prompts=brand-test.txt
```

### Thorough audit

Check these specific facts across every knowledge-graph source:

- [ ] Company name (legal + operating)
- [ ] Founding year
- [ ] Headquarters city / country
- [ ] Founder names
- [ ] Current CEO
- [ ] Industry / category
- [ ] Website URL
- [ ] Employee count (or range)
- [ ] Funding raised (if applicable)

If any fact differs across sources, pick the correct one and update everywhere. Pay attention to Wikipedia talk pages — edits get reverted if they look self-serving.

## Why this matters for AI citation specifically

When ChatGPT / Claude / Perplexity / Gemini answer "best SIP trunking provider for voice AI," they don't just search the web. They pull from their pre-training data, which heavily sampled Wikipedia, Wikidata, Crunchbase-style databases, and authority sources. A brand that's invisible in the knowledge graph gets cited approximately never, regardless of how beautiful their website is.

Conversely, a brand with a solid Wikipedia stub + Wikidata entry + Crunchbase profile + LinkedIn + consistent `sameAs` schema gets cited confidently, even before earning a single dollar of paid distribution.

This is the single highest-leverage action for B2B AEO, and most teams skip it because it's tedious and doesn't look like "SEO work."
