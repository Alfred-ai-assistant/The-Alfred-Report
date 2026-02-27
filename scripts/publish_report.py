#!/usr/bin/env python3
import json
import os
import sys
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

# Add scripts dir to path so we can import skills
sys.path.insert(0, str(Path(__file__).parent))
from weather_skill import get_forecast as get_weather
from todoist_skill import get_tasks as get_todoist
from kanban_skill import get_kanban_status as get_kanban
from ai_news_skill import get_ai_news
from youtube_skill import get_youtube_updates
from reddit_skill import get_reddit_sections
from stock_news_skill import get_portfolio_news
from stock_watchlist_skill import get_watchlist_news
from company_news_links import get_company_news_links
from cost_tracker import init_tracker, save_log, get_telegram_message

import re as _re

REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = REPO_ROOT / "public" / "alfred-report"
DAILY_DIR = PUBLIC_DIR / "daily"

def now_iso_local():
    # Local time on the server is fine; your report JSON will carry this.
    return datetime.now().astimezone().isoformat(timespec="seconds")

def ensure_dirs():
    DAILY_DIR.mkdir(parents=True, exist_ok=True)

def load_index():
    idx_path = PUBLIC_DIR / "index.json"
    if not idx_path.exists():
        return {"reports": []}
    with idx_path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")
    tmp.replace(path)

def send_telegram_message(text: str):
    """Send a message to Telegram."""
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[TELEGRAM] Skipping: no credentials")
        return
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown"
        }).encode()
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=10) as r:
            r.read()
        print("[TELEGRAM] Message sent")
    except Exception as e:
        print(f"[TELEGRAM] Failed to send: {e}")

def _title_words(title: str) -> set:
    """Return a set of significant lowercase words from a title."""
    stopwords = {"the", "a", "an", "of", "in", "on", "at", "to", "for", "and", "or",
                 "is", "are", "with", "by", "from", "that", "this", "it", "its", "as"}
    words = set(_re.findall(r'\w+', title.lower()))
    return words - stopwords


def _titles_overlap(t1: str, t2: str, threshold: float = 0.55) -> bool:
    """Return True if two titles share enough significant words to be the same story."""
    w1 = _title_words(t1)
    w2 = _title_words(t2)
    if not w1 or not w2:
        return False
    overlap = len(w1 & w2) / min(len(w1), len(w2))
    return overlap >= threshold


def cross_section_deduplicate(sections: dict) -> dict:
    """
    Remove repeated items across sections so the same story never appears twice.

    Rules (applied in order):
      1. Strip Reddit URLs from ai_news — Reddit has its own dedicated section.
      2. Strip ai_reddit_trending items whose URL OR title already appears in ai_news.
      3. Strip company_reddit_watch items whose URL already appears in ai_reddit_trending
         or ai_news.
    """
    # ── Step 1: remove Reddit links from ai_news ──────────────────────────────
    if "ai_news" in sections:
        before = len(sections["ai_news"].get("items", []))
        sections["ai_news"]["items"] = [
            item for item in sections["ai_news"].get("items", [])
            if "reddit.com" not in item.get("url", "")
        ]
        removed = before - len(sections["ai_news"]["items"])
        if removed:
            print(f"[DEDUP] Removed {removed} Reddit URL(s) from ai_news")

    # ── Step 2: remove ai_reddit_trending items already covered by ai_news ───
    ai_news_urls   = {item["url"] for item in sections.get("ai_news", {}).get("items", [])}
    ai_news_titles = [item.get("title", "") for item in sections.get("ai_news", {}).get("items", [])]

    if "ai_reddit_trending" in sections:
        kept = []
        for item in sections["ai_reddit_trending"].get("items", []):
            url   = item.get("url", "")
            title = item.get("title", "")
            if url in ai_news_urls:
                print(f"[DEDUP] Dropped reddit item (URL match): {title[:60]}")
                continue
            if any(_titles_overlap(title, t) for t in ai_news_titles):
                print(f"[DEDUP] Dropped reddit item (title overlap): {title[:60]}")
                continue
            kept.append(item)
        sections["ai_reddit_trending"]["items"] = kept

    # ── Step 3: remove company_reddit_watch items already in reddit/ai_news ──
    seen_urls = ai_news_urls | {item["url"] for item in sections.get("ai_reddit_trending", {}).get("items", [])}

    if "company_reddit_watch" in sections:
        for company in sections["company_reddit_watch"].get("companies", []):
            before = len(company.get("items", []))
            company["items"] = [
                item for item in company.get("items", [])
                if item.get("url", "") not in seen_urls
            ]
            removed = before - len(company["items"])
            if removed:
                print(f"[DEDUP] Removed {removed} duplicate(s) from company watch: {company.get('company_name')}")

    return sections


def main():
    ensure_dirs()

    report_date = os.environ.get("ALFRED_REPORT_DATE")
    if not report_date:
        report_date = datetime.now().astimezone().date().isoformat()
    
    # Check if today's report already exists — skip regeneration to save costs
    daily_path = DAILY_DIR / f"{report_date}.json"
    if daily_path.exists():
        print(f"[PUBLISH] Report for {report_date} already exists. Skipping regeneration to save API costs.")
        print(f"[PUBLISH] Existing report: {daily_path}")
        return
    
    # Initialize cost tracker
    init_tracker(report_date)

    # Build sections
    sections = {}
    
    # Weather section
    sections["weather"] = get_weather()
    
    # Todoist section
    sections["todoist"] = get_todoist()
    
    # Kanban section
    sections["kanban"] = get_kanban()
    
    # AI News section
    sections["ai_news"] = get_ai_news()
    
    # YouTube section
    sections["youtube"] = get_youtube_updates()
    
    # Reddit sections
    ai_reddit, company_reddit = get_reddit_sections()
    sections["ai_reddit_trending"] = ai_reddit
    sections["company_reddit_watch"] = company_reddit
    
    # Stock Portfolio News and Watchlist
    sections["portfolio_news"] = get_portfolio_news()
    sections["watchlist_news"] = get_watchlist_news()
    
    # Links to Company News (simple hard-coded Google News links)
    sections["company_news_links"] = get_company_news_links()

    # ── Cross-section deduplication ──────────────────────────────────────────
    # Remove the same story from appearing in multiple sections.
    sections = cross_section_deduplicate(sections)

    payload = {
        "schema_version": 1,
        "report_date": report_date,
        "generated_at": f"{report_date}T07:00:00-05:00",
        "timezone": "America/New_York",
        "sections": sections
    }

    latest_path = PUBLIC_DIR / "latest.json"
    index_path = PUBLIC_DIR / "index.json"

    save_json(daily_path, payload)
    save_json(latest_path, payload)

    index = load_index()
    reports = index.get("reports", [])

    # Remove existing entry for the same date
    reports = [r for r in reports if r.get("date") != report_date]

    # Prepend newest
    reports.insert(0, {"date": report_date, "path": f"/alfred-report/daily/{report_date}.json"})

    # Keep last 60 days (adjust later)
    index["reports"] = reports[:60]
    save_json(index_path, index)

    print(f"[PUBLISH] Wrote {daily_path}")
    print("Updated latest.json and index.json")
    
    # Save cost log and send Telegram summary
    save_log()
    telegram_msg = get_telegram_message()
    send_telegram_message(telegram_msg)

if __name__ == "__main__":
    main()
