#!/usr/bin/env python3
"""
Stock Portfolio News Skill for The Alfred Report

Fetches news per ticker via Brave Search, scores using config-based ranker,
applies Fresh-Only filter (no repeats from yesterday), and returns ranked stories.

Key decisions per Sean:
- Uses Brave Search API (not Google/Yahoo as news sources)
- No AI summaries (cost control)
- Config from stocks.tickers.yaml and stocks.news_ranker.yaml
- State persisted to state/stocks_news_seen.json
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

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).parent))
from cache_util import get_cached, save_cache, hash_data
from cost_tracker import record as record_cost

BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY", "")

# Repo paths
REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO_ROOT / "config"
STATE_DIR = REPO_ROOT / "state"
STATE_FILE = STATE_DIR / "stocks_news_seen.json"

# Source domain mapping (maps known domains to config source keys)
DOMAIN_TO_SOURCE = {
    "reuters.com": "reuters",
    "reuters.co.uk": "reuters",
    "bloomberg.com": "bloomberg",
    "bloomberg.co.uk": "bloomberg",
    "wsj.com": "wsj",
    "ft.com": "ft",
    "cnbc.com": "cnbc",
    "marketwatch.com": "marketwatch",
    "barrons.com": "barrons",
    "seekingalpha.com": "seekingalpha",
    "benzinga.com": "benzinga",
    "reddit.com": "reddit",
    "x.com": "x",
    "twitter.com": "x",
    "finance.yahoo.com": "yahoo",
    "news.google.com": "google",
}


def load_config() -> Tuple[Dict, Dict]:
    """Load ticker list and ranker config from YAML."""
    tickers_path = CONFIG_DIR / "stocks.tickers.yaml"
    ranker_path = CONFIG_DIR / "stocks.news_ranker.yaml"
    
    with open(tickers_path) as f:
        tickers_config = yaml.safe_load(f)
    with open(ranker_path) as f:
        ranker_config = yaml.safe_load(f)
    
    return tickers_config, ranker_config


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


def map_domain_to_source(url: str) -> str:
    """Map a URL to a source key from config."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        hostname = hostname.lower().lstrip("www.")
        return DOMAIN_TO_SOURCE.get(hostname, "unknown")
    except Exception:
        return "unknown"


def canonicalize_url(url: str, strip_params: List[str]) -> str:
    """Create a canonical URL for deduplication/freshness checks."""
    try:
        from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
        parsed = urlparse(url)
        hostname = (parsed.hostname or "").lower()
        path = parsed.path.rstrip("/") if parsed.path else ""
        
        # Strip query params
        if parsed.query:
            qs = parse_qs(parsed.query)
            for param in strip_params:
                qs.pop(param, None)
            query = urlencode(qs, doseq=True)
        else:
            query = ""
        
        # Rebuild without fragment
        return urlunparse(("https", hostname, path, "", query, ""))
    except Exception:
        return url.lower().rstrip("/")


def fetch_brave_news(query: str, count: int = 10) -> List[Dict]:
    """Fetch news results via Brave Search API."""
    if not BRAVE_API_KEY:
        print(f"[STOCK_NEWS] BRAVE_API_KEY not set, skipping query: {query}")
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
                "published": item.get("age", ""),  # Brave returns age string
            })
        
        return results
    except Exception as e:
        print(f"[STOCK_NEWS] Brave Search failed for '{query}': {e}")
        return []


def parse_brave_age(age_str: str) -> datetime:
    """Parse Brave's age string to datetime (approximate)."""
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


