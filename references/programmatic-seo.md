# Programmatic SEO

Template-driven pages at scale. The Zillow, Yelp, Airbnb, Booking.com, Wise, and Nomad List playbook. Under the right conditions, programmatic SEO can 10× a site's organic traffic — or get the site penalized for "low-quality pages" if done wrong.

## When programmatic SEO works

Two ingredients must be true:

1. **Search demand is fragmented across many long-tail queries** with similar intent. Examples:
   - `"houses for rent in [city]"` — thousands of cities
   - `"[job title] salary in [city]"` — tens of thousands of combinations
   - `"convert [amount] [currency A] to [currency B]"` — millions
   - `"[BPM] bpm workout music"` — dozens of BPM values × workout types
   - `"makeup artists in [city]"` — thousands of cities × categories

2. **You can generate each page with genuinely useful, differentiated content** — not just swap a city name into a template. The content must answer the query specifically.

If you don't have both, programmatic SEO will either not rank (thin content) or get manually penalized (doorway pages policy).

## The failure mode that kills most attempts

```
❌ 10,000 pages that say:
"Houses for rent in {city}. Find the best houses for rent in {city}.
Our listings for {city} are updated daily. Contact us for houses in {city}."
```

Google calls this "doorway pages" and penalizes it. AI models also don't cite from this kind of content — there's nothing distinctive to extract.

The hard part is having *genuinely useful data per page* — actual listings, actual prices, actual stats. If you don't, programmatic SEO is a trap.

## Patterns that work

### 1. Data-driven reference pages

```
convert/usd-to-eur/
convert/usd-to-gbp/
convert/eur-to-jpy/
...
```

Each page shows:
- Current rate
- Historical chart
- Formula
- Calculator
- Common amounts table

The data comes from a currency API; content templates get populated automatically. Works because every page has *unique factual data*.

Examples in the wild: Wise (currency), NomadList (city stats), SmartAsset (tax calculators), BambooHR (salary data).

### 2. Aggregator / directory pages

```
[category]-in-[city]/
  → "Best dentists in Chicago"
  → "Top marketing agencies in Austin"
  → "Coworking spaces in Lisbon"
```

Each page lists *real businesses with real reviews*, not placeholder copy. The content is unique because it lists different entities per page.

Examples: Yelp, TripAdvisor, Clutch, G2 (by category × city).

### 3. "How to [X] with [tool]" intent

```
how-to/export-data-from-[app-A]/
how-to/migrate-from-[app-A]-to-[app-B]/
```

Works for B2B SaaS where users search for specific integration/migration paths. Pages must contain real step-by-step instructions, not generic template copy.

Examples: Zapier (integration pages), Notion (templates by use case), Fivetran (connector pages).

### 4. Comparison pages

```
[tool-A]-vs-[tool-B]/
[tool-A]-alternatives/
```

Works for categories with active comparison shopping. Content must include real feature comparisons, not just "A has more features than B." Include comparison tables, specific pricing, use-case fit.

Examples: G2, Capterra, Product Hunt (some pages), Capterra.

### 5. Long-tail local service

```
[service]-near-[neighborhood-in-city]/
```

Only works if you have deep local data. Otherwise it's doorway spam. See `local-seo.md`.

## Architecture

### Data layer

Programmatic SEO needs a structured data source:

- Your own database (inventory, listings, users, transactions)
- Public API (currency, weather, population)
- Scraped + verified (sports stats, product catalogs)
- User-generated (reviews, listings, answers)

Each URL maps to a row / query in the data layer. The template is just the presentation.

### URL structure

```
✅ Clean, keyword-rich, hierarchical:
/jobs/[role]/in/[city]/
/compare/[tool-a]-vs/[tool-b]/
/convert/[from-currency]/to/[to-currency]/

❌ Parameter-heavy:
/pages?role=engineer&city=nyc
/compare?a=tool-a&b=tool-b
```

Use path segments, not query parameters. Query-parameter pages rank worse.

### Canonicalization

Every programmatic page must have a self-referencing canonical to avoid duplicate-content penalties:

```html
<link rel="canonical" href="https://example.com/jobs/engineer/in/nyc/">
```

If two paths could render the same content (e.g., `engineer/in/nyc` and `engineer/in/new-york`), pick one as canonical and 301 the other.

### Sitemap

Split sitemaps by category — one sitemap per ~50,000 URLs, linked from a sitemap index:

```xml
<!-- sitemap-index.xml -->
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://example.com/sitemaps/cities.xml</loc></sitemap>
  <sitemap><loc>https://example.com/sitemaps/jobs.xml</loc></sitemap>
  <sitemap><loc>https://example.com/sitemaps/comparisons.xml</loc></sitemap>
</sitemapindex>
```

