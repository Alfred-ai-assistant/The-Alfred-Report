#!/usr/bin/env python3
"""
Private Market News Skill for The Alfred Report

Fetches news per private company via Brave Search using the structured
query groups defined in private_market_news.yaml. Applies query group weights,
source type weights, per-company limits, and Fresh-Only deduplication.
"""

import json
import os
import re
import sys
import math
import yaml
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from cost_tracker import record as record_cost

BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO_ROOT / "config"
STATE_DIR = REPO_ROOT / "state"
STATE_FILE = STATE_DIR / "private_market_news_seen.json"

# Source domain to type mapping
DOMAIN_TO_SOURCE_TYPE = {
    # News outlets
    "reuters.com": "news",
    "reuters.co.uk": "news",
    "bloomberg.com": "news",
    "bloomberg.co.uk": "news",
    "wsj.com": "news",
    "ft.com": "news",
    "cnbc.com": "news",
    "marketwatch.com": "news",
    "barrons.com": "news",
    "axios.com": "news",
    "techcrunch.com": "news",
    "theinformation.com": "news",
    "businessinsider.com": "news",
    "forbes.com": "news",
    "fortune.com": "news",
    "venturebeat.com": "news",
    "calcalistech.com": "news",
    # Blogs (lower weight)
    "medium.com": "blog",
    "substack.com": "blog",
    "reddit.com": "blog",
    "x.com": "blog",
    "twitter.com": "blog",
}


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