def tag_story(title: str, snippet: str, event_weights: Dict) -> List[str]:
    """Apply event tags based on headline + snippet keywords."""
    text = f"{title} {snippet}".lower()
    tags = []
    
    # Keyword patterns for each event type
    patterns = {
        "guidance": ["raises guidance", "cuts outlook", "lowers guidance", "raises outlook", "guidance"],
        "sec_filing": ["8-k", "10-k", "10-q", "sec filing", "files with sec", "sec charges"],
        "earnings": ["earnings", "beats estimates", "misses estimates", "eps", "revenue"],
        "m_and_a_confirmed": ["acquires", "merger completed", "deal closed", "to acquire", "acquisition"],
        "m_and_a_rumor": ["in talks", "considering sale", "exploring options", "potential deal"],
        "regulatory_action": ["doj", "ftc", "export controls", "antitrust", "fine", "settlement with regulators"],
        "probe_or_investigation": ["under investigation", "probe", "investigation launched", "subpoena"],
        "lawsuit": ["lawsuit", "sued", "class action", "settlement"],
        "contract_win": ["wins contract", "secures deal", "awarded contract", "partnership with"],
        "product_launch_major": ["launches", "new product", "unveils"],
        "analyst_change_major": ["upgraded", "downgraded", "price target raised", "price target cut", "initiates coverage"],
        "analyst_reiterate": ["reiterates", "maintains rating", "maintains buy", "maintains hold"],
        "macro": ["fed", "interest rate", "inflation", "gdp", "unemployment", "fomc"],
    }
    
    for tag, keywords in patterns.items():
        if any(kw in text for kw in keywords):
            tags.append(tag)
    
    if not tags:
        tags.append("other")
    
    return tags


def score_story(
    story: Dict,
    source_key: str,
    event_tags: List[str],
    ranker_config: Dict,
    seen_tags_this_ticker: Set[str]
) -> Tuple[float, str]:
    """Score a story using the ranker config. Returns (score, why_ranked)."""
    sources = ranker_config.get("sources", {})
    event_weights = ranker_config.get("event_weights", {})
    freshness_config = ranker_config.get("freshness", {})
    thresholds = ranker_config.get("thresholds", {})
    scoring_weights = ranker_config.get("scoring", {})
    novelty_config = ranker_config.get("novelty", {})
    syndication = ranker_config.get("syndication", {})
    
    # Source score (trust/speed)
    if source_key in sources:
        src = sources[source_key]
        trust = src.get("trust", 40)
        speed = src.get("speed", 50)
        tier = src.get("tier", 3)
    else:
        trust, speed, tier = 40, 50, 3
    
    source_score = 0.7 * trust + 0.3 * speed
    
    # Event score
    max_event = 20  # default "other"
    tag_weights = []
    for tag in event_tags:
        w = event_weights.get(tag, 20)
        tag_weights.append((tag, w))
        if w > max_event:
            max_event = w
    
    # Bonus for additional tags (capped)
    other_tags_sum = sum(w for _, w in sorted(tag_weights, key=lambda x: -x[1])[1:])
    other_tags_capped = min(60, other_tags_sum)
    event_score = max_event + 0.15 * other_tags_capped
    
    # Freshness
    now = datetime.now(timezone.utc)
    published = story.get("published_at", now)
    if isinstance(published, str):
        published = datetime.fromisoformat(published.replace('Z', '+00:00'))
    
    minutes_ago = (now - published).total_seconds() / 60
    half_life = freshness_config.get("half_life_minutes", 720)
    floor = freshness_config.get("floor", 0.15)
    freshness = max(floor, math.exp(-minutes_ago / half_life))
    
    # Base score
    sw = scoring_weights.get("source_weight", 0.45)
    ew = scoring_weights.get("event_weight", 0.40)
    fw = scoring_weights.get("freshness_weight", 0.15)
    
    base_score = sw * source_score + ew * event_score + fw * freshness * 100
    
    # Syndication boost
    unique_sources = story.get("unique_sources", 1)
    confirm_boost = min(
        syndication.get("confirm_boost_cap", 1.0),
        syndication.get("confirm_boost_per_extra_source", 0.15) * (unique_sources - 1)
    ) * 100
    
    tier1_boost = syndication.get("tier1_boost", 0.25) * 100 if tier == 1 else 0
    
    # Novelty penalty
    novelty_penalty = 0
    primary_tag = event_tags[0] if event_tags else "other"
    if primary_tag in seen_tags_this_ticker:
        # Penalize if same tag already seen for this ticker
        novelty_penalty = novelty_config.get("same_tag_penalty_6h", 0.25) * 100
    
    final_score = base_score + confirm_boost + tier1_boost - novelty_penalty
    final_score = max(0, min(100, final_score))
    
    why = f"Event={primary_tag}({max_event}) Source={source_key}({int(source_score)}) Fresh={freshness:.2f}"
    if confirm_boost > 0:
        why += f" Confirm={unique_sources}src"
    if tier1_boost > 0:
        why += " Tier1+"
    if novelty_penalty > 0:
        why += f" Novelty-{int(novelty_penalty)}"
    
    return final_score, why


