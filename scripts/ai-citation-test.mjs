#!/usr/bin/env node
/**
 * ai-citation-test.mjs
 *
 * Query OpenAI / Anthropic / Perplexity / Gemini with a list of commercial
 * prompts and measure how often a brand / domain is cited. Outputs a JSON
 * report suitable for delta comparison across runs.
 *
 * Usage:
 *   node ai-citation-test.mjs \
 *     --brand="DIDWW" \
 *     --domain="didww.com" \
 *     --prompts=prompts.txt \
 *     [--providers=openai,anthropic,perplexity,gemini] \
 *     [--output=report.json] \
 *     [--competitors="Twilio,Bandwidth,Telnyx"]
 *
 * Env vars (set at least one):
 *   OPENAI_API_KEY
 *   ANTHROPIC_API_KEY
 *   PERPLEXITY_API_KEY
 *   GEMINI_API_KEY
 *
 * prompts.txt format: one commercial prompt per line. Empty lines and
 * lines starting with # are ignored. Example:
 *   best global SIP trunking provider for AI voice agents
 *   cheapest DID number provider Germany
 *   # regulated voice infrastructure comparison
 *   EU data-residency voice API providers
 */

import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";

// ---------- arg parsing ----------

const argv = Object.fromEntries(
  process.argv.slice(2).map((a) => {
    const m = a.match(/^--([^=]+)(?:=(.*))?$/);
    if (!m) return [a, true];
    return [m[1], m[2] ?? true];
  })
);

const BRAND = argv.brand;
const DOMAIN = argv.domain;
const PROMPTS_FILE = argv.prompts;
const OUTPUT = argv.output || `ai-citations-${new Date().toISOString().slice(0, 10)}.json`;
const COMPETITORS = (argv.competitors || "").split(",").map((s) => s.trim()).filter(Boolean);

if (!BRAND || !PROMPTS_FILE) {
  console.error(
    "Usage: node ai-citation-test.mjs --brand=X --domain=X --prompts=X.txt [--providers=X] [--output=X] [--competitors=X,Y,Z]"
  );
  process.exit(1);
}

const PROVIDERS_REQUESTED = (argv.providers || "openai,anthropic,perplexity,gemini")
  .split(",")
  .map((s) => s.trim().toLowerCase())
  .filter(Boolean);

// ---------- provider availability ----------

const PROVIDERS = {
  openai: { key: process.env.OPENAI_API_KEY, fn: askOpenAI },
  anthropic: { key: process.env.ANTHROPIC_API_KEY, fn: askAnthropic },
  perplexity: { key: process.env.PERPLEXITY_API_KEY, fn: askPerplexity },
  gemini: { key: process.env.GEMINI_API_KEY, fn: askGemini },
};

const activeProviders = PROVIDERS_REQUESTED.filter((p) => PROVIDERS[p]?.key);
const skippedProviders = PROVIDERS_REQUESTED.filter((p) => !PROVIDERS[p]?.key);

if (activeProviders.length === 0) {
  console.error("No provider API keys found. Set at least one of:");
  console.error("  OPENAI_API_KEY, ANTHROPIC_API_KEY, PERPLEXITY_API_KEY, GEMINI_API_KEY");
  process.exit(1);
}

if (skippedProviders.length) {
  console.warn(`Skipping providers (no API key): ${skippedProviders.join(", ")}`);
}

// ---------- prompts ----------

if (!existsSync(PROMPTS_FILE)) {
  console.error(`Prompts file not found: ${PROMPTS_FILE}`);
  process.exit(1);
}

const prompts = readFileSync(PROMPTS_FILE, "utf8")
  .split("\n")
  .map((l) => l.trim())
  .filter((l) => l && !l.startsWith("#"));

if (prompts.length === 0) {
  console.error(`No prompts found in ${PROMPTS_FILE}`);
  process.exit(1);
}

console.log(`Testing ${prompts.length} prompts × ${activeProviders.length} providers = ${prompts.length * activeProviders.length} queries`);

// ---------- provider implementations ----------

