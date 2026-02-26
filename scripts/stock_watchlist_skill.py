#!/usr/bin/env python3
"""
Stock Watchlist News Skill for The Alfred Report

Identical to stock_news_skill.py but uses stocks-watchlist.yaml 
for a different set of tickers (supplementary holdings).
"""

import sys
from pathlib import Path

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).parent))
from stock_news_skill import get_stock_news_section


def get_watchlist_news():
    """Entry point for watchlist news section."""
    return get_stock_news_section(
        config_file="stocks-watchlist.yaml",
        section_name="watchlist_news",
        section_title="Stock Watchlist News",
        state_key="watchlist",
        log_prefix="[STOCK_WATCHLIST]"
    )


if __name__ == "__main__":
    import json
    result = get_watchlist_news()
    print(json.dumps(result, indent=2))