def process_ticker(
    ticker: Dict,
    ranker_config: Dict,
    seen_state: Dict,
    report_date: str,
    debug: Dict
) -> Optional[Dict]:
    """Process a single ticker and return its stories."""
    symbol = ticker.get("symbol", "")
    if not ticker.get("enabled", True):
        return None
    
    print(f"[STOCK_NEWS] Processing {symbol}...")
    
    # Fetch news via Brave Search
    queries = [f"{symbol} stock news", f"{symbol} company news"]
    raw_results = []
    for query in queries:
        results = fetch_brave_news(query, count=10)
        raw_results.extend(results)
        debug["total_candidates"] += len(results)
    
    if not raw_results:
        return None
    
    # Config values
    strip_params = ranker_config.get("dedupe", {}).get("strip_query_params", [])
    freshness_config = ranker_config.get("freshness", {})
    
    # Normalize and cluster
    clusters = defaultdict(lambda: {
        "titles": [],
        "urls": [],
        "sources": set(),
        "earliest": None,
        "best_url": None,
        "title": ""
    })
    
    for r in raw_results:
        if not r.get("url") or not r.get("title"):
            continue
        
        source_key = map_domain_to_source(r["url"])
        canonical = canonicalize_url(r["url"], strip_params)
        
        # Normalize title for dedupe
        norm_title = re.sub(r'[^\w\s]', '', r["title"].lower())
        norm_title = re.sub(r'\s+', ' ', norm_title).strip()
        
        # Use domain + normalized title as cluster key
        cluster_key = f"{source_key}:{norm_title[:50]}"
        
        published = parse_brave_age(r.get("published", ""))
        
        clusters[cluster_key]["titles"].append(r["title"])
        clusters[cluster_key]["urls"].append((canonical, r["url"]))
        clusters[cluster_key]["sources"].add(source_key)
        clusters[cluster_key]["title"] = r["title"]
        
        if clusters[cluster_key]["earliest"] is None or published < clusters[cluster_key]["earliest"]:
            clusters[cluster_key]["earliest"] = published
    
    # Build final story list from clusters
    stories = []
    for key, cluster in clusters.items():
        # Pick best URL (prefer tier 1 sources, else shortest canonical)
        tier = ranker_config.get("sources", {}).get(list(cluster["sources"])[0] if cluster["sources"] else "unknown", {}).get("tier", 3)
        best_url = cluster["urls"][0][1]  # Default to first
        for canonical, original in cluster["urls"]:
            this_source = map_domain_to_source(original)
            this_tier = ranker_config.get("sources", {}).get(this_source, {}).get("tier", 3)
            if this_tier == 1:
                best_url = original
                break
        
        # Event tagging
        snippet = ""
        tags = tag_story(cluster["title"], snippet, ranker_config.get("event_weights", {}))
        
        stories.append({
            "title": cluster["title"],
            "url": best_url,
            "canonical_url": cluster["urls"][0][0],  # First canonical for freshness check
            "published_at": cluster["earliest"].isoformat() if cluster["earliest"] else datetime.now(timezone.utc).isoformat(),
            "sources": list(cluster["sources"]),
            "unique_sources": len(cluster["sources"]),
            "tags": tags,
        })
    
    # Fresh-Only filter
    fresh_only_config = ranker_config.get("fresh_only", {})
    exclude_count = fresh_only_config.get("exclude_if_seen_in_last_reports", 1)
    
    fresh_stories = []
    seen_urls = set()
    for date_key, date_data in seen_state.items():
        if isinstance(date_data, dict):
            seen_urls.update(date_data.get("urls", []))
    
    for s in stories:
        if s["canonical_url"] not in seen_urls:
            fresh_stories.append(s)
        else:
            debug["removed_fresh_only"] += 1
    
    if not fresh_stories:
        print(f"[STOCK_NEWS] {symbol}: all stories filtered by Fresh-Only")
        return None
    
    # Score stories
    seen_tags = set()
    scored = []
    for s in fresh_stories:
        source_key = s["sources"][0] if s["sources"] else "unknown"
        score, why = score_story(s, source_key, s["tags"], ranker_config, seen_tags)
        s["score"] = round(score, 1)
        s["why_ranked"] = why
        scored.append(s)
        if s["tags"]:
            seen_tags.add(s["tags"][0])
    
    # Sort by score
    scored.sort(key=lambda x: -x["score"])
    
    # Select top and glance
    thresholds = ranker_config.get("thresholds", {})
    top_min = thresholds.get("top_min_score", 55)
    must_include = thresholds.get("must_include_score", 80)
    glance_range = thresholds.get("glance_range", [45, 54])
    max_top = thresholds.get("max_top", 5)
    max_glance = thresholds.get("max_glance", 3)
    
    top_stories = []
    glance_stories = []
    included_urls = []
    
    for s in scored:
        if s["score"] >= must_include:
            top_stories.append(s)
            included_urls.append(s["canonical_url"])
        elif s["score"] >= top_min and len(top_stories) < max_top:
            top_stories.append(s)
            included_urls.append(s["canonical_url"])
        elif glance_range[0] <= s["score"] <= glance_range[1] and len(glance_stories) < max_glance:
            if s["tags"] and s["tags"][0] not in {t["tags"][0] if t["tags"] else "" for t in top_stories}:
                glance_stories.append(s)
                included_urls.append(s["canonical_url"])
    
    if not top_stories and not glance_stories:
        return None
    
    # Build output
    result = {
        "symbol": symbol,
        "top_stories": [
            {
                "score": s["score"],
                "tags": s["tags"],
                "headline": s["title"],
                "source": s["sources"][0] if s["sources"] else "unknown",
                "url": s["url"],
                "published_at": s["published_at"],
                "why_ranked": s["why_ranked"],
            }
            for s in top_stories
        ],
        "glance": [
            {
                "score": s["score"],
                "tags": s["tags"],
                "headline": s["title"],
                "why_ranked": s["why_ranked"],
            }
            for s in glance_stories
        ]
    }
    
    # Return included URLs for state update
    return result, included_urls


