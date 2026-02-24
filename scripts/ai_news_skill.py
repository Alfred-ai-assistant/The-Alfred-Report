#!/usr/bin/env python3
"""
AI News Skill for The Alfred Report

Multi-lane data collection:
  Lane 1: Hacker News top/best stories (with score + comment signals)
  Lane 2: Brave Search → Tier-1 AI publications
  Lane 3: Brave Search → Primary source announcements (OpenAI, Anthropic, etc.)
  Lane 4: arXiv RSS (cs.AI, cs.LG, stat.ML) — selective only

One bounded LLM call at the end to:
  - Write the why_it_matters for each story (from snippet only)
  - Write the narrative summary paragraph

No hallucination. Do not invent metadata.
"""

import os
import json
import gzip
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import time
import re
import sys
from pathlib import Path

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).parent))
from cache_util import get_cached, save_cache, hash_data

# ── Config ────────────────────────────────────────────────────────────────────

BRAVE_API_KEY   = os.environ.get("BRAVE_API_KEY", "")
ANTHROPIC_KEY   = os.environ.get("ANTHROPIC_API_KEY", "")

AI_KEYWORDS = [
    "AI", "artificial intelligence", "LLM", "large language model",
    "OpenAI", "Anthropic", "Gemini", "Claude", "Llama",
    "inference", "training", "GPU", "foundation model", "generative AI",
    "machine learning", "neural network", "GPT", "ChatGPT",
    "DeepMind", "Meta AI", "NVIDIA AI", "Hugging Face"
]

AI_KW_PATTERN = re.compile(
    r'\b(' + '|'.join(re.escape(k) for k in AI_KEYWORDS) + r')\b',
    re.IGNORECASE
)

TIER1_SOURCES = [
    ("techcrunch.com", "TechCrunch", 80),
    ("theverge.com", "The Verge", 80),
    ("venturebeat.com", "VentureBeat", 80),
    ("arstechnica.com", "Ars Technica", 80),
    ("technologyreview.mit.edu", "MIT Technology Review", 90),
    ("ft.com", "Financial Times", 90),
    ("bloomberg.com", "Bloomberg", 90),
    ("reuters.com", "Reuters", 90),
    ("wired.com", "Wired", 70),
]

PRIMARY_SOURCES = [
    ("openai.com/blog", "OpenAI", 100),
    ("anthropic.com/news", "Anthropic", 100),
    ("deepmind.google", "Google DeepMind", 100),
    ("ai.meta.com", "Meta AI", 100),
    ("blogs.microsoft.com", "Microsoft AI", 95),
    ("developer.apple.com/news", "Apple ML", 95),
    ("research.google", "Google Research", 95),
    ("nvidianews.nvidia.com", "NVIDIA", 95),
    ("huggingface.co/blog", "Hugging Face", 90),
]

NOW_UTC = datetime.now(timezone.utc)
CUTOFF  = NOW_UTC - timedelta(hours=36)   # slight buffer beyond 24h

# ── HTTP helper ───────────────────────────────────────────────────────────────

def http_get(url: str, headers: dict = {}, timeout: int = 10) -> Optional[bytes]:
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
            if r.headers.get("Content-Encoding") == "gzip" or (data[:2] == b'\x1f\x8b'):
                data = gzip.decompress(data)
            return data
    except Exception:
        return None

# ── Lane 1: Hacker News ───────────────────────────────────────────────────────

def collect_hn_stories(max_check: int = 300) -> List[Dict]:
    raw = http_get("https://hacker-news.firebaseio.com/v0/beststories.json")
    if not raw:
        raw = http_get("https://hacker-news.firebaseio.com/v0/topstories.json")
    if not raw:
        return []

    ids = json.loads(raw)[:max_check]
    stories = []

    for sid in ids:
        data = http_get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json")
        if not data:
            continue
        item = json.loads(data)

        # Must have a URL (not Ask HN etc.)
        url = item.get("url", "")
        title = item.get("title", "")
        if not url or not title:
            continue

        # Must match AI keywords
        if not AI_KW_PATTERN.search(title):
            continue

        # Recency check
        ts = item.get("time", 0)
        published = datetime.fromtimestamp(ts, tz=timezone.utc)
        if published < CUTOFF:
            continue

        score   = item.get("score", 0)
        comments = item.get("descendants", 0)

        stories.append({
            "title":        title,
            "url":          url,
            "source":       urllib.parse.urlparse(url).netloc.replace("www.", ""),
            "published_at": published.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "snippet":      "",
            "hn_score":     score,
            "hn_comments":  comments,
            "authority":    50,   # default; will be upgraded if matches tier-1
            "lane":         "hn",
        })

    return stories