### Internal linking

Programmatic pages die in isolation. Build internal-linking infrastructure:

- Hub / pillar pages link down to category pages
- Category pages link to their ~20 most-searched children
- Children link to siblings (related) and up to parent hubs
- Every page has 10–30 internal links from other programmatic pages

Rule of thumb: an isolated page (few internal links) stops ranking even if content is strong.

## Quality gates before shipping

Before launching 10,000 pages, run every template through these gates:

- [ ] Each page has **unique data in the first 100 words** (not just title swap)
- [ ] Each page has at least one unique table / chart / list drawn from data
- [ ] Canonical URL set to self
- [ ] Meta description dynamically generated from data (not static template)
- [ ] `<h1>` varies per page
- [ ] Page loads in <2s (programmatic SEO at scale murders performance if uncareful)
- [ ] Robots allowed, indexable
- [ ] Schema.org markup appropriate for content type (ItemList, Product, JobPosting, etc.)
- [ ] Empty-state handled (what if there are zero entities for `[city] × [category]`?)

**The empty-state question is underrated.** If your template renders a page like "Dentists in Peoria, IL" and the database has zero dentists in Peoria, you have three options: (a) redirect to parent category, (b) 404, (c) render with zero-state copy. Do **not** publish thin "we couldn't find any dentists in Peoria" pages at scale — that's exactly what Google penalizes.

## Scaling safely

### Launch in waves

Don't publish all 100,000 pages at once. Publish in batches of 2,000–5,000. Watch Search Console:
- Does `Indexed` grow proportionally?
- Are crawled pages getting indexed? Or are most `Crawled — currently not indexed`?
- Are some getting `Alternate page with proper canonical tag`?

If most pages aren't indexing, the quality isn't good enough. Improve the template or add more data per page.

### Monitor crawl budget

Large programmatic sites can exhaust Google's crawl budget. Signals:
- `Pages discovered — currently not indexed` rising
- Crawl stats showing <1 page/sec even for high-authority sites

Mitigations:
- Server speed (p90 response time <300ms for HTML)
- Reduce low-value pages (prune low-search-demand URL patterns)
- `<lastmod>` in sitemap only when content actually changes (not every deploy)

### Index-gate, don't publish-gate

Publish all pages. Noindex the ones that don't merit indexing (thin, empty-state, deprecated). Don't hide them behind auth — Google needs to see them to honor the noindex signal.

## Example: "BPM workout music" for FitBeat Music

```
/music/by-bpm/120-bpm/
/music/by-bpm/140-bpm/
/music/by-bpm/160-bpm/
...
/music/by-workout/boxing/140-bpm/
/music/by-workout/running/160-bpm/
...
```

Each page needs genuinely useful content:
- List of FitBeat's tracks at that BPM (real inventory)
- Explanation of why that BPM suits that workout (short, factual)
- Embedded 20-second previews
- Related BPM ranges
- Comparison to free Spotify / Apple Music options at same BPM
- User rating / use-count if available

~40 BPM values × 6 workout categories = 240 pages. Each has unique music inventory. This is real programmatic SEO with a genuine moat — the music library.

## Example: "makeup artists in [city]" for pro.makeup

```
/find/city/[city-name]/
/find/city/[city-name]/[category]/
```

- 500 cities × 5 categories = 2,500 pages
- Each page must list real verified artists (this is the entire business thesis)

If the directory has <100 MUAs total, this is an empty-state disaster. Programmatic SEO requires **the inventory to exist first**. This is the chicken-and-egg for pro.makeup: you can't do programmatic SEO until you have artists listed in every major city.

## Common pitfalls

- Publishing before the data layer has real, varied content → thin content penalty
- Not handling empty state → thousands of placeholder pages
- No canonicalization → duplicate content
- No internal linking between programmatic pages → orphaned pages
- Static / templated meta descriptions across all pages → wasted ranking signal
- Duplicating content across similar URLs (`/austin-tx/` + `/austin/`) → pick one, 301 the other
- No monitoring after launch → discovering problems 3 months later

## Programmatic SEO audit checklist

- [ ] Data layer has unique, factual content per page (not just name swap)
- [ ] Each template passes the "5-second differentiation test" — reader can see it's specifically about this entity within 5 seconds
- [ ] URL structure is clean path-based, not parameter-based
- [ ] Canonical URLs set self-referencing
- [ ] Sitemap index + per-category sitemaps
- [ ] Internal linking between sibling / parent / child pages (10–30 per page)
- [ ] Schema.org markup per page type
- [ ] Empty-state handled (redirect / noindex / hide)
- [ ] Launched in waves with Search Console monitoring
- [ ] Pruning criteria defined (when to noindex or 410 low-performers)