def get_source_type(url: str) -> str:
    """Determine source type (news, web, blog) from URL."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        hostname = hostname.lower().lstrip("www.")
        return DOMAIN_TO_SOURCE_TYPE.get(hostname, "web")
    except Exception:
        return "web"


def canonicalize_url(url: str) -> str:
    """Create a canonical URL for deduplication."""
    try:
        from urllib.parse import urlparse, urlunparse
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
        path = parsed.path.rstrip("/") if parsed.path else ""
        # Strip query params and fragment
        return urlunparse(("https", hostname, path, "", "", ""))
    except Exception:
        return url.lower().rstrip("/")


def fetch_brave_news(query: str, count: int = 10) -> List[Dict]:
    """Fetch news results via Brave Search API."""
    if not BRAVE_API_KEY:
        print(f"[PRIVATE_MARKET] BRAVE_API_KEY not set, skipping: {query[:50]}...")
        return []
    
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
        "mna_confirmed": ["acquires", "acquired", "merger completed", "deal closed", "to acquire", "acquisition", "buys"],
        "mna_rumor": ["in talks", "considering sale", "exploring options", "potential deal", "shopping for buyer"],
        "layoffs": ["layoffs", "cuts jobs", "workforce reduction", "firing", "staff reduction"],
        "product": ["launches", "new product", "unveils", "announces", "releases", "chip", "accelerator"],
        "partnership": ["partnership", "collaboration", "teams up with", "joins forces", "strategic alliance", "contract"],
        "regulatory": ["fda", "investigation", "regulators", "lawsuit", "sued", "fine", "trial"],
        "other": [],
    }
    
    for tag, keywords in patterns.items():
        if any(kw in text for kw in keywords):
            tags.append(tag)
    
    if not tags:
        tags.append("other")
    
    return tags


def compute_score(
    story: Dict,
    query_group: str,
    config: Dict
) -> Tuple[float, str]:
    """Compute weighted score for a story."""
    settings = config.get("settings", {})
    query_weights = settings.get("query_group_weights", {})
    source_weights = settings.get("source_type_weights", {})
    min_score = settings.get("min_score", 0.55)
    
    # Base score from position (higher = better)
    base = 0.7
    
    # Query group weight
    group_weight = query_weights.get(query_group, 1.0)
    
    # Source type weight
    source_type = get_source_type(story.get("url", ""))
    source_weight = source_weights.get(source_type, 1.0)
    
    # Event tags boost
    tags = story.get("tags", [])
    event_boost = 1.0
    if "funding" in tags:
        event_boost = 1.3
    elif "ipo" in tags:
        event_boost = 1.25
    elif "mna_confirmed" in tags:
        event_boost = 1.2
    elif "mna_rumor" in tags:
        event_boost = 1.1
    elif "partnership" in tags:
        event_boost = 1.05
    
    # Freshness decay (older = lower score)
    # 12-hour half-life with much lower floor (0.05) to heavily penalize old news
    now = datetime.now(timezone.utc)
    published = story.get("published_at", now)
    if isinstance(published, str):
        published = datetime.fromisoformat(published.replace('Z', '+00:00'))
    hours_ago = (now - published).total_seconds() / 3600
    freshness = max(0.05, math.exp(-hours_ago / 12))  # 12hr half-life, 0.05 floor
    
    # Final score (0-100 scale)
    raw_score = base * group_weight * source_weight * event_boost * freshness
    final_score = min(100, raw_score * 100)
    
    why = f"group={query_group}({group_weight}) src={source_type}({source_weight}) event={tags[0] if tags else 'other'}({event_boost:.2f}) fresh={freshness:.2f}"
    
    return final_score, why


def process_company(
    company: Dict,
    config: Dict,
    seen_urls: Set[str]
) -> Optional[Dict]:
    """Process a single company and return its stories."""
    name = company.get("name", "")
    if not company.get("enabled", True):
        return None
    
    limit = company.get("limit", 5)
    queries = company.get("queries", {})
    
    print(f"[PRIVATE_MARKET] Processing {name}...")
    
    # Collect results from all query groups
    all_results = []
    
    for group_name, group_queries in queries.items():
        if not isinstance(group_queries, list):
            continue
        for query in group_queries:
            results = fetch_brave_news(query, count=10)
            for r in results:
                r["_query_group"] = group_name
                r["_source_query"] = query
            all_results.extend(results)
    
    if not all_results:
        return None
    
    # Deduplicate by canonical URL
    seen_canonical = set()
    unique_results = []
    for r in all_results:
        if not r.get("url") or not r.get("title"):
            continue
        canonical = canonicalize_url(r["url"])
        if canonical not in seen_canonical:
            seen_canonical.add(canonical)
            r["_canonical_url"] = canonical
            unique_results.append(r)
    
    # Fresh-Only filter
    fresh_results = [r for r in unique_results if r["_canonical_url"] not in seen_urls]
    
    if not fresh_results:
        print(f"[PRIVATE_MARKET] {name}: all stories filtered by Fresh-Only")
        return None
    
    # Normalize and score
    stories = []
    for r in fresh_results:
        published = parse_brave_age(r.get("published", ""))
        tags = tag_story(r["title"], r.get("description", ""))
        
        story = {
            "title": r["title"],
            "url": r["url"],
            "canonical_url": r["_canonical_url"],
            "published_at": published.isoformat(),
            "description": r.get("description", ""),
            "tags": tags,
            "_query_group": r["_query_group"],
        }
        
        score, why = compute_score(story, r["_query_group"], config)
        story["score"] = round(score, 1)
        story["why_ranked"] = why
        stories.append(story)
    
    # Sort by score descending
    stories.sort(key=lambda x: -x["score"])
    
    # Apply per-company limit
    top_stories = stories[:limit]
    
    if not top_stories:
        return None
    
    return {
        "company": name,
        "stories": [
            {
                "score": s["score"],
                "tags": s["tags"],
                "headline": s["title"],
                "source": get_source_type(s["url"]),
                "url": s["url"],
                "published_at": s["published_at"],
                "why_ranked": s["why_ranked"],
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
            result = process_company(company, config, seen_urls)
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
    
    print(f"[PRIVATE_MARKET] Complete: {len(results)} companies with stories")
    
    return {
        "title": "Private Market News",
        "summary": f"News from {len(results)} private companies" if results else "No significant private market news today",
        "companies": results,
        "meta": {
            "generated_at": now.isoformat(),
            "companies_count": len(companies),
            "with_stories": len(results),
        }
    }


if __name__ == "__main__":
    result = get_private_market_news()
    print(json.dumps(result, indent=2))