# ── Brave Search helper ───────────────────────────────────────────────────────

def brave_search(query: str, freshness: str = "pd") -> List[Dict]:
    """freshness: pd=24h, pw=week"""
    if not BRAVE_API_KEY:
        return []

    params = urllib.parse.urlencode({
        "q":         query,
        "count":     5,
        "freshness": freshness,
    })
    url = f"https://api.search.brave.com/res/v1/web/search?{params}"
    headers = {
        "Accept":              "application/json",
        "Accept-Encoding":     "gzip",
        "X-Subscription-Token": BRAVE_API_KEY,
    }
    raw = http_get(url, headers=headers, timeout=12)
    if not raw:
        return []

    try:
        data = json.loads(raw)
    except Exception:
        return []

    results = []
    for r in data.get("web", {}).get("results", []):
        pub_date = r.get("page_age") or r.get("age") or ""
        results.append({
            "title":    r.get("title", ""),
            "url":      r.get("url", ""),
            "source":   urllib.parse.urlparse(r.get("url", "")).netloc.replace("www.", ""),
            "snippet":  r.get("description", ""),
            "pub_raw":  pub_date,
        })
    return results

# ── Lane 2: Tier-1 publications ───────────────────────────────────────────────

def collect_tier1() -> List[Dict]:
    queries = [
        "AI artificial intelligence news",
        "LLM model release AI research",
        "OpenAI Anthropic Google AI news",
    ]
    candidates = []
    for q in queries:
        results = brave_search(q, freshness="pd")
        for r in results:
            r["lane"] = "tier1"
            r["authority"] = 70
            r["hn_score"] = 0
            r["hn_comments"] = 0
            # Boost if from known tier-1 source
            for domain, name, weight in TIER1_SOURCES:
                if domain in r["source"]:
                    r["authority"] = weight
                    break
            if r["title"] and r["url"]:
                candidates.append(r)
    return candidates

# ── Lane 3: Primary source announcements ──────────────────────────────────────

def collect_primary_sources() -> List[Dict]:
    queries = [
        "site:openai.com OR site:anthropic.com announcement model release",
        "site:deepmind.google OR site:ai.meta.com research release",
        "site:nvidianews.nvidia.com OR site:huggingface.co blog AI",
    ]
    candidates = []
    for q in queries:
        results = brave_search(q, freshness="pd")
        for r in results:
            r["lane"] = "primary"
            r["authority"] = 95
            r["hn_score"] = 0
            r["hn_comments"] = 0
            # Exact match boost
            for domain, name, weight in PRIMARY_SOURCES:
                if domain in r["url"]:
                    r["authority"] = weight
                    break
            if r["title"] and r["url"]:
                candidates.append(r)
    return candidates

# ── Lane 4: arXiv (selective) ─────────────────────────────────────────────────

def collect_arxiv() -> List[Dict]:
    categories = ["cs.AI", "cs.LG", "stat.ML"]
    results = []
    for cat in categories:
        url = f"https://rss.arxiv.org/rss/{cat}"
        raw = http_get(url, timeout=10)
        if not raw:
            continue
        try:
            root = ET.fromstring(raw)
            ns = {"dc": "http://purl.org/dc/elements/1.1/"}
            for item in root.findall(".//item")[:5]:
                title_el  = item.find("title")
                link_el   = item.find("link")
                desc_el   = item.find("description")
                if title_el is None or link_el is None:
                    continue
                title   = title_el.text or ""
                link    = link_el.text or ""
                snippet = re.sub(r'<[^>]+>', '', desc_el.text or "")[:300]
                if not AI_KW_PATTERN.search(title + " " + snippet):
                    continue
                results.append({
                    "title":       title.strip(),
                    "url":         link.strip(),
                    "source":      "arxiv.org",
                    "snippet":     snippet.strip(),
                    "pub_raw":     "",
                    "lane":        "arxiv",
                    "authority":   40,
                    "hn_score":    0,
                    "hn_comments": 0,
                })
        except Exception:
            continue
    return results

