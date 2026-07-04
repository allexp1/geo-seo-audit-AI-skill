# Content Decay and Refresh Strategy

Content loses rankings over time — not because it gets "worse," but because the world moves, competitors publish newer pieces, freshness signals weight against older content, and specific facts go stale. Managing decay systematically is often a higher-ROI activity than writing new content.

## Why content decays

1. **Freshness weighting** — Google's QDF (Query Deserves Freshness) algorithm boosts recent content for many query types
2. **Competitive displacement** — competitors publish better / more comprehensive versions
3. **Fact rot** — specific prices, statistics, version numbers, dates become wrong
4. **Link rot** — outbound links 404, reducing perceived quality
5. **Internal cannibalization** — you published a newer piece that competes with this one
6. **Intent drift** — the query that drove traffic now means something slightly different

## Detection — find what's decaying

### Search Console approach

```bash
# Using the scripts/search-console-export.mjs helper
GSC_ACCESS_TOKEN=... node scripts/search-console-export.mjs \
  https://example.com \
  2025-10-01 2026-01-31 \
  > clicks-last-quarter.json
```

Compare the same query for two periods. A page losing >20% clicks period-over-period is a refresh candidate.

### Cohort approach

Pull all URLs published in a given quarter (e.g., Q1 2025). Look at clicks over time for that cohort:

```
Cohort: published Q1 2025
Month 1: 100% baseline (full month post-publish)
Month 3: 120% (still growing)
Month 6: 140% (peak)
Month 12: 110% (decaying from peak)
Month 18: 80%
Month 24: 55%  ← refresh or prune
```

The curve is category-dependent. News content peaks within days; evergreen content can peak at 6-12 months; reference content can grow for years.

## Refresh vs. prune vs. consolidate

For each decaying page, pick one action:

### Refresh (most common)

The page still serves real search intent. Update it:
- Update the date (`dateModified` in schema, visible "Last updated" byline)
- Replace stale facts / stats / prices
- Fix broken outbound links
- Add new sections reflecting recent developments
- Improve formatting for AEO (40-60 word direct answer, FAQ block)
- Re-submit in GSC ("URL inspection" → "Request indexing")

Rule of thumb: refresh if >30% of the content is still useful. Rewriting makes more sense if less than that.

### Consolidate (merge into another page)

You have two pages competing for the same intent (content cannibalization). Pick the stronger one, merge the weaker's unique content into it, 301 redirect the weaker URL to the stronger.

```
Old: /blog/how-to-pick-sip-trunk (12 clicks/mo, weak)
Old: /blog/best-sip-trunk-providers (340 clicks/mo, strong)

After consolidation:
- Merge unique tips from /how-to into /best-
- 301 /how-to → /best-
- Update internal links to point to /best-
```

### Prune (remove / 410 / noindex)

The page no longer serves real intent. Options ranked by aggressiveness:

1. **Noindex** — keeps the URL alive (existing links work), removes from search index
2. **410 Gone** — tells Google the page is permanently removed
3. **301 Redirect** — to the nearest-intent replacement (if one exists)
4. **Delete + 404** — avoid; creates bad UX if any external links point here

Prune when: traffic is <5/mo, content is factually outdated beyond salvage, and there's no meaningful "replacement" intent to redirect to.

### Leave alone

Not every decay is fixable. A page about a discontinued product, a defunct service, a one-off news event — just let it go. Spending refresh effort on these returns nothing.

## Refresh prioritization matrix

| Decline | Effort to refresh | Action |
|---------|-------------------|--------|
| High traffic → big decline | Low | **Refresh immediately** |
| High traffic → big decline | High | **Refresh this quarter** |
| Medium traffic → decline | Low | Refresh in batches |
| Low traffic → decline | Any | Prune or consolidate |
| High traffic → no decline | N/A | Leave alone |

## Refresh execution workflow

```
1. Run GSC export for last 2 quarters
2. Find URLs where clicks dropped >20% QoQ
3. Filter for URLs still indexed and relevant to current business
4. Score each: traffic potential (was peak) × effort to refresh
5. Sort by score, take top 20 for the quarter
6. For each:
   a. Read the page
   b. Run the target query yourself — look at top 3 competing pages
   c. Note what they have that you don't
   d. Update content, date, schema
   e. Submit in GSC
7. Measure in 30 days — did clicks recover?
```

## Signals a page is ripe for refresh

- Ranking dropped 5+ positions in last 90 days (GSC position data)
- CTR for the same position is below category median (searcher picks competitor when both show)
- Outbound links have 404s
- Stats / prices / version numbers in the page are visibly outdated
- "Published" / "Updated" date is >18 months ago
- Top-of-page image is dated visually
- Schema.org `dateModified` is stale

## Quarterly refresh cadence

Recommended rhythm for a content-driven site:

| Cadence | Pages | Action |
|---------|-------|--------|
| Weekly | Top 5 breaking-news-relevant pages | Update within 24h of major developments |
| Monthly | Top 20 traffic drivers | Spot-check for stale facts |
| Quarterly | 20 high-potential decaying pages | Deep refresh |
| Semi-annually | All evergreen pillars | Full refresh + visual update |
| Annually | Entire content inventory | Prune decision (keep / merge / remove) |

## Indicator: `dateModified` matters more than `datePublished`

For AEO especially. AI engines disproportionately cite recently-updated content. Keep `datePublished` as the original ship date; update `dateModified` every meaningful refresh:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "datePublished": "2024-03-15",
  "dateModified": "2026-04-18"
}
</script>
```

Visible "Last updated" byline helps too — users click fresher content.

## Common pitfalls

- Refreshing only the date without actually updating content → Google detects "fake freshness" and ignores the signal
- Refreshing too frequently on unchanging content → creates noise
- Not submitting refreshed pages in GSC → refresh not registered for weeks
- Pruning without considering backlinks → losing earned authority
- Consolidating without 301 → losing equity from the removed URL

## Content-decay audit checklist

- [ ] Search Console export for last 2 quarters available
- [ ] Top 50 traffic-driving URLs listed
- [ ] Decline-rate calculated per URL
- [ ] Top 20 refresh candidates prioritized
- [ ] Prune list separate from refresh list
- [ ] Consolidation opportunities (cannibalization) identified
- [ ] `dateModified` discipline defined for refresh workflow
- [ ] Quarterly refresh cadence scheduled (not ad-hoc)
