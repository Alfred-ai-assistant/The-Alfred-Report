Alfred Report — Public Stock Per-Ticker News Module (Fresh-Only)

Goal

Add a “Stock News” section to the Daily Alfred Report that feels fresh every day:
	•	If a story link appeared on yesterday’s report, do not show it again today (even if it’s still relevant).
	•	It’s acceptable for some tickers to have no stories on a given day.
	•	Inputs (tickers + ranking config) live in YAML files in the existing config folder.
	•	Output is a ranked list per ticker with a short “why it ranked” note.
	•	No links to old stories; only show links that are new vs yesterday.

⸻

Data flow
	1.	Load configuration YAMLs from config folder.
	2.	For each ticker, collect stories from sources (Google News, Yahoo Finance news by ticker, plus your curated sources list).
	3.	Normalize + dedupe stories into clusters.
	4.	Apply Fresh-Only filter against “yesterday’s published links” cache.
	5.	Score clusters and select top items per ticker.
	6.	Render into the daily report.
	7.	Persist today’s “shown links” so tomorrow can filter them out.

⸻

Config files (YAML)

1) Tickers list

File: config/stocks.tickers.yaml

Schema
	•	tickers: list of strings (e.g., NVDA, MSFT)
	•	Optional per-ticker settings:
	•	enabled: bool (default true)
	•	max_top: override global
	•	min_score: override global
	•	tags_boost: optional map of tag->boost (for your personal priorities)

Example

tickers:
  - symbol: NVDA
    enabled: true
  - symbol: MSFT
  - symbol: NET
  - symbol: PLTR
  - symbol: AVGO


File: config/stocks.news_ranker.yaml

Schema
	•	fresh_only:
	•	exclude_if_seen_in_last_reports: integer (default 1 = yesterday only)
	•	allow_repeat_if_url_changed: bool (default false)
	•	freshness:
	•	half_life_minutes: 720
	•	floor: 0.15
	•	thresholds:
	•	top_min_score: 55
	•	must_include_score: 80
	•	glance_range: [45, 54]
	•	max_top: 5
	•	max_glance: 3
	•	sources (initial list you approved):
	•	each has trust, speed, tier
	•	event_weights (tag->weight)
	•	dedupe:
	•	strip_query_params: [utm_source, utm_medium, utm_campaign, utm_term, utm_content, ref, cmpid]
	•	title_stopwords: optional list (or just use internal defaults)
	•	novelty:
	•	same_tag_penalty_6h: 0.25
	•	same_tag_penalty_24h: 0.45
	•	similar_title_penalty_48h: 0.60
	•	syndication:
	•	confirm_boost_per_extra_source: 0.15
	•	confirm_boost_cap: 1.0
	•	tier1_boost: 0.25

Example:
fresh_only:
  exclude_if_seen_in_last_reports: 1
  allow_repeat_if_url_changed: false

freshness:
  half_life_minutes: 720
  floor: 0.15

thresholds:
  top_min_score: 55
  must_include_score: 80
  glance_range: [45, 54]
  max_top: 5
  max_glance: 3

sources:
  reuters: { trust: 95, speed: 90, tier: 1 }
  bloomberg: { trust: 95, speed: 90, tier: 1 }
  wsj: { trust: 92, speed: 75, tier: 1 }
  ft: { trust: 90, speed: 70, tier: 1 }
  cnbc: { trust: 80, speed: 90, tier: 2 }
  marketwatch: { trust: 75, speed: 80, tier: 2 }
  barrons: { trust: 85, speed: 65, tier: 2 }
  seekingalpha: { trust: 70, speed: 60, tier: 3 }
  benzinga: { trust: 72, speed: 88, tier: 3 }
  reddit: { trust: 35, speed: 85, tier: 4 }
  x: { trust: 35, speed: 90, tier: 4 }

event_weights:
  guidance: 95
  sec_filing: 90
  earnings: 85
  m_and_a_confirmed: 90
  m_and_a_rumor: 70
  regulatory_action: 90
  probe_or_investigation: 80
  lawsuit: 75
  contract_win: 70
  product_launch_major: 60
  analyst_change_major: 55
  analyst_reiterate: 25
  macro: 35

dedupe:
  strip_query_params: [utm_source, utm_medium, utm_campaign, utm_term, utm_content, ref, cmpid]

novelty:
  same_tag_penalty_6h: 0.25
  same_tag_penalty_24h: 0.45
  similar_title_penalty_48h: 0.60

syndication:
  confirm_boost_per_extra_source: 0.15
  confirm_boost_cap: 1.0
  tier1_boost: 0.25

Fresh-Only behavior (must enforce)

Definition of “seen”

A story is considered “seen” if its canonical URL (after stripping tracking params and normalizing domain) appeared in the prior report(s) governed by exclude_if_seen_in_last_reports.

Required outcome
	•	Today’s output must contain only URLs not shown yesterday.
	•	If filtering removes everything for a ticker, that ticker section is blank (or omitted entirely—pick one consistent approach).

Canonical URL rules
	•	Lowercase hostname
	•	Remove trailing /
	•	Remove known tracking query params (config list)
	•	If the source uses redirects (Google News), attempt to resolve to publisher URL when feasible; otherwise treat the redirect URL as canonical.

