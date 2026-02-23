#!/usr/bin/env python3
"""
Kanban Skill for The Alfred Report

Fetches status from the Tech Kanban board (iMac OpenClaw Tech Kanban)
Returns formatted section dict ready for JSON serialization
"""

import re
import subprocess
from datetime import datetime
from typing import Dict, List

def get_kanban_status() -> Dict:
    """
    Fetch kanban board status and return as section dict
    
    Returns dict with schema:
    {
        "title": "...",
        "summary": "...",
        "items": [...],
        "meta": {...}
    }
    """
    
    try:
        # Call the kanban skill to list all cards
        result = subprocess.run(
            ["bash", "-c", "bash ~/.openclaw/workspace/skills/github-kanban/list_cards.sh"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return {
                "title": "Alfred's Tech Build Out",
                "summary": f"Error fetching kanban status",
                "items": [],
                "meta": {
                    "source": "GitHub Projects v2",
                    "error": result.stderr[:200]
                }
            }
        
        # Parse output
        lines = result.stdout.strip().split('\n')
        
        # Count cards by status
        status_counts = {
            "Backlog": 0,
            "Ready": 0,
            "In progress": 0,
            "Impeded or On Hold": 0,
            "Done": 0
        }
        
        status_cards = {
            "Backlog": [],
            "Ready": [],
            "In progress": [],
            "Impeded or On Hold": [],
            "Done": []
        }
        
        current_status = None
        
        for line in lines:
            # Match status headers like "[Backlog] Card Title"
            status_match = re.match(r'\[(\w.*?)\]\s+(.+)', line)
            if status_match:
                status = status_match.group(1)
                title = status_match.group(2).strip()
                
                # Normalize status name
                if status in status_counts:
                    current_status = status
                    status_counts[status] += 1
                    status_cards[status].append(title)
        
        # Build items showing status breakdown (skip Impeded or On Hold)
        items = []
        for status in ["In progress", "Ready", "Backlog", "Done"]:
            count = status_counts[status]
            cards = status_cards[status]
            
            # Create item for this status
            item = {
                "status": status,
                "count": count,
                "cards": cards[:5]  # Show up to 5 cards as examples
            }
            items.append(item)
        
        # Build summary
        in_progress = status_counts["In progress"]
        ready = status_counts["Ready"]
        backlog = status_counts["Backlog"]
        done = status_counts["Done"]
        total = sum(status_counts.values())
        
        summary = f"{total} cards total • {in_progress} in progress • {ready} ready • {backlog} backlog • {done} done"
        
        return {
            "title": "Alfred's Tech Build Out",
            "summary": summary,
            "items": items,
            "meta": {
                "source": "GitHub Projects v2 (iMac OpenClaw Tech Kanban)",
                "updated_at": datetime.now().isoformat(),
                "total_cards": total,
                "in_progress": in_progress,
                "ready": ready,
                "backlog": backlog,
                "done": done
            }
        }
    
    except subprocess.TimeoutExpired:
        return {
            "title": "Alfred's Tech Build Out",
            "summary": "Kanban fetch timed out",
            "items": [],
            "meta": {
                "source": "GitHub Projects v2",
                "error": "timeout"
            }
        }
    except Exception as e:
        return {
            "title": "Alfred's Tech Build Out",
            "summary": f"Failed to fetch kanban status: {str(e)}",
            "items": [],
            "meta": {
                "source": "GitHub Projects v2",
                "error": str(e)[:200]
            }
        }

if __name__ == "__main__":
    import json
    # Test
    section = get_kanban_status()
    print(json.dumps(section, indent=2))
