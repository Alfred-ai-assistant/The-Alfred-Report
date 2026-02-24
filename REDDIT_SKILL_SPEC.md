REDDIT_SKILL_SPEC.md

Reddit (via Brave Search) Skill Specification
For The Alfred Report

Overview
Reddit Data API access is gated and unreliable for external non-Devvit apps. For The Alfred Report, Alfred will discover Reddit posts using the Brave Web Search API and produce two report sections:
	1.	AI Reddit Trending: generic daily trending AI-related posts
	2.	Company Reddit Watch: daily company-specific monitoring using a configurable “company table” with keywords/topics

This design requires no Reddit API keys.

Inputs and Config Files (YAML)
Alfred must read these config files on every run:

A) config/reddit_ai_sources.yaml
Contains ai_daily_sources, a list of subreddits to scan for AI trending content. Each entry includes: subreddit, weight, enabled.

B) config/reddit_company_watch.yaml
Contains companies, a list of tracked companies. Each entry includes: company_name, ticker, aliases, keywords, topics, subreddit_scopes, enabled.

These YAML files are the single source of truth. Alfred does not “remember” companies or sources in memory. It reads YAML every run.

General Retrieval Rule
All Reddit discovery is done via Brave Search queries constrained to reddit.com URLs. Alfred must not scrape at scale. Alfred may optionally enrich only the final selected posts later.

Time Window
Default window is the last 24 hours, rolling. If Brave returns an item slightly older but clearly still dominating current discussion, Alfred may include it only if it is strongly relevant and there are not enough high-quality fresh items.

Canonical URL Rule
Alfred must normalize Reddit URLs to a canonical post URL (permalink form) for deduplication and stable output. Prefer the actual post URL, not just a search result redirect.

Capability 1: AI Reddit Trending
Objective
Create a daily list of the best AI-related Reddit posts from the last 24 hours using the subreddits defined in config/reddit_ai_sources.yaml.

Report Section Key
sections.ai_reddit_trending

Retrieval
For each enabled subreddit in ai_daily_sources:

Run Brave Search queries that target that subreddit path. Conceptually:
	•	site:reddit.com/r/SUBREDDIT (AI OR LLM OR “machine learning” OR model OR inference OR training OR agent OR OpenAI OR Anthropic OR Claude OR Gemini OR Llama OR NVIDIA)

Alfred should keep the number of queries bounded per subreddit (small), and cache results within the run.

Filtering
Keep candidates that:
	•	Are Reddit post URLs within that subreddit path
	•	Are likely within the last 24 hours (best available signal)
	•	Match AI intent based on title/snippet keyword rules

Exclude candidates that are clearly:
	•	Weekly megathreads / stickies (when identifiable)
	•	Off-topic based on title/snippet
	•	Duplicate URLs

Deduplication
Deduplicate by:
	•	Canonical URL (exact match)
	•	If necessary: near-duplicate title similarity within same subreddit

Ranking
Rank candidates with a deterministic score using:
	•	Recency (strong weight)
	•	Keyword match strength (medium)
	•	Subreddit weight from YAML (multiplier)
Optional later: engagement enrichment if you add it.

Select top N (default 15; allow fewer if not enough quality posts).

Output
sections.ai_reddit_trending must include:
	•	title: “AI on Reddit” (or similar)
	•	summary: short narrative (optional initially)
	•	items: ranked array

Each item includes at minimum:
	•	title
	•	url (canonical post URL)
	•	subreddit
	•	created_at: ISO or null if unknown
	•	source: “reddit”
	•	matched_terms: optional list of matched keywords
	•	weight: optional (subreddit weight used)

Engagement fields (score/comments) are optional until enrichment exists.

Capability 2: Company Reddit Watch
Objective
For each enabled company in config/reddit_company_watch.yaml, discover and return posts from the last 24 hours that match the company plus company-specific keywords/topics. Alfred also tags each post with topics based on configured interest areas.

Report Section Key
sections.company_reddit_watch

Retrieval
For each enabled company:

Build a query using:
	•	company_name
	•	aliases
	•	keywords
	•	ticker only if it’s safe (tickers can be ambiguous; if used, require confirming terms)

Scope:
	•	If subreddit_scopes is provided, constrain queries to those subreddits first.
	•	If subreddit_scopes is empty/missing, fall back to a default list (tech + finance subs).

Conceptual query pattern:
	•	site:reddit.com/r/SUBREDDIT (“CompanyName” OR alias1 OR alias2) (keyword1 OR keyword2 OR keyword3)

Filtering
A post is relevant if:
	•	company_name or an alias appears in title/snippet, OR
	•	ticker appears AND at least one confirming keyword/alias appears

Filter to last 24 hours using best available signal.

Topic Tagging
Alfred must apply topic tagging based on the company’s configured topics and keywords.

Required outputs per post:
	•	matched_terms: which aliases/keywords matched
	•	topics: list of topic tags (from the configured topics list; derived deterministically)
	•	topic_confidence: high/medium/low

Topic tagging rules:
	•	First pass must be deterministic keyword mapping (stable and explainable).
	•	Optional later: a small LLM classification call only for ambiguous items, restricted to choosing from the allowed topics for that company. No freeform.

Ranking per Company
Sort by:
	1.	match strength (more/stronger matched terms)
	2.	recency
	3.	optional engagement if added later

Cap results per company (default 10).

Output
sections.company_reddit_watch must include:
	•	title: “Company Reddit Watch”
	•	summary: optional cross-company overview
	•	generated_from:
	•	timeframe_hours: 24
	•	run_at: ISO timestamp
	•	source: “brave_search”
	•	companies: array
	•	meta: counts

Each company entry must include:
	•	company_name
	•	ticker
	•	keywords (echo from YAML)
	•	topics_of_interest (echo from YAML topics)
	•	subreddit_scopes (actual used)
	•	query (final assembled query string)
	•	items: array
	•	company_summary: optional, else null
	•	meta:
	•	posts_found
	•	posts_included
	•	top_topics

Each post item must include:
	•	title
	•	url (canonical post URL)
	•	subreddit: string or null
	•	created_at: ISO or null
	•	matched_terms: array
	•	topics: array
	•	topic_confidence: high/medium/low
Optional later: score/num_comments if enriched.

Failure Behavior
If Brave returns too few results:
	•	AI trending: output fewer items (minimum acceptable 5–8)
	•	Company watch: output empty items for that company; company_summary null

If Brave fails entirely:
	•	Sections exist but items arrays are empty and summary explains “Unable to retrieve Reddit results today.”

Cost Control
Do not use LLM to search. Do not fetch full pages for all candidates.
Bound Brave queries and optionally enrich only final selected posts.
LLM usage is optional and should be small and bounded.

End of Spec
