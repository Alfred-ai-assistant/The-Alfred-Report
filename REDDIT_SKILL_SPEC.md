Reddit Integration Skill Specification

The Alfred Report

Overview

This document defines the Reddit integration for The Alfred Report.

The Reddit skill has two core capabilities:
	1.	AI Reddit Trending — Daily trending AI-related posts
	2.	Company Reddit Watch — Daily company-specific post monitoring with topic tagging

This integration must be deterministic, API-driven, and safe.
No scraping. Official Reddit API only. Read-only access.

Infrastructure must not change when expanding logic.

⸻

Authentication

Use official Reddit OAuth (script-type app).

Required credentials:
	•	client_id
	•	client_secret
	•	username
	•	password
	•	user_agent

Scopes:
	•	read only

No write permissions.
No moderation permissions.
No voting or posting.

Credentials must be stored in AWS Secrets Manager.
Never log secrets.

⸻

Capability 1: AI Reddit Trending

Objective

Generate a daily list of the most relevant AI-related Reddit posts from the last 24 hours.

This feeds:

sections.ai_reddit_trending

Subreddit Sources

A configurable list in a file for specifics:

config/reddit_ai_sources.json

These should include AI-focused subreddits and related high-signal communities.

The list must be configurable and versioned in Git.

Data Retrieval

For each subreddit:
	•	Pull listings from new
	•	Optionally pull from hot
	•	Limit candidate size (for example 50–200 posts)
	•	Filter to posts created in last 24 hours

Exclude:
	•	Stickied posts
	•	Removed/deleted posts
	•	NSFW (optional rule)
	•	Off-topic posts

Relevance Filter

Post must match AI-related keywords such as:
AI, artificial intelligence, LLM, transformer, inference, training, fine-tune, agent, model release, OpenAI, Anthropic, Claude, Gemini, Llama, NVIDIA, CUDA, GPU.

Filtering should be deterministic.

Optional lightweight classifier only when ambiguous.

Ranking

Score posts using:
	•	Engagement score (score + comments, log-scaled)
	•	Recency boost (within 24 hours)
	•	Subreddit quality weight (optional)
	•	Authority boost if linking to primary source

Deduplicate by:
	•	Canonical external URL
	•	Title similarity

Select top 15

Output Structure

sections.ai_reddit_trending must include:
	•	title
	•	summary (optional narrative)
	•	items (ranked array)

Each item includes:
	•	title
	•	url
	•	permalink
	•	subreddit
	•	score
	•	num_comments
	•	created_utc
	•	tags (optional)

Optional:
	•	One short narrative paragraph grounded only in selected posts.

⸻

Capability 2: Company Reddit Watch

Objective

For each configured company, run a daily query and return relevant Reddit posts from the last 24 hours, tagged with metadata.

This feeds:

sections.company_reddit_watch

Source of Truth

Companies are defined in:

config/reddit_company_watch.json

This file acts as the “table Alfred remembers.”

Each company record contains:
	•	company_name
	•	ticker (optional)
	•	aliases
	•	keywords
	•	topics
	•	subreddit_scopes
	•	enabled

Alfred must read this file every run.
No hardcoding of companies in logic.

Retrieval Logic

For each enabled company:

Construct a query using:
	•	company_name
	•	ticker (if non-ambiguous)
	•	aliases
	•	keywords

Search within:
	•	subreddit_scopes if provided
	•	otherwise default finance/tech subreddits

Filter to last 24 hours.

Exclude low-signal or removed posts.

Topic Tagging

Each matched post must include:
	•	matched_terms (which keywords matched)
	•	topics (array of topic labels)
	•	topic_confidence (high, medium, low)

Topic taxonomy examples:
	•	ipo_private_markets
	•	earnings_financials
	•	partnership
	•	acquisition_mna
	•	regulation_policy
	•	security_privacy
	•	competitive_landscape
	•	hardware_infra
	•	product_release
	•	rumors_speculation

Tagging method:
	1.	Deterministic keyword rules first
	2.	Optional small LLM classification call for ambiguous posts

Do not use LLM to search Reddit.

Output Structure

sections.company_reddit_watch must include:
	•	title
	•	summary (optional cross-company overview)
	•	generated_from
	•	companies (array)
	•	meta

Each company entry must include:
	•	company_name
	•	ticker
	•	keywords
	•	topics_of_interest
	•	subreddit_scopes
	•	query
	•	items (array of posts)
	•	company_summary (optional)
	•	meta

Each post item must include:
	•	title
	•	url
	•	permalink
	•	subreddit
	•	created_utc
	•	score
	•	num_comments
	•	domain
	•	matched_terms
	•	topics
	•	topic_confidence

If no posts found:
	•	items must be empty array
	•	company_summary must be null

Select top 10 scoring posts.

No hallucinated data.

⸻

Cost Control Rules

Do NOT:
	•	Use LLM for searching
	•	Use LLM for ranking
	•	Pull entire comment trees
	•	Scrape HTML

Use LLM only for:
	•	Optional summary paragraphs
	•	Optional ambiguous topic classification

One bounded LLM call per section maximum.

⸻

Operational Flow (Daily)

At 07:00 EST:
	1.	Read company config file
	2.	Pull Reddit data
	3.	Normalize posts
	4.	Rank and dedupe
	5.	Tag topics
	6.	Construct sections.ai_reddit_trending
	7.	Construct sections.company_reddit_watch
	8.	Write JSON into report payload
	9.	Publisher commits and pushes

Infrastructure remains unchanged.
