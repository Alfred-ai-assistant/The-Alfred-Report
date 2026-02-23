#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add scripts dir to path so we can import skills
sys.path.insert(0, str(Path(__file__).parent))
from weather_skill import get_forecast as get_weather
from todoist_skill import get_tasks as get_todoist

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

def main():
    ensure_dirs()

    report_date = os.environ.get("ALFRED_REPORT_DATE")
    if not report_date:
        report_date = datetime.now().astimezone().date().isoformat()

    # Build sections
    sections = {}
    
    # Weather section
    sections["weather"] = get_weather()
    
    # Todoist section
    sections["todoist"] = get_todoist()
    
    payload = {
        "schema_version": 1,
        "report_date": report_date,
        "generated_at": f"{report_date}T07:00:00-05:00",
        "timezone": "America/New_York",
        "sections": sections
    }

    daily_path = DAILY_DIR / f"{report_date}.json"
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

    print(f"Wrote {daily_path}")
    print("Updated latest.json and index.json")

if __name__ == "__main__":
    main()
