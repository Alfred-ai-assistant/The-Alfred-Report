# Private Market Company News — Feature Spec 

Goal: Add a new daily report section that pulls “Private Market Company” news using Google News + general web search, with strict freshness (no repeat links from yesterday), and per-company daily link caps.

This should behave like the existing **Portfolio News** section (scoring, dedupe, formatting), but with more diverse sources allowed and less reliance on “major” outlets.

---

## Output: New Report Section

Section title (suggested):
**Private Market Company News (24h)**

For each company that has eligible items today:
- Company header line
- Up to N links (N depends on company)
- Each item includes:
  - Title
  - Source / domain
  - Published time (if available)
  - Optional short snippet (1 line)
  - Canonical URL (must be stable)

If a company has zero eligible items after filtering:
- Omit it entirely (preferred) OR show “No new items” (configurable; default omit)

---

## Input Config File

Create a YAML config file in the same config folder where your other YAML sources live.

YAML filed stored in Github at Alfred-ai-assistant/The-Alfred-Report/Config/private_market_news.yaml


Content: use the structured YAML we agreed on (companies + grouped queries + weights).  
This YAML is the single source of truth for:
- company list
- per-company link limit
- query groups and weights
- lookback window
- “don’t repeat yesterday” policy

---

## YAML Contract (Required Fields)

Top-level key:
- `private_market_news`

Required:
- `private_market_news.settings.lookback_hours` (default 24)
- `private_market_news.settings.dedupe_days` (default 1)
- `private_market_news.settings.max_candidates_per_company` (default 40)
- `private_market_news.settings.min_score` (default 0.55)

Weights:
- `private_market_news.settings.query_group_weights` (map of group → float)
- `private_market_news.settings.source_type_weights` (map of type → float)

Companies list:
- `private_market_news.companies[]`
  - `name` (string)
  - `limit` (int)  
    - 5 for: Cerebras Systems, Groq, SambaNova Systems, Liquid Death, Neuralink  
    - 3 for: Automation Anywhere, Dialpad, Impossible Foods, Dataminr, BitPay, Mythic AI
  - `enabled` (bool)
  - `queries` (map of group → list of query strings)
    - groups used in v1: `primary`, `capital_events`, `strategic`, `product`

---

## Query Design Explanation (Why multiple queries)

The grouped queries are intentional. A single phrase like `"Cerebras Systems"` will *not* reliably capture:
- shorthand usage (“Cerebras”)
- capital market language (“IPO”, “funding”, “valuation”)
- strategic terms (“partnership”, “contract”, “government”)
- product terms (“chip”, “accelerator”)

If you only use `"Cerebras Systems"` you’ll miss a lot of high-value items and you’ll also get “name-only” fluff.
Grouping lets us:
- widen recall without spamming output
- score higher-signal items (e.g., IPO/funding) above general mentions

---

## Data Sources

For each company query string:
- Google News search (news vertical)
- General web search (web vertical)

Source diversity rules:
- Allow non-major sources (blogs, trade sites, press releases, niche newsletters)
- Still apply domain quality scoring to prevent spam/SEO farms

Suggested “source_type” labeling:
- `news` for Google News results
- `web` for general web results
- `blog` if a result is clearly a blog/substack-like domain (optional heuristic)

---

## Freshness / “No Repeat Links From Yesterday”

Hard requirement:
- An article URL must NOT appear if it was shown in the previous day’s report.

Implementation requirement:
- Maintain a small daily history store of already-used canonical URLs for this section.
- On each run:
  - load yesterday’s URL set (or last `dedupe_days`)
  - filter any candidate whose canonical URL is already present
  - after final selection, write today’s URLs back to history

History file (suggested):
`/home/alfred/.openclaw/workspace/TheAlfredReport/private_market_news/seen_urls.json`
if there is already a place where we store this type of info for other features like portfolio stock news, use that folder instead

Stored data (suggested shape):
- Map of `YYYY-MM-DD` → list of canonical URLs
- Keep only last `dedupe_days + 2` to limit growth

Canonicalization rules (to reduce dupes):
- Strip tracking params (utm_*, gclid, fbclid, etc.)
- Normalize scheme/host casing
- Prefer final resolved URL if redirects are present
- Remove Google News redirect wrappers if encountered

---

## Scoring & Ranking

The ranking should work like Portfolio News with a slightly broader source acceptance.

For each candidate result, compute:

`final_score = recency_score * query_group_weight * source_type_weight * domain_quality_weight * title_quality_weight`

Where:
- `recency_score`: favors items within lookback window; decays with age
- `query_group_weight`: from YAML (e.g. capital_events 1.3 boosts IPO/funding)
- `source_type_weight`: from YAML (news > web > blog by default)
- `domain_quality_weight`: internal heuristic (known reputable domains higher; spam lower)
- `title_quality_weight`: penalize empty/garbled titles; boost “announces/raises/files/acquires/partners”

Filter rule:
- discard anything with `final_score < min_score`

Dedupe inside the same run:
- If multiple sources point to same canonical URL, keep the best-scoring instance only.

Selection:
- Sort remaining candidates by `final_score` desc
- Take first `company.limit`

---

## Runtime Behavior

Schedule:
- Runs once per day as part of the Alfred daily report pipeline.

Lookback:
- Default: last 24 hours (configurable via YAML)

Empty days:
- If a company has no eligible items (after scoring + dedupe), it is allowed to be blank for that day (preferred).

Safety valve:
- Cap total fetched candidates per company (`max_candidates_per_company`) to avoid runaway search.

---

## Integration Points

Add a new generator step:
- `private_market_news` section generator in page.tsx
- Reads: config/private_market_news.yaml from Github location reference above
- Writes: report markdown + seen URL history file

UI / report rendering:
- Add section near Portfolio News (either right below or right above)
- Maintain same formatting conventions as Portfolio News for consistency

---

## Observability

Logs should include:
- company name
- number of raw candidates
- number filtered by “seen yesterday”
- number filtered by score threshold
- number selected (final)
- top 1–2 reasons for rejection when debugging (optional)

---

## Acceptance Criteria

- YAML file exists in Github and is the only place companies/queries/weights are edited.
- Daily report section is generated.
- No URL shown today can appear if it appeared yesterday (within `dedupe_days`).
- First 5 companies cap at 5 links; remaining companies cap at 3 links.
- Sources can be diverse (not limited to major outlets), while spam is reasonably suppressed by scoring.
- If no new items exist, company may be omitted (default).
- When completed and tested successfully, write an implementation guide and put it here: /home/alfred/.openclaw/workspace/TheAlfredReport/
---
