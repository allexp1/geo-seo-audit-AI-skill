# Topical Authority and Content Clusters

Ranking for one query is harder than ranking for a cluster of related queries. A site that covers a topic comprehensively — pillar pages, deep supporting content, internal linking that reinforces relationships — ranks better than a site with one lonely article on the topic, even if the lonely article is brilliantly written.

## Mental model — the "topic expert" test

Imagine two sites pitching for the same slot in Google's index on "SIP trunking":

**Site A:** One 3,000-word article titled "Best SIP Trunking Providers 2026"
**Site B:** 40 interconnected pages covering: what SIP trunking is, how to choose a provider, per-country DID pricing, SIP codecs explained, STIR/SHAKEN compliance, SIP vs PRI, SIP for voice AI, SIP troubleshooting, 15 specific provider reviews, comparison pages

Site B ranks higher for the headline query even if Site A's individual page is better written. Google reads comprehensiveness as expertise; AI models cite comprehensive sites more often.

## The content cluster structure

```
                ┌────────────────┐
                │  PILLAR PAGE   │  ← /sip-trunking/
                │  (broad topic) │
                └────┬───────┬───┘
        ┌────────────┤       ├──────────────┐
        │            │       │              │
        ▼            ▼       ▼              ▼
   ┌─────────┐  ┌─────────┐  ┌──────────┐  ┌──────────┐
   │ Cluster │  │ Cluster │  │ Cluster  │  │ Cluster  │
   │ post 1  │  │ post 2  │  │ post 3   │  │ post 4   │
   └────┬────┘  └────┬────┘  └─────┬────┘  └─────┬────┘
        │            │             │             │
        ▼            ▼             ▼             ▼
   ┌─────────────────────────────────────────────────┐
   │          DEEP SUPPORTING CONTENT                │
   │  (spec pages, how-tos, comparisons, FAQ)        │
   └─────────────────────────────────────────────────┘

   Every page links up (to pillar), down (to children),
   and laterally (to siblings).
```

**Pillar page:** broad topic, 2,500–5,000 words, covers the whole area
**Cluster posts:** specific sub-topics, 800–2,500 words each, 10–30 of them
**Supporting content:** FAQs, glossaries, specific how-tos, comparisons

## Building a cluster — step by step

### 1. Pick the pillar topic

The pillar should represent a major area of commercial intent for your business. Tests:
- Do you want to sell something adjacent to this topic?
- Is there enough sub-topic depth to support 10+ pages?
- Is the topic stable for 3+ years?

Example pillars per subject:
- **DIDWW:** SIP trunking, voice AI infrastructure, DID numbering, compliance
- **FitBeat Music:** BPM workout music, tempo-matching running, interval training music
- **pro.makeup:** professional makeup credentials, verified makeup artists, makeup certification
- **Enso.bot:** AI agents for SMBs, autonomous business tools, no-code AI workflows

Don't pick pillars broader than your business — you won't rank and you won't convert if you did.

### 2. Keyword cluster — map the territory

Using `references/keyword-research.md`, build a full inventory of queries in the topic. Group by intent:

- **Definition queries** — "what is SIP trunking"
- **How-to queries** — "how to set up SIP trunking"
- **Comparison queries** — "SIP trunking vs PRI"
- **Provider queries** — "best SIP trunking providers"
- **Niche queries** — "SIP trunking for voice AI agents"
- **Troubleshooting** — "SIP trunking registration failed"

Target 30–50 queries for a solid cluster. Too few = thin cluster. Too many = unfocused.

### 3. Design the information architecture

For each query, assign:
- **URL** (path structure matters — `/guides/sip-trunking/vs-pri` beats `/blog/post-423`)
- **Depth in hierarchy** (pillar, cluster, support)
- **Primary / secondary / tertiary keywords**
- **Internal links it should have (to / from)**

Single URL structure example:

```
/sip-trunking/                          ← pillar
/sip-trunking/how-it-works              ← cluster
/sip-trunking/how-to-choose-a-provider  ← cluster
/sip-trunking/voice-ai-agents           ← cluster (target vertical)
/sip-trunking/compliance/stir-shaken    ← support
/sip-trunking/compliance/kyc            ← support
/sip-trunking/troubleshooting/...       ← support
/sip-trunking/compare/twilio            ← support
/sip-trunking/compare/bandwidth         ← support
```

