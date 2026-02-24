#!/usr/bin/env python3
"""
Cache utility for Alfred Report LLM outputs

Prevents re-running expensive LLM calls when source data hasn't changed.
Uses hash-based invalidation per day.
"""

import json
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

CACHE_DIR = Path("/home/alfred/repos/The-Alfred-Report/public/alfred-report/cache")

def get_cache_path(section_name: str, date: str) -> Path:
    """Get cache file path for a section on a given date."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{date}_{section_name}.json"

def hash_data(data: Any) -> str:
    """Create a deterministic hash of data."""
    data_str = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(data_str.encode()).hexdigest()[:16]

def get_cached(section_name: str, date: str, source_data: Any) -> Optional[Dict]:
    """
    Retrieve cached LLM output if:
    1. Cache file exists for this date and section
    2. Source data hash matches (data hasn't changed)
    
    Returns cached dict or None if cache miss.
    """
    cache_path = get_cache_path(section_name, date)
    
    if not cache_path.exists():
        return None
    
    try:
        with open(cache_path) as f:
            cached = json.load(f)
        
        current_hash = hash_data(source_data)
        if cached.get("_hash") == current_hash:
            return cached.get("data")
    except Exception:
        pass
    
    return None

def save_cache(section_name: str, date: str, source_data: Any, llm_output: Dict) -> None:
    """Save LLM output to cache with hash of source data."""
    cache_path = get_cache_path(section_name, date)
    
    cached = {
        "_hash": hash_data(source_data),
        "_date": date,
        "_saved_at": datetime.now(timezone.utc).isoformat(),
        "data": llm_output
    }
    
    try:
        with open(cache_path, 'w') as f:
            json.dump(cached, f)
    except Exception as e:
        print(f"Warning: failed to save cache for {section_name}: {e}")

def clear_old_cache(days_to_keep: int = 7) -> None:
    """Remove cache files older than days_to_keep."""
    if not CACHE_DIR.exists():
        return
    
    cutoff = datetime.now(timezone.utc).timestamp() - (days_to_keep * 86400)
    
    for cache_file in CACHE_DIR.glob("*.json"):
        if cache_file.stat().st_mtime < cutoff:
            try:
                cache_file.unlink()
            except Exception:
                pass
