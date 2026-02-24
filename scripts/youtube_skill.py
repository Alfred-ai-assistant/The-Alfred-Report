#!/usr/bin/env python3
"""
YouTube AI Daily Digest Skill for The Alfred Report

Fetches videos added TODAY to the AI Daily Digest playlist
Returns formatted section dict ready for JSON serialization
"""

import json
import os
import urllib.request
import urllib.parse
from datetime import datetime, timedelta, timezone
from typing import Dict, List

def get_youtube_updates() -> Dict:
    """
    Read the youtube-digest state file to find today's added videos
    Then fetch their full details from YouTube API
    
    Returns dict with schema:
    {
        "title": "...",
        "summary": "...",
        "items": [...],
        "meta": {...}
    }
    """
    
    try:
        state_file = os.path.expanduser("~/.openclaw/workspace/skills/youtube-digest/state/digest_state.json")
        
        if not os.path.exists(state_file):
            return {
                "title": "Additions to AI Daily Digest",
                "summary": "No YouTube additions tracked yet.",
                "items": [],
                "meta": {
                    "source": "AI Daily Digest Playlist",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "video_count": 0
                }
            }
        
        # Read state
        with open(state_file, 'r') as f:
            state = json.load(f)
        
        # Filter for today's videos
        today = datetime.now(timezone.utc).date()
        today_videos = []
        
        # youtube-digest uses "videos" key, not "added_video_ids"
        for video_id, added_at_str in state.get("videos", {}).items():
            # Parse timestamp
            try:
                added_at = datetime.fromisoformat(added_at_str.replace('Z', '+00:00'))
                if added_at.date() == today:
                    today_videos.append(video_id)
            except (ValueError, KeyError):
                continue
        
        if not today_videos:
            return {
                "title": "Additions to AI Daily Digest",
                "summary": "No new videos added today.",
                "items": [],
                "meta": {
                    "source": "AI Daily Digest Playlist",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "video_count": 0
                }
            }
        
        # Fetch video details from YouTube API
        api_key = os.environ.get("YOUTUBE_API_KEY")
        if not api_key:
            # Try to use the YouTube client credentials
            return {
                "title": "Additions to AI Daily Digest",
                "summary": f"{len(today_videos)} video(s) added today (details unavailable without API key)",
                "items": [
                    {
                        "title": f"Video {vid}",
                        "url": f"https://www.youtube.com/watch?v={vid}",
                        "channel": "Unknown"
                    }
                    for vid in today_videos
                ],
                "meta": {
                    "source": "AI Daily Digest Playlist",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "video_count": len(today_videos)
                }
            }
        
        # Fetch from YouTube API
        video_ids_str = ",".join(today_videos)
        url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet&id={video_ids_str}&key={api_key}"
        
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode())
            
            items = []
            for video in data.get("items", []):
                snippet = video.get("snippet", {})
                items.append({
                    "title": snippet.get("title", "Untitled"),
                    "url": f"https://www.youtube.com/watch?v={video['id']}",
                    "channel": snippet.get("channelTitle", "Unknown"),
                    "published_at": snippet.get("publishedAt", ""),
                    "thumbnail": snippet.get("thumbnails", {}).get("default", {}).get("url", "")
                })
            
            summary = f"Added {len(items)} video(s) to the AI Daily Digest playlist today"
            
            return {
                "title": "Additions to AI Daily Digest",
                "summary": summary,
                "items": items,
                "meta": {
                    "source": "AI Daily Digest Playlist",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "video_count": len(items)
                }
            }
        
        except Exception as e:
            # Fallback: just return video IDs as links
            return {
                "title": "Additions to AI Daily Digest",
                "summary": f"{len(today_videos)} video(s) added today",
                "items": [
                    {
                        "title": f"YouTube Video",
                        "url": f"https://www.youtube.com/watch?v={vid}",
                        "channel": "AI Daily Digest"
                    }
                    for vid in today_videos
                ],
                "meta": {
                    "source": "AI Daily Digest Playlist",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "video_count": len(today_videos),
                    "error": str(e)[:100]
                }
            }
    
    except Exception as e:
        return {
            "title": "Additions to AI Daily Digest",
            "summary": f"Failed to fetch YouTube updates: {str(e)}",
            "items": [],
            "meta": {
                "source": "AI Daily Digest Playlist",
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "video_count": 0,
                "error": str(e)[:200]
            }
        }


if __name__ == "__main__":
    section = get_youtube_updates()
    print(json.dumps(section, indent=2))
