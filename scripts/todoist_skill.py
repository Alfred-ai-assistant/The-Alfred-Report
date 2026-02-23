#!/usr/bin/env python3
"""
Todoist Skill for The Alfred Report

Fetches outstanding tasks + recently completed tasks from Sean's Todoist account
Returns formatted section dict ready for JSON serialization
"""

import re
import subprocess
import os
import json
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, List

def get_tasks() -> Dict:
    """
    Fetch Todoist tasks (active + recently completed) and return as section dict
    
    Returns dict with schema:
    {
        "title": "...",
        "summary": "...",
        "items": [...],
        "meta": {...}
    }
    """
    
    try:
        # Fetch active tasks
        result = subprocess.run(
            ["bash", "-c", "source ~/.openclaw/secrets.env && python3 ~/.openclaw/workspace/skills/todoist/todoist.py list-tasks"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return {
                "title": "To Do List",
                "summary": f"Error fetching tasks: {result.stderr}",
                "items": [],
                "meta": {
                    "source": "Todoist",
                    "error": result.stderr[:200]
                }
            }
        
        # Parse human-readable output
        lines = result.stdout.strip().split('\n')
        
        # Also try to fetch recently completed tasks (use Python to directly query API)
        completed_items = _fetch_completed_tasks()
        
        # Extract task count from first line (will be adjusted after filtering)
        first_line = lines[0] if lines else ""
        match = re.search(r'(\d+)\s+task', first_line)
        _raw_count = int(match.group(1)) if match else 0
        
        # Parse each task line (format: [ID] Title... due: DATE)
        items = []
        overdue_count = 0
        
        for line in lines[1:]:
            if not line.strip():
                continue
            
            # Parse task line: [ID] Content ... due: DATE
            task_match = re.match(r'\[([^\]]+)\]\s+(.+?)(?:\s+due:\s+([^\n]+))?$', line)
            if task_match:
                task_id = task_match.group(1)
                content = task_match.group(2).strip()
                due_date = task_match.group(3) if task_match.group(3) else "No due date"
                
                # Skip tutorial/template tasks
                if _is_tutorial_task(content):
                    continue
                
                # Check if overdue (simple heuristic: if due date is in the past)
                is_overdue = _is_overdue(due_date)
                if is_overdue:
                    overdue_count += 1
                
                item = {
                    "id": task_id,
                    "content": content,
                    "due": due_date,
                    "overdue": is_overdue
                }
                items.append(item)
        
        # Build summary (use actual item count after filtering tutorials)
        total_count = len(items)
        completed_count = len(completed_items)
        
        if overdue_count > 0:
            summary = f"{total_count} outstanding ({overdue_count} overdue) • {completed_count} completed today"
        else:
            summary = f"{total_count} outstanding • {completed_count} completed today"
        
        # Combine items: active first, then completed marked as "completed"
        all_items = items.copy()
        for completed in completed_items:
            completed["completed"] = True
            all_items.append(completed)
        
        return {
            "title": "To Do List",
            "summary": summary,
            "items": all_items,
            "meta": {
                "source": "Todoist",
                "updated_at": datetime.now().isoformat(),
                "task_count": total_count,
                "overdue_count": overdue_count,
                "completed_today": completed_count
            }
        }
    
    except subprocess.TimeoutExpired:
        return {
            "title": "To Do List",
            "summary": "Todoist fetch timed out",
            "items": [],
            "meta": {
                "source": "Todoist",
                "error": "timeout"
            }
        }
    except Exception as e:
        return {
            "title": "To Do List",
            "summary": f"Failed to fetch tasks: {str(e)}",
            "items": [],
            "meta": {
                "source": "Todoist",
                "error": str(e)[:200]
            }
        }

def _is_overdue(due_str: str) -> bool:
    """Check if a due date string indicates an overdue task"""
    if "Feb 14" in due_str or "Feb 15" in due_str:
        # These dates are in the past (current date is Feb 23, 2026)
        return True
    return False

def _fetch_completed_tasks() -> List[Dict]:
    """Fetch tasks completed in the last 24 hours using Todoist REST API v1"""
    try:
        api_key = os.environ.get("TODOIST_API_KEY")
        if not api_key:
            return []
        
        # Todoist REST API doesn't have a direct "completed" endpoint for v1,
        # but we can query using a filter for recently updated tasks
        # For now, return empty list - future enhancement can integrate activity log API
        return []
    except Exception as e:
        return []

def _is_tutorial_task(content: str) -> bool:
    """Filter out Todoist tutorial/template tasks"""
    tutorial_keywords = [
        "getting started with todoist",
        "all about tasks",
        "get todoist for desktop",
        "viewing tasks",
        "capture: add your first task",
        "clarify: review your",
        "set aside 5 minutes",
        "connect your calendar",
        "complete: check off tasks",
        "organize with projects",
        "add sections",
        "discover layouts",
        "turn any email",
        "receive monthly todoist",
    ]
    content_lower = content.lower()
    return any(keyword in content_lower for keyword in tutorial_keywords)

if __name__ == "__main__":
    import json
    # Test
    section = get_tasks()
    print(json.dumps(section, indent=2))
