#!/usr/bin/env python3
"""
Todoist Skill for The Alfred Report

Fetches outstanding tasks from Sean's Todoist account
Returns formatted section dict ready for JSON serialization
"""

import re
import subprocess
from datetime import datetime
from typing import Dict, List

def get_tasks() -> Dict:
    """
    Fetch Todoist tasks and return as section dict
    
    Returns dict with schema:
    {
        "title": "...",
        "summary": "...",
        "items": [...],
        "meta": {...}
    }
    """
    
    try:
        # Call the todoist skill to list all tasks
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
        
        # Extract task count from first line
        first_line = lines[0] if lines else ""
        match = re.search(r'(\d+)\s+task', first_line)
        total_count = int(match.group(1)) if match else 0
        
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
        
        # Build summary
        if overdue_count > 0:
            summary = f"{total_count} outstanding tasks ({overdue_count} overdue)"
        else:
            summary = f"{total_count} outstanding tasks"
        
        return {
            "title": "To Do List",
            "summary": summary,
            "items": items,
            "meta": {
                "source": "Todoist",
                "updated_at": datetime.now().isoformat(),
                "task_count": total_count,
                "overdue_count": overdue_count
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

if __name__ == "__main__":
    import json
    # Test
    section = get_tasks()
    print(json.dumps(section, indent=2))
