#!/usr/bin/env python3
"""
Alfred Report Validation & Backup Runner
Checks the latest report for missing/empty critical sections
If YouTube has no videos, re-runs digest and regenerates report
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

REPORT_DIR = Path("/home/alfred/repos/The-Alfred-Report/public/alfred-report")
LATEST_JSON = REPORT_DIR / "latest.json"
SECTIONS_TO_CHECK = ["weather", "todoist", "kanban", "youtube"]

def load_latest_report():
    """Load the latest report JSON"""
    if not LATEST_JSON.exists():
        print("❌ No latest.json found")
        return None
    
    with open(LATEST_JSON) as f:
        return json.load(f)

def check_sections(report):
    """Check critical sections for errors/completeness"""
    if not report or "sections" not in report:
        print("❌ Report missing sections")
        return False
    
    issues = []
    sections = report["sections"]
    
    # Weather
    if "weather" not in sections or not sections["weather"].get("items"):
        issues.append("❌ Weather: missing or empty")
    elif sections["weather"].get("meta", {}).get("error"):
        issues.append(f"⚠️ Weather: {sections['weather']['meta']['error']}")
    else:
        print("✅ Weather: OK")
    
    # Todoist
    if "todoist" not in sections or not sections["todoist"].get("items"):
        issues.append("⚠️ Todoist: empty (may be normal if no tasks)")
    elif sections["todoist"].get("meta", {}).get("error"):
        issues.append(f"❌ Todoist: {sections['todoist']['meta']['error']}")
    else:
        print(f"✅ Todoist: {len(sections['todoist']['items'])} task(s)")
    
    # Kanban (Alfred build out)
    if "kanban" not in sections or not sections["kanban"].get("items"):
        issues.append("⚠️ Kanban: empty")
    elif sections["kanban"].get("meta", {}).get("error"):
        issues.append(f"❌ Kanban: {sections['kanban']['meta']['error']}")
    else:
        print(f"✅ Kanban: {len(sections['kanban']['items'])} status group(s)")
    
    # YouTube
    youtube_empty = (
        "youtube" not in sections or 
        not sections["youtube"].get("items") or
        len(sections["youtube"]["items"]) == 0
    )
    
    if youtube_empty:
        issues.append("⚠️ YouTube: no videos (will retry digest)")
        return "youtube_retry"
    elif sections["youtube"].get("meta", {}).get("error"):
        issues.append(f"❌ YouTube: {sections['youtube']['meta']['error']}")
    else:
        print(f"✅ YouTube: {len(sections['youtube']['items'])} video(s)")
    
    if issues:
        for issue in issues:
            print(issue)
        return False
    
    return True

def retry_youtube_digest():
    """Re-run YouTube digest if it's empty"""
    print("\n[BACKUP] Running YouTube digest...")
    result = subprocess.run(
        ["python3", "digest.py"],
        cwd="/home/alfred/.openclaw/workspace/skills/youtube-digest",
        capture_output=True,
        text=True,
        timeout=120
    )
    
    if result.returncode == 0:
        # Extract video count from output
        for line in result.stdout.split('\n'):
            if 'Done — added' in line:
                print(f"[BACKUP] {line.strip()}")
                return True
    
    print(f"[BACKUP] Digest finished (no new videos or already run)")
    return False

def regenerate_report():
    """Re-generate The Alfred Report"""
    print("\n[BACKUP] Regenerating Alfred Report...")
    result = subprocess.run(
        ["bash", "scripts/run_daily_publish.sh"],
        cwd="/home/alfred/repos/The-Alfred-Report",
        capture_output=True,
        text=True,
        timeout=300
    )
    
    if result.returncode == 0:
        print("[BACKUP] Report regenerated successfully")
        return True
    else:
        print(f"[BACKUP] Report generation failed")
        return False

def main():
    print("=" * 60)
    print("Alfred Report Backup Validation")
    print(f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)
    
    # Load and check
    report = load_latest_report()
    if not report:
        print("\nCannot proceed without a report")
        return 1
    
    print("\nChecking critical sections...")
    result = check_sections(report)
    
    if result == "youtube_retry":
        print("\n[BACKUP] YouTube section empty. Checking if digest needs to run...")
        # Try to run digest
        retry_youtube_digest()
        # Regenerate report
        if regenerate_report():
            # Verify
            report = load_latest_report()
            youtube_count = len(report.get("sections", {}).get("youtube", {}).get("items", []))
            print(f"\n✅ Report updated with {youtube_count} video(s)")
            return 0
        else:
            print("\n❌ Failed to regenerate report")
            return 1
    
    elif result is True:
        print("\n✅ All critical sections OK")
        return 0
    
    else:
        print("\n❌ Some sections have issues (see above)")
        return 1

if __name__ == "__main__":
    sys.exit(main())