# ── Scoring & deduplication ───────────────────────────────────────────────────

def score_candidate(c: Dict) -> float:
    """Higher = better. Weights match the spec."""
    score = 0.0

    # Authority (0–100)
    score += c.get("authority", 50) * 1.5

    # HN engagement
    hn = c.get("hn_score", 0) + c.get("hn_comments", 0) * 0.5
    score += min(hn, 200) * 0.5

    # Strategic importance from title keywords
    title = (c.get("title") or "").lower()
    if any(k in title for k in ["release", "launch", "announced", "introduces"]):
        score += 20
    if any(k in title for k in ["regulation", "ban", "policy", "law", "congress"]):
        score += 15
    if any(k in title for k in ["billion", "funding", "raises", "acquisition"]):
        score += 12
    if any(k in title for k in ["chip", "hardware", "gpu", "tpu"]):
        score += 10
    if any(k in title for k in ["research", "paper", "arxiv", "study"]):
        score += 5

    # Prefer primary lane stories
    if c.get("lane") == "primary":
        score += 25

    return score


def deduplicate(candidates: List[Dict]) -> List[Dict]:
    """Cluster by near-duplicate title; keep highest-scored per cluster."""
    seen_titles = []
    kept = []

    def similar(a: str, b: str) -> bool:
        # Simple word-overlap similarity
        wa = set(re.findall(r'\w+', a.lower()))
        wb = set(re.findall(r'\w+', b.lower()))
        if not wa or not wb:
            return False
        overlap = len(wa & wb) / min(len(wa), len(wb))
        return overlap > 0.55

    for c in sorted(candidates, key=score_candidate, reverse=True):
        title = c.get("title", "")
        if any(similar(title, seen) for seen in seen_titles):
            continue
        seen_titles.append(title)
        kept.append(c)

    return kept

# ── LLM summary ───────────────────────────────────────────────────────────────

def generate_summary_with_llm(stories: List[Dict]) -> tuple[List[Dict], str]:
    """
    ONE bounded LLM call.
    Adds why_it_matters + tags to each story.
    Returns (enriched_stories, narrative).
    Uses cache to avoid re-running on same data.
    """
    if not ANTHROPIC_KEY:
        # Fallback: no LLM enrichment
        for s in stories:
            s.setdefault("why_it_matters", "")
            s.setdefault("tags", [])
        return stories, "AI news summary unavailable (no LLM key)."
    
    # Check cache first
    today = datetime.now(timezone.utc).date().isoformat()
    source_data = sorted([s["url"] for s in stories])  # Sort URLs for consistent hashing
    
    cached = get_cached("ai_news", today, source_data)
    if cached:
        narrative = cached.get("narrative", "")
        enriched = cached.get("enriched", [])
        
        # Merge cached enrichment back into stories
        for i, s in enumerate(stories):
            if i < len(enriched):
                s["why_it_matters"] = enriched[i].get("why_it_matters", "")
                s["tags"] = enriched[i].get("tags", [])
            else:
                s.setdefault("why_it_matters", "")
                s.setdefault("tags", [])
        
        return stories, narrative

    # Build compact structured input (no full article bodies)
    story_list = "\n".join(
        f"{i+1}. [{s['source']}] {s['title']}"
        + (f"\n   Snippet: {s['snippet'][:200]}" if s.get("snippet") else "")
        for i, s in enumerate(stories)
    )

    prompt = f"""You are producing the AI news section of a daily briefing called The Alfred Report.

Today is {NOW_UTC.strftime('%A, %B %-d, %Y')} UTC.

Below are the top AI news stories collected in the past 24 hours:

{story_list}

Return a valid JSON object with exactly two keys:

1. "enriched": array of objects, one per story (same order), each with:
   - "why_it_matters": 1-2 sentences. Only from what the title+snippet tells you. Do not speculate.
   - "tags": array of 1-3 strings from: models, policy, hardware, enterprise, research, safety, funding, open-source

2. "narrative": a 150-300 word professional brief. Group by theme. Mention companies by name. Analytical tone. No hype. No fabrication. Only reference the stories listed above.

Return ONLY valid JSON. No markdown. No commentary outside the JSON object."""

    body = json.dumps({
        "model":      "claude-haiku-4-5",
        "max_tokens": 2000,
        "messages":   [{"role": "user", "content": prompt}]
    }).encode()

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "x-api-key":         ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "content-type":      "application/json",
            "accept-encoding":   "identity",   # no gzip — simplifies parsing
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            if not raw:
                raise ValueError("Empty response from Anthropic API")
            try:
                resp = json.loads(raw)
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON response: {raw[:200]}")
        
        if "error" in resp:
            raise ValueError(f"API error: {resp['error']}")
        
        raw_text = resp["content"][0]["text"]
        
        # Strip markdown code block if present
        if raw_text.startswith("```json"):
            raw_text = raw_text[7:]  # Remove ```json
        if raw_text.startswith("```"):
            raw_text = raw_text[3:]  # Remove ```
        raw_text = raw_text.strip()
        if raw_text.endswith("```"):
            raw_text = raw_text[:-3].strip()
        
        llm_data = json.loads(raw_text)

        enriched_meta = llm_data.get("enriched", [])
        narrative     = llm_data.get("narrative", "")

        for i, s in enumerate(stories):
            meta = enriched_meta[i] if i < len(enriched_meta) else {}
            s["why_it_matters"] = meta.get("why_it_matters", "")
            s["tags"]           = meta.get("tags", [])

        # Save to cache for future runs (source_data is already sorted)
        cache_data = {
            "narrative": narrative,
            "enriched": enriched_meta
        }
        save_cache("ai_news", today, source_data, cache_data)

        return stories, narrative

    except Exception as e:
        for s in stories:
            s.setdefault("why_it_matters", "")
            s.setdefault("tags", [])
        return stories, f"Summary generation failed: {e}"

