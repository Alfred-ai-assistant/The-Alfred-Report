#!/usr/bin/env python3
"""
Reddit Skill for The Alfred Report

Two sections:
1. AI Reddit Trending — top AI posts from configured subreddits
2. Company Reddit Watch — company-specific posts with topic tagging

Uses Brave Search only (no Reddit API). Deterministic keyword matching.
One cheap haiku call for summaries.
"""

import os
import json
import yaml
import urllib.request
import urllib.parse
import re
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List
from collections import defaultdict

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).parent))
from cache_util import get_cached, save_cache, hash_data

BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

# Config files
REPO_ROOT = "/home/alfred/repos/The-Alfred-Report"
CONFIG_AI_SOURCES = f"{REPO_ROOT}/config/reddit_ai_sources.yaml"
CONFIG_COMPANY_WATCH = f"{REPO_ROOT}/config/reddit_company_watch.yaml"

# ── Brave Search ──────────────────────────────────────────────────────────────

def brave_search(query: str, count: int = 10) -> List[Dict]:
    """Run a Brave Search query, return web results."""
    if not BRAVE_API_KEY:
        return []

    params = urllib.parse.urlencode({
        "q":     query,
        "count": count,
    })
    url = f"https://api.search.brave.com/res/v1/web/search?{params}"
    headers = {
        "Accept":              "application/json",
        "X-Subscription-Token": BRAVE_API_KEY,
    }

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
        return data.get("web", {}).get("results", [])
    except Exception:
        return []

# ── AI Reddit Trending ─────────────────────────────────────────────────────────

def get_ai_reddit_trending() -> Dict:
    """Fetch top AI posts from configured subreddits via Brave Search."""
    
    try:
        with open(CONFIG_AI_SOURCES) as f:
            config = yaml.safe_load(f)
    except Exception as e:
        return {
            "title": "AI on Reddit",
            "summary": f"Failed to load config: {e}",
            "items": [],
            "meta": {"error": str(e)[:200]}
        }

    ai_sources = config.get("ai_daily_sources", [])
    enabled_sources = [s for s in ai_sources if s.get("enabled", True)]

    candidates = []
    ai_keywords = ["AI", "LLM", "machine learning", "model", "inference", "training", "agent", 
                   "OpenAI", "Anthropic", "Claude", "Gemini", "Llama", "NVIDIA", "neural"]

    # Query each subreddit
    for source in enabled_sources:
        subreddit = source["subreddit"]
        weight = source.get("weight", 1.0)

        query = f"site:reddit.com/r/{subreddit} (AI OR LLM OR 'machine learning' OR model OR inference OR training)"
        results = brave_search(query, count=20)  # Request more to account for filtering

        for r in results:
            url = r.get("url", "")
            title = r.get("title", "")

            # Must be a reddit post URL
            if "reddit.com/r/" not in url or "/comments/" not in url:
                continue

            # Must match AI intent
            matched = [kw for kw in ai_keywords if kw.lower() in (title + " " + r.get("description", "")).lower()]
            if not matched:
                continue

            candidates.append({
                "title": title,
                "url": url,
                "subreddit": subreddit,
                "source": "reddit",
                "matched_terms": matched,
                "weight": weight,
                "snippet": r.get("description", ""),
            })

    # Deduplicate by URL
    seen_urls = set()
    deduplicated = []
    for c in candidates:
        if c["url"] not in seen_urls:
            seen_urls.add(c["url"])
            deduplicated.append(c)

    # Score and rank
    def score(c):
        score = 0.0
        score += c["weight"] * 10  # Subreddit weight
        score += len(c["matched_terms"]) * 2  # Keyword matches
        return score

    ranked = sorted(deduplicated, key=score, reverse=True)[:15]

    items = [
        {
            "title": r["title"],
            "url": r["url"],
            "subreddit": r["subreddit"],
            "source": r["source"],
            "matched_terms": r["matched_terms"],
        }
        for r in ranked
    ]

    summary = f"Found {len(items)} top AI posts from {len(enabled_sources)} subreddits"

    return {
        "title": "AI on Reddit",
        "summary": summary,
        "items": items,
        "meta": {
            "source": "brave_search",
            "subreddits_searched": len(enabled_sources),
            "posts_found": len(items),
            "timeframe_hours": 24,
        }
    }

# ── Company Reddit Watch ───────────────────────────────────────────────────────