⸻

State / cache (for freshness)

Persist a rolling “shown links” record.

File: state/stocks_news_seen.json (or similar in existing state dir)

Structure
	•	keyed by report_date (YYYY-MM-DD)
	•	each date contains:
	•	urls: list (or set) of canonical URLs shown anywhere in the report
	•	optional: per ticker list to help debugging

Example (conceptual)
{
  "2026-02-24": {
    "urls": ["https://www.reuters.com/...","https://finance.yahoo.com/..."],
    "by_ticker": { "NVDA": ["..."], "MSFT": ["..."] }
  }
}

Retention:
	•	Keep at least the last exclude_if_seen_in_last_reports + 2 days.
	•	Safe to cap at 30 days.

⸻

Story collection (per ticker)

Minimum feeds (v1):
	•	Google News query for ticker + company name (if available)
	•	Yahoo Finance ticker news
	•	Source-direct feeds where easy (optional v1): Reuters/WSJ/etc via whatever access you already have

Normalize into an internal list of candidate stories:
	•	title
	•	source (mapped to sources keys when possible; else unknown)
	•	url
	•	published_at (best effort; if missing, use fetch time)
	•	optional snippet/summary if available

⸻

Dedupe and clustering

For each ticker’s candidate stories:
	1.	Build story_key using:
	•	normalized title (lowercase, punctuation stripped, common suffixes removed)
	•	canonical domain of URL
	2.	Group stories with same key into a cluster.
	3.	Cluster attributes:
	•	earliest publish time
	•	best URL (prefer Tier 1 sources, else shortest canonical URL)
	•	list of unique sources in cluster (used for confirmation boost)

⸻

Event tagging

Create event_tags using headline + snippet keyword detection (lightweight heuristics).
Examples:
	•	“raises guidance”, “cuts outlook” → guidance
	•	“8-K”, “files”, “SEC” → sec_filing
	•	“acquire”, “merger”, “deal”, “in talks” → m_and_a_confirmed or m_and_a_rumor
	•	“DOJ”, “FTC”, “SEC charges”, “export controls” → regulatory_action
	•	“upgraded”, “downgraded” + bank names → analyst_change_major
	•	“reiterates”, “maintains” → analyst_reiterate
	•	etc.

If no tags match, assign other with a low default weight (e.g., 20).

⸻

Scoring model (0–100)

Use the model below (exact math is flexible; outputs should behave similarly).

Source score

source_score = 0.7*trust + 0.3*speed

Event score

event_score = max(event_weights(tags)) + 0.15*sum(other_tag_weights capped at 60)

Freshness score

t = minutes since published
freshness = exp(-t / half_life_minutes) clamped to [floor..1]

Confirmation / syndication boost
	•	confirm_boost = min(confirm_boost_cap, confirm_boost_per_extra_source*(unique_sources - 1))
	•	tier1_boost = tier1_boost if any Tier 1 source present else 0

Novelty penalty (within the same run and recent history)

Apply penalties if the ticker already has similar tag/title recently (config values).

Final score

Combine:
	•	45% source
	•	40% event
	•	15% freshness
then apply boosts and penalties; clamp to [0..100].

⸻

Selection logic (per ticker)

After scoring, apply Fresh-Only filter first, then select:
	•	Top Stories: highest scores where score >= top_min_score, up to max_top
	•	Worth a glance: scores within glance_range only if they introduce a new tag today for that ticker, up to max_glance
	•	Always include any story with score >= must_include_score even if it’s older (but still must pass Fresh-Only).

If nothing remains: output blank/omitted.

⸻

Rendering format in the Alfred Report

Per ticker section:

Ticker header: NVDA — Stock News
For each item:
	•	[score] {tag} — {headline} (Source, HH:MM)
	•	one-sentence summary (generated)
	•	Why it ranked: Event=guidance(95) Source=Reuters(93) Fresh=0.82 Confirm=3

Link policy
	•	Include the URL only for items that passed Fresh-Only (they will be new vs yesterday by definition).
	•	If you prefer zero URLs entirely in the report, store them for drill-through elsewhere—but your requirement was “no links if they were on yesterday’s report,” so showing new links is fine.

⸻

Logging & debugging requirements

Write a compact debug log per run:
	•	tickers processed
	•	candidate count per ticker
	•	removed by Fresh-Only (count)
	•	top selected items with scores
	•	cache write success and date key used

This will prevent “why is my ticker blank?” confusion.

⸻

Acceptance tests (must pass)
	1.	If a URL was shown on 2026-02-24, it must not appear on 2026-02-25 output.
	2.	If all candidate stories for a ticker were shown yesterday, ticker output is blank/omitted.
	3.	If a story appears from multiple sources today but was shown yesterday (any URL match), it is still excluded.
	4.	Changing only UTM parameters does not bypass the Fresh-Only filter.
	5.	Config changes in YAML take effect without code changes.

⸻

Deliverables summary
	•	config/stocks.tickers.yaml
	•	config/stocks.news_ranker.yaml
	•	state/stocks_news_seen.json (created/maintained automatically)
	•	Report section: “Stock News” with per-ticker ranked items filtered for freshness