async function askOpenAI(prompt) {
  // gpt-4o with web search enabled. Fallback to gpt-4o-mini without search
  // if web search access is not available on the account.
  const res = await fetch("https://api.openai.com/v1/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
    },
    body: JSON.stringify({
      model: "gpt-4o-search-preview",
      messages: [{ role: "user", content: prompt }],
      max_tokens: 800,
    }),
  });
  if (!res.ok) {
    // Fallback: plain gpt-4o-mini (no web search)
    const fallback = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
      },
      body: JSON.stringify({
        model: "gpt-4o-mini",
        messages: [{ role: "user", content: prompt }],
        max_tokens: 800,
      }),
    });
    if (!fallback.ok) throw new Error(`OpenAI error: ${res.status} / fallback ${fallback.status}`);
    const data = await fallback.json();
    return { text: data.choices?.[0]?.message?.content ?? "", fallback: true };
  }
  const data = await res.json();
  return { text: data.choices?.[0]?.message?.content ?? "", fallback: false };
}

async function askAnthropic(prompt) {
  const res = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-api-key": process.env.ANTHROPIC_API_KEY,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify({
      model: "claude-opus-4-7",
      max_tokens: 800,
      messages: [{ role: "user", content: prompt }],
      tools: [{ type: "web_search_20250305", name: "web_search", max_uses: 3 }],
    }),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Anthropic error: ${res.status} ${body.slice(0, 200)}`);
  }
  const data = await res.json();
  const text = (data.content || [])
    .filter((b) => b.type === "text")
    .map((b) => b.text)
    .join("\n");
  return { text };
}

async function askPerplexity(prompt) {
  const res = await fetch("https://api.perplexity.ai/chat/completions", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${process.env.PERPLEXITY_API_KEY}`,
    },
    body: JSON.stringify({
      model: "sonar-pro",
      messages: [{ role: "user", content: prompt }],
      max_tokens: 800,
    }),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Perplexity error: ${res.status} ${body.slice(0, 200)}`);
  }
  const data = await res.json();
  const text = data.choices?.[0]?.message?.content ?? "";
  const citations = data.citations || [];
  return { text, structuredCitations: citations };
}

async function askGemini(prompt) {
  const model = "gemini-2.0-flash";
  const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${process.env.GEMINI_API_KEY}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      contents: [{ role: "user", parts: [{ text: prompt }] }],
      tools: [{ google_search: {} }],
    }),
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Gemini error: ${res.status} ${body.slice(0, 200)}`);
  }
  const data = await res.json();
  const text =
    data.candidates?.[0]?.content?.parts?.map((p) => p.text).filter(Boolean).join("\n") ?? "";
  const groundingChunks =
    data.candidates?.[0]?.groundingMetadata?.groundingChunks ?? [];
  const citations = groundingChunks.map((c) => c.web?.uri).filter(Boolean);
  return { text, structuredCitations: citations };
}

// ---------- extractors ----------

function extractUrls(text) {
  const urlRegex = /https?:\/\/[^\s)\]>,"']+/gi;
  return [...new Set((text.match(urlRegex) || []).map((u) => u.replace(/[.,;:)]+$/, "")))];
}

function countMentions(text, needle) {
  if (!needle) return 0;
  const escaped = needle.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const re = new RegExp(`\\b${escaped}\\b`, "gi");
  return (text.match(re) || []).length;
}

function firstMentionPosition(text, needle) {
  if (!needle) return -1;
  const i = text.toLowerCase().indexOf(needle.toLowerCase());
  return i === -1 ? -1 : i;
}

function domainFromUrl(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, "").toLowerCase();
  } catch {
    return null;
  }
}

function crudeSentiment(text, brand) {
  if (!brand) return "neutral";
  // Cheap heuristic: look for positive/negative words within ~80 chars of each brand mention.
  const lower = text.toLowerCase();
  const brandLower = brand.toLowerCase();
  const positives = /(best|top|leader|recommend|excellent|reliable|trusted|innovative|strong)/i;
  const negatives = /(poor|avoid|bad|failed|slow|unreliable|deprecated|shutdown|lawsuit)/i;
  let pos = 0, neg = 0;
  let from = 0;
  while (true) {
    const idx = lower.indexOf(brandLower, from);
    if (idx === -1) break;
    const window = text.slice(Math.max(0, idx - 80), idx + brand.length + 80);
    if (positives.test(window)) pos++;
    if (negatives.test(window)) neg++;
    from = idx + brand.length;
  }
  if (pos > neg) return "positive";
  if (neg > pos) return "negative";
  return "neutral";
}

// ---------- run ----------