def get_company_reddit_watch() -> Dict:
    """Monitor Reddit for company-specific mentions with topic tagging."""
    
    try:
        with open(CONFIG_COMPANY_WATCH) as f:
            config = yaml.safe_load(f)
    except Exception as e:
        return {
            "title": "Company Reddit Watch",
            "summary": f"Failed to load config: {e}",
            "items": [],
            "meta": {"error": str(e)[:200]}
        }

    companies = config.get("companies", [])
    enabled_companies = [c for c in companies if c.get("enabled", True)]

    results = {
        "title": "Company Reddit Watch",
        "summary": "",
        "companies": [],
        "generated_from": {
            "source": "brave_search",
            "timeframe_hours": 24,
            "run_at": datetime.now(timezone.utc).isoformat(),
        },
        "meta": {
            "companies_tracked": len(enabled_companies),
            "total_posts": 0,
        }
    }

    for company in enabled_companies:
        name = company["company_name"]
        ticker = company.get("ticker")
        aliases = company.get("aliases", [])
        keywords = company.get("keywords", [])
        topics = company.get("topics", [])
        scopes = company.get("subreddit_scopes", ["technology", "stocks", "investing"])

        # Build search query
        terms = [name] + aliases
        query_terms = " OR ".join(f'"{t}"' for t in terms)
        scope_query = " OR ".join(f"site:reddit.com/r/{s}" for s in scopes)

        query = f"({scope_query}) ({query_terms})"
        search_results = brave_search(query, count=15)

        company_items = []
        for sr in search_results:
            url = sr.get("url", "")
            title = sr.get("title", "")
            snippet = sr.get("description", "")

            # Must be a reddit post
            if "reddit.com/r/" not in url or "/comments/" not in url:
                continue

            # Match company/aliases
            full_text = (title + " " + snippet).lower()
            matched_terms = []
            for term in aliases + [name]:
                if term.lower() in full_text:
                    matched_terms.append(term)

            if not matched_terms and ticker:
                # Check ticker with confirming keyword
                if ticker.lower() in full_text:
                    confirming = [kw for kw in keywords if kw.lower() in full_text]
                    if confirming:
                        matched_terms.append(ticker)

            if not matched_terms:
                continue

            # Deterministic topic tagging
            matched_topics = []
            topic_confidence = "low"
            for topic in topics:
                # Check if any keyword for this topic appears
                if any(kw.lower() in full_text for kw in keywords):
                    matched_topics.append(topic)
            
            if matched_terms:
                topic_confidence = "high" if len(matched_terms) > 1 else "medium"

            company_items.append({
                "title": title,
                "url": url,
                "subreddit": url.split("/r/")[1].split("/")[0] if "/r/" in url else None,
                "source": "reddit",
                "matched_terms": matched_terms,
                "topics": matched_topics[:3],  # Top 3
                "topic_confidence": topic_confidence,
            })

        # Deduplicate and limit
        seen = set()
        deduped = []
        for item in company_items:
            if item["url"] not in seen:
                seen.add(item["url"])
                deduped.append(item)
        
        final_items = deduped[:10]

        company_entry = {
            "company_name": name,
            "ticker": ticker,
            "keywords": keywords[:5],  # Echo top keywords
            "topics_of_interest": topics,
            "subreddit_scopes": scopes,
            "query": query,
            "items": final_items,
            "company_summary": None,  # Will be filled by LLM
            "meta": {
                "posts_found": len(final_items),
                "posts_included": len(final_items),
                "top_topics": list(set(t for item in final_items for t in item["topics"]))[:3],
            }
        }

        results["companies"].append(company_entry)
        results["meta"]["total_posts"] += len(final_items)

    return results

# ── LLM Summaries ─────────────────────────────────────────────────────────────

def add_summaries(ai_trending: Dict, company_watch: Dict) -> tuple:
    """One bounded haiku call to generate summaries for both sections.
    Uses cache to avoid re-running on same data."""
    
    if not ANTHROPIC_KEY:
        return ai_trending, company_watch
    
    # Check cache first
    today = datetime.now(timezone.utc).date().isoformat()
    source_data = {
        "ai_urls": [item["url"] for item in ai_trending.get("items", [])],
        "company_urls": [item["url"] for c in company_watch.get("companies", []) for item in c.get("items", [])]
    }
    
    cached = get_cached("reddit_summaries", today, source_data)
    if cached:
        ai_trending["summary"] = cached.get("ai_reddit_summary", ai_trending["summary"])
        company_watch["summary"] = cached.get("company_watch_summary", company_watch.get("summary", ""))
        return ai_trending, company_watch

    # Build a compact prompt for both sections
    ai_count = len(ai_trending.get("items", []))
    company_count = company_watch.get("meta", {}).get("total_posts", 0)
    
    prompt = f"""Write two brief summaries (50–100 words each) for a daily report:

1. AI on Reddit ({ai_count} top posts found): summarize themes, trending topics, communities
2. Company Reddit Watch ({company_count} posts across companies): summarize which companies are getting mentions, what topics dominate

Return JSON with keys: "ai_reddit_summary", "company_watch_summary"
Return ONLY the JSON object. No markdown."""

    body = json.dumps({
        "model": "claude-haiku-4-5",
        "max_tokens": 500,
        "messages": [{"role": "user", "content": prompt}]
    }).encode()

    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            headers={
                "x-api-key":         ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
                "content-type":      "application/json",
                "accept-encoding":   "identity",
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            resp = json.loads(r.read())
        
        raw_text = resp["content"][0]["text"]
        
        # Strip markdown code blocks if present
        if raw_text.startswith("```"):
            raw_text = re.sub(r'^```json?\n', '', raw_text)
            raw_text = re.sub(r'\n```$', '', raw_text)
        
        summaries = json.loads(raw_text)
        
        ai_trending["summary"] = summaries.get("ai_reddit_summary", ai_trending["summary"])
        company_watch["summary"] = summaries.get("company_watch_summary", "")
        
        # Save to cache
        save_cache("reddit_summaries", today, source_data, summaries)
        
        return ai_trending, company_watch

    except Exception as e:
        return ai_trending, company_watch

# ── Main Entry ────────────────────────────────────────────────────────────────

def get_reddit_sections() -> tuple:
    """Return both (ai_trending, company_watch) sections."""
    ai_trending = get_ai_reddit_trending()
    company_watch = get_company_reddit_watch()
    
    # Add LLM summaries (one cheap call for both)
    ai_trending, company_watch = add_summaries(ai_trending, company_watch)
    
    return ai_trending, company_watch


if __name__ == "__main__":
    ai, cw = get_reddit_sections()
    print(json.dumps({"ai_reddit_trending": ai, "company_reddit_watch": cw}, indent=2))