### 4. Build the pillar first

The pillar exists to claim the broad topic and hand off to children. Structure:

- H1 matching the main topic
- Table of contents linking to H2s (each H2 also has a cluster post)
- 200–400 words per H2 (enough for snippet eligibility, not a full essay)
- Each H2 ends with "Learn more: [link to cluster page]"
- Internal links to support content throughout
- Schema: `Article` + `FAQPage` if Q&A included

### 5. Write cluster content with rigor

Each cluster post should be able to win its specific long-tail query on its own merits. It's linked from the pillar but doesn't depend on the pillar for value.

Per post:
- H1 = primary keyword (or close variant)
- 40-60 word direct answer in first 300 words (featured snippet + AEO)
- Embedded FAQ section (4-8 questions) with `FAQPage` schema
- Internal links: up to pillar, to 2-4 sibling cluster posts, to 2-4 support pages
- Updated `dateModified` when refreshed

### 6. Interlink ruthlessly

The cluster fails without internal linking. Rule of thumb:

- Every page links **up** to its parent (pillar or category)
- Every page links **laterally** to at least 3 sibling pages
- Every page links **down** to at least 2 child / supporting pages
- Pillar pages have 20–30 internal links out
- Cluster pages have 8–15 internal links out

Anchor text should be descriptive (not "click here") and use natural keyword variations, not exact-match spam.

## Ordering of publication

Don't publish the pillar alone; it dies without children. Ordering:

1. Stub the pillar page (publish with basic content — flesh out later)
2. Publish 5–8 cluster posts first month
3. Expand the pillar as each cluster post publishes
4. Publish 10–20 more cluster posts over the next 2–3 months
5. Support content follows as gaps are discovered

## Measuring cluster health

Monthly:

- **Average ranking position across cluster keywords** — should improve as cluster matures
- **Total impressions** on cluster URLs in GSC
- **Total clicks** on cluster URLs
- **Ratio of ranked queries to total targeted** — aim 80%+
- **Internal-linking-graph coverage** — every cluster page has inbound links from ≥3 other cluster pages

## Anti-patterns

### 1. Keyword cannibalization within the cluster

Two cluster posts competing for the same query. Fix via consolidation (see `references/content-decay.md`).

### 2. Pillar that's just a linkfarm

Pillar pages must stand on their own as substantive content, not just list of links. "Ultimate guide" pages with 20 links and no real body fail.

### 3. No commercial connection

Building a cluster for pure content SEO without a clear path to conversion. Every pillar should route toward a commercial page (product, pricing, contact) within 1-2 clicks.

### 4. One-and-done publication

Writing the cluster once and never refreshing. Clusters decay faster than standalone content because queries shift. Plan refresh cadence (`references/content-decay.md`).

### 5. Over-clustering

If you try to rank for every conceivable variation, you'll produce 100 thin posts that dilute authority. Fewer, denser posts win.

## AEO implications

AI citation correlates strongly with topical-authority signals. A pillar-and-cluster site gets cited more often because:

- Comprehensive coverage = multiple citation-worthy pages
- Internal linking creates clear entity relationships
- Sibling pages confirm facts across the cluster
- Schema at cluster scale reinforces topic authority

AI models specifically favor sources that "clearly specialize" over generalist sources. A site with 50 SIP-trunking pages will get cited over a site with one SIP-trunking page and 49 pages about unrelated topics.

## Cluster audit checklist

- [ ] Pillar topic identified with clear commercial tie
- [ ] Full keyword inventory (30–50 queries) for the cluster
- [ ] URL hierarchy mapped
- [ ] Pillar page published with real substantive content
- [ ] ≥10 cluster posts published
- [ ] Every cluster post links up, down, and laterally
- [ ] Anchor text varied and descriptive
- [ ] FAQ schema + Article schema applied
- [ ] Monthly measurement dashboard defined
- [ ] Refresh cadence scheduled