# ── Main entry ────────────────────────────────────────────────────────────────

def get_ai_news() -> Dict:
    try:
        # Collect from all lanes
        candidates = []
        candidates.extend(collect_hn_stories())
        candidates.extend(collect_tier1())
        candidates.extend(collect_primary_sources())
        candidates.extend(collect_arxiv())

        # Deduplicate and score
        candidates = deduplicate(candidates)

        # Top 15
        top = candidates[:15]

        if len(top) < 8:
            return {
                "title":   "AI in the News",
                "summary": "No major AI developments detected in the past 24 hours.",
                "items":   [],
                "meta": {
                    "source":     "HackerNews, Brave Search, arXiv",
                    "updated_at": NOW_UTC.isoformat(),
                    "story_count": 0
                }
            }

        # One LLM call to enrich + summarize
        top, narrative = generate_summary_with_llm(top)

        # Build output items
        items = []
        for s in top:
            item = {
                "title":         s.get("title", ""),
                "url":           s.get("url", ""),
                "source":        s.get("source", ""),
                "why_it_matters": s.get("why_it_matters", ""),
                "tags":          s.get("tags", []),
            }
            if s.get("published_at"):
                item["published_at"] = s["published_at"]
            if s.get("hn_score"):
                item["hn_score"] = s["hn_score"]
            items.append(item)

        return {
            "title":   "AI in the News",
            "summary": narrative,
            "items":   items,
            "meta": {
                "source":      "HackerNews, Brave Search, arXiv",
                "updated_at":  NOW_UTC.isoformat(),
                "story_count": len(items),
                "lanes_used":  list({s.get("lane") for s in top}),
            }
        }

    except Exception as e:
        return {
            "title":   "AI in the News",
            "summary": f"Failed to fetch AI news: {e}",
            "items":   [],
            "meta": {
                "source":     "HackerNews, Brave Search, arXiv",
                "updated_at": NOW_UTC.isoformat(),
                "error":      str(e)[:300]
            }
        }


if __name__ == "__main__":
    import sys
    section = get_ai_news()
    print(json.dumps(section, indent=2))
    print(f"\n--- {len(section['items'])} stories ---", file=sys.stderr)
