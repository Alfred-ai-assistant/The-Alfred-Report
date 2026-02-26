#!/usr/bin/env python3
"""
Private Market News Skill for The Alfred Report

Simplified version: just company names, 2-day recency cutoff, minimal scoring.
Focus: fresh news about private companies, nothing older than 48 hours.
"""

import json
import os
import re
import sys
import math
import yaml
import urllib.request
import urllib.parse
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

sys.path.insert(0, str(Path(__file__).parent))
from cost_tracker import record as record_cost

BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")
REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO_ROOT / "config"
STATE_DIR = REPO_ROOT / "state"
STATE_FILE = STATE_DIR / "private_market_news_seen.json"


def load_config() -> Dict:
    """Load private market news config from YAML."""
    config_path = CONFIG_DIR / "private_market_news.yaml"
    with open(config_path) as f:
        data = yaml.safe_load(f)
    return data.get("private_market_news", {})


def load_seen_state() -> Dict:
    """Load the 'seen URLs' state file."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if not STATE_FILE.exists():
        return {}
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_seen_state(state: Dict):
    """Save the 'seen URLs' state file."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    tmp.replace(STATE_FILE)


def canonicalize_url(url: str) -> str:
    """Create a canonical URL for deduplication."""
    try:
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
        path = parsed.path.rstrip("/") if parsed.path else ""
        return urlunparse(("https", hostname, path, "", "", ""))
    except Exception:
        return url.lower().rstrip("/")


def fetch_brave_news(query: str, count: int = 20) -> List[Dict]:
    """Fetch news results via Brave Search API."""
    if not BRAVE_API_KEY:
        print(f"[PRIVATE_MARKET] BRAVE_API_KEY not set")
        return []
    
    # Throttle to avoid rate limiting
    time.sleep(0.5)
    
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://api.search.brave.com/res/v1/news/search?q={encoded_query}&count={count}&freshness=day"
        
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": BRAVE_API_KEY
            }
        )
        
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        
        results = []
        for item in data.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("description", ""),
                "published": item.get("age", ""),
            })
        
        return results
    except Exception as e:
        print(f"[PRIVATE_MARKET] Brave Search failed: {e}")
        return []


def parse_brave_age(age_str: str) -> datetime:
    """Parse Brave's age string to datetime."""
    now = datetime.now(timezone.utc)
    if not age_str:
        return now
    
    age_str = age_str.lower().strip()
    try:
        if "minute" in age_str or "min" in age_str:
            m = re.search(r'(\d+)', age_str)
            if m:
                return now - timedelta(minutes=int(m.group(1)))
        elif "hour" in age_str or "hr" in age_str:
            m = re.search(r'(\d+)', age_str)
            if m:
                return now - timedelta(hours=int(m.group(1)))
        elif "day" in age_str:
            m = re.search(r'(\d+)', age_str)
            if m:
                return now - timedelta(days=int(m.group(1)))
        elif "week" in age_str:
            m = re.search(r'(\d+)', age_str)
            if m:
                return now - timedelta(weeks=int(m.group(1)))
    except Exception:
        pass
    
    return now


def tag_story(title: str, description: str) -> List[str]:
    """Apply event tags based on headline + description."""
    text = f"{title} {description}".lower()
    tags = []
    
    patterns = {
        "funding": ["raises", "funding", "series", "valuation", "unicorn", "investment", "investors", "led by", "backed by", "million", "billion"],
        "ipo": ["ipo", "going public", "public offering", "spac", "listing", "debut", "files to go public"],
        "mna": ["acquires", "acquired", "merger", "deal closed", "to acquire", "acquisition", "buys"],
        "partnership": ["partnership", "collaboration", "teams up", "joins forces", "strategic", "contract"],
        "product": ["launches", "new product", "unveils", "announces", "releases", "chip", "inference"],
        "other": [],
    }
    
    for tag, keywords in patterns.items():
        if any(kw in text for kw in keywords):
            tags.append(tag)
    
    if not tags:
        tags.append("other")
    
    return tags