def get_portfolio_news() -> Dict:
    """Main entry point for the stock news section."""
    now = datetime.now(timezone.utc)
    report_date = now.strftime("%Y-%m-%d")
    
    print(f"[STOCK_NEWS] Starting portfolio news fetch for {report_date}")
    
    # Load configs
    tickers_config, ranker_config = load_config()
    
    # Load seen state
    seen_state = load_seen_state()
    
    # Debug tracking
    debug = {
        "tickers_processed": 0,
        "total_candidates": 0,
        "removed_fresh_only": 0,
        "state_written": False,
        "report_date": report_date,
    }
    
    # Process each ticker
    tickers = tickers_config.get("tickers", [])
    results = []
    all_included_urls = []
    
    for ticker in tickers:
        try:
            result = process_ticker(ticker, ranker_config, seen_state, report_date, debug)
            if result:
                ticker_data, urls = result
                results.append(ticker_data)
                all_included_urls.extend(urls)
                debug["tickers_processed"] += 1
        except Exception as e:
            print(f"[STOCK_NEWS] Error processing {ticker.get('symbol', '?')}: {e}")
            continue
    
    # Update state with today's URLs
    if all_included_urls:
        if report_date not in seen_state:
            seen_state[report_date] = {"urls": [], "by_ticker": {}}
        
        # Deduplicate
        existing = set(seen_state[report_date].get("urls", []))
        new_urls = [u for u in all_included_urls if u not in existing]
        seen_state[report_date]["urls"].extend(new_urls)
        
        # Cleanup old entries (keep last 30 days)
        cutoff = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        seen_state = {k: v for k, v in seen_state.items() if k >= cutoff}
        
        save_seen_state(seen_state)
        debug["state_written"] = True
        print(f"[STOCK_NEWS] Saved {len(new_urls)} new URLs to state")
    
    print(f"[STOCK_NEWS] Complete: {len(results)} tickers with stories")
    
    return {
        "section": "portfolio_news",
        "title": "Stock Portfolio News",
        "generated_at": now.isoformat(),
        "tickers": results,
        "debug": debug,
    }


if __name__ == "__main__":
    # Test run
    result = get_portfolio_news()
    print(json.dumps(result, indent=2))