const report = {
  meta: {
    brand: BRAND,
    domain: DOMAIN || null,
    competitors: COMPETITORS,
    providers: activeProviders,
    promptCount: prompts.length,
    timestamp: new Date().toISOString(),
  },
  results: [],
  aggregate: {},
};

for (const prompt of prompts) {
  for (const provider of activeProviders) {
    process.stdout.write(`[${provider}] ${prompt.slice(0, 60)}${prompt.length > 60 ? "…" : ""} ... `);
    try {
      const { text, structuredCitations = [], fallback } = await PROVIDERS[provider].fn(prompt);
      const urls = [...new Set([...extractUrls(text), ...structuredCitations])];
      const domains = [...new Set(urls.map(domainFromUrl).filter(Boolean))];

      const brandMentions = countMentions(text, BRAND);
      const brandPosition = firstMentionPosition(text, BRAND);
      const domainMentioned = DOMAIN
        ? domains.some((d) => d === DOMAIN.toLowerCase() || d.endsWith(`.${DOMAIN.toLowerCase()}`))
        : false;
      const competitorsCited = {};
      for (const c of COMPETITORS) {
        const count = countMentions(text, c);
        if (count > 0) competitorsCited[c] = count;
      }
      const sentiment = brandMentions > 0 ? crudeSentiment(text, BRAND) : "not-mentioned";

      report.results.push({
        prompt,
        provider,
        fallback: !!fallback,
        brandMentions,
        brandPosition,
        domainMentioned,
        competitorsCited,
        sentiment,
        urls,
        domains,
        text,
      });
      const status =
        brandMentions > 0
          ? `✓ brand mentioned ${brandMentions}× (${sentiment})`
          : Object.keys(competitorsCited).length > 0
          ? `✗ brand missing · competitors: ${Object.keys(competitorsCited).join(", ")}`
          : `✗ brand missing`;
      console.log(status);
    } catch (err) {
      console.log(`ERROR ${err.message}`);
      report.results.push({ prompt, provider, error: err.message });
    }
  }
}

// ---------- aggregate ----------

function aggregate(rows) {
  const total = rows.filter((r) => !r.error).length;
  const mentioned = rows.filter((r) => (r.brandMentions || 0) > 0).length;
  const domainMentioned = rows.filter((r) => r.domainMentioned).length;
  const sentimentDist = { positive: 0, neutral: 0, negative: 0, "not-mentioned": 0 };
  const competitorCounts = {};
  for (const r of rows) {
    if (r.error) continue;
    sentimentDist[r.sentiment] = (sentimentDist[r.sentiment] || 0) + 1;
    for (const [c, n] of Object.entries(r.competitorsCited || {})) {
      competitorCounts[c] = (competitorCounts[c] || 0) + (n > 0 ? 1 : 0);
    }
  }
  return {
    queriesRun: total,
    brandMentionRate: total ? mentioned / total : 0,
    domainCitationRate: total ? domainMentioned / total : 0,
    sentiment: sentimentDist,
    competitorMentionRates: Object.fromEntries(
      Object.entries(competitorCounts).map(([k, v]) => [k, total ? v / total : 0])
    ),
  };
}

report.aggregate.overall = aggregate(report.results);
for (const p of activeProviders) {
  report.aggregate[p] = aggregate(report.results.filter((r) => r.provider === p));
}

// ---------- output ----------

const outPath = resolve(OUTPUT);
writeFileSync(outPath, JSON.stringify(report, null, 2));

console.log("\n================ SUMMARY ================");
console.log(`Brand: ${BRAND}${DOMAIN ? ` (${DOMAIN})` : ""}`);
console.log(`Queries: ${report.aggregate.overall.queriesRun}`);
console.log(`Brand mention rate: ${(report.aggregate.overall.brandMentionRate * 100).toFixed(1)}%`);
console.log(`Domain citation rate: ${(report.aggregate.overall.domainCitationRate * 100).toFixed(1)}%`);
console.log(`Sentiment: ${JSON.stringify(report.aggregate.overall.sentiment)}`);
if (Object.keys(report.aggregate.overall.competitorMentionRates).length) {
  console.log("Competitor mention rates:");
  for (const [c, r] of Object.entries(report.aggregate.overall.competitorMentionRates).sort(
    (a, b) => b[1] - a[1]
  )) {
    console.log(`  ${c}: ${(r * 100).toFixed(1)}%`);
  }
}
console.log(`\nReport written to: ${outPath}`);