def process_company(
    company: Dict,
    config: Dict,
    seen_urls: Set[str],
    max_age_hours: int
) -> Optional[Dict]:
    """Process a single company and return its stories."""
    name = company.get("name", "")
    if not company.get("enabled", True):
        return None
    
    limit = company.get("limit", 5)
    
    print(f"[PRIVATE_MARKET] Processing {name}...")
    
    # Simple search: just the company name
    results = fetch_brave_news(f'"{name}"', count=20)
    
    if not results:
        return None
    
    # Deduplicate by canonical URL
    seen_canonical = set()
    unique_results = []
    for r in results:
        if not r.get("url") or not r.get("title"):
            continue
        canonical = canonicalize_url(r["url"])
        if canonical not in seen_canonical:
            seen_canonical.add(canonical)
            r["_canonical_url"] = canonical
            unique_results.append(r)
    
    # Filter by recency (last 48 hours)
    now = datetime.now(timezone.utc)
    fresh_results = []
    for r in unique_results:
        published = parse_brave_age(r.get("published", ""))
        hours_old = (now - published).total_seconds() / 3600
        
        # Only include stories from last 2 days
        if hours_old <= max_age_hours:
            r["_published"] = published
            r["_hours_old"] = hours_old
            fresh_results.append(r)
    
    if not fresh_results:
        print(f"[PRIVATE_MARKET] {name}: no stories from last {max_age_hours} hours")
        return None
    
    # Fresh-Only filter (don't repeat yesterday's stories)
    deduped_results = [r for r in fresh_results if r["_canonical_url"] not in seen_urls]
    
    if not deduped_results:
        print(f"[PRIVATE_MARKET] {name}: all recent stories already shown yesterday")
        return None
    
    # Score and tag
    stories = []
    for r in deduped_results:
        tags = tag_story(r["title"], r.get("description", ""))
        
        # Simple score: heavy recency weight
        hours_old = r["_hours_old"]
        freshness = max(0.1, math.exp(-hours_old / 6))  # 6hr half-life
        base_score = 70 * freshness
        
        # Tiny boost for high-value events
        event_boost = 1.0
        if "funding" in tags or "ipo" in tags:
            event_boost = 1.15
        
        final_score = min(100, base_score * event_boost)
        
        story = {
            "score": round(final_score, 1),
            "headline": r["title"],
            "url": r["url"],
            "published_at": r["_published"].isoformat(),
            "tags": tags,
            "hours_old": round(hours_old, 1),
            "canonical_url": r["_canonical_url"],
        }
        stories.append(story)
    
    # Sort by score, take top N
    stories.sort(key=lambda x: -x["score"])
    top_stories = stories[:limit]
    
    if not top_stories:
        return None
    
    return {
        "company": name,
        "stories": [
            {
                "score": s["score"],
                "headline": s["headline"],
                "url": s["url"],
                "published_at": s["published_at"],
                "tags": s["tags"],
            }
            for s in top_stories
        ],
        "_included_urls": [s["canonical_url"] for s in top_stories]
    }


def get_private_market_news() -> Dict:
    """Entry point for private market news section."""
    now = datetime.now(timezone.utc)
    report_date = now.strftime("%Y-%m-%d")
    
    print(f"[PRIVATE_MARKET] Starting private market news fetch for {report_date}")
    
    config = load_config()
    settings = config.get("settings", {})
    companies = config.get("companies", [])
    max_age_hours = settings.get("max_story_age_hours", 48)
    
    # Load seen state
    seen_state = load_seen_state()
    dedupe_days = settings.get("dedupe_days", 1)
    
    # Build set of seen URLs from recent days
    seen_urls = set()
    cutoff = (now - timedelta(days=dedupe_days)).strftime("%Y-%m-%d")
    for date_key, date_data in seen_state.items():
        if date_key >= cutoff and isinstance(date_data, dict):
            seen_urls.update(date_data.get("urls", []))
    
    # Process each company
    results = []
    all_included_urls = []
    
    for company in companies:
        try:
            result = process_company(company, config, seen_urls, max_age_hours)
            if result:
                urls = result.pop("_included_urls", [])
                results.append(result)
                all_included_urls.extend(urls)
        except Exception as e:
            print(f"[PRIVATE_MARKET] Error processing {company.get('name', '?')}: {e}")
            continue
    
    # Update state with today's URLs
    if all_included_urls:
        if report_date not in seen_state:
            seen_state[report_date] = {"urls": []}
        
        existing = set(seen_state[report_date].get("urls", []))
        new_urls = [u for u in all_included_urls if u not in existing]
        seen_state[report_date]["urls"].extend(new_urls)
        
        # Cleanup old entries (keep last 30 days)
        cutoff_30 = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        seen_state = {k: v for k, v in seen_state.items() if k >= cutoff_30}
        
        save_seen_state(seen_state)
        print(f"[PRIVATE_MARKET] Saved {len(new_urls)} new URLs to state")
    
    print(f"[PRIVATE_MARKET] Complete: {len(results)} companies with recent stories")
    
    return {
        "title": "Private Market News",
        "summary": f"News from {len(results)} private companies (last 48 hours)" if results else "No private market news in last 48 hours",
        "companies": results,
        "meta": {
            "generated_at": now.isoformat(),
            "companies_tracked": len(companies),
            "with_recent_stories": len(results),
        }
    }


if __name__ == "__main__":
    result = get_private_market_news()
    print(json.dumps(result, indent=2))
