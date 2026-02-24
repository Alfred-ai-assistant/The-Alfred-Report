#!/usr/bin/env python3
"""
YouTube AI Daily Digest Skill for The Alfred Report

Reads today's video IDs from the digest state file,
fetches full details via YouTube Data API (OAuth),
and returns a formatted section dict for the report.
"""

import json
import os
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from typing import Dict, List

YOUTUBE_API    = "https://www.googleapis.com/youtube/v3"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
STATE_FILE     = os.path.expanduser(
    "~/.openclaw/workspace/skills/youtube-digest/state/digest_state.json"
)


def _get_access_token() -> str:
    """Exchange refresh token for a short-lived access token using urllib."""
    client_id     = os.environ["YOUTUBE_CLIENT_ID"]
    client_secret = os.environ["YOUTUBE_CLIENT_SECRET"]
    refresh_token = os.environ["YOUTUBE_REFRESH_TOKEN"]

    body = urllib.parse.urlencode({
        "client_id":     client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type":    "refresh_token",
    }).encode()

    req = urllib.request.Request(TOKEN_ENDPOINT, data=body, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())["access_token"]


def _fetch_video_details(video_ids: List[str], access_token: str) -> List[Dict]:
    """
    Fetch title, channel, published date, and thumbnail for a list of video IDs.
    Thumbnails are also constructable without an API call, but we pull them here
    for accuracy (maxresdefault may not exist; API returns the best available).
    """
    # YouTube API allows up to 50 IDs per request
    items = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        params = urllib.parse.urlencode({
            "part": "snippet",
            "id":   ",".join(batch),
        })
        req = urllib.request.Request(
            f"{YOUTUBE_API}/videos?{params}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode())

        for video in data.get("items", []):
            snippet   = video.get("snippet", {})
            video_id  = video["id"]
            thumbnails = snippet.get("thumbnails", {})

            # Prefer high quality, fall back progressively
            thumbnail_url = (
                thumbnails.get("maxres", {}).get("url")
                or thumbnails.get("high",   {}).get("url")
                or thumbnails.get("medium", {}).get("url")
                or thumbnails.get("default",{}).get("url")
                or f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
            )

            items.append({
                "video_id":     video_id,
                "title":        snippet.get("title", "Untitled"),
                "channel":      snippet.get("channelTitle", "Unknown"),
                "published_at": snippet.get("publishedAt", ""),
                "thumbnail":    thumbnail_url,
                "url":          f"https://www.youtube.com/watch?v={video_id}",
            })

    return items


def get_youtube_updates() -> Dict:
    """
    Main entry point for The Alfred Report.
    Returns section dict with video items for today.
    """
    try:
        # ── Read state file ────────────────────────────────────────────────
        if not os.path.exists(STATE_FILE):
            return _empty("No YouTube additions tracked yet.")

        with open(STATE_FILE) as f:
            state = json.load(f)

        today = datetime.now(timezone.utc).date()
        today_ids = [
            vid for vid, ts in state.get("videos", {}).items()
            if datetime.fromisoformat(ts).date() == today
        ]

        if not today_ids:
            return _empty("No new videos added today.")

        # ── Get OAuth access token ─────────────────────────────────────────
        try:
            access_token = _get_access_token()
        except Exception as e:
            return _fallback(today_ids, f"OAuth token error: {e}")

        # ── Fetch video details ────────────────────────────────────────────
        try:
            videos = _fetch_video_details(today_ids, access_token)
        except Exception as e:
            return _fallback(today_ids, f"API fetch error: {e}")

        if not videos:
            return _fallback(today_ids, "No video details returned from API.")

        return {
            "title":   "Today's AI Daily Digest",
            "summary": f"{len(videos)} new video{'s' if len(videos) != 1 else ''} added across your AI channels",
            "items":   videos,
            "meta": {
                "source":     "AI Daily Digest Playlist",
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "video_count": len(videos),
            },
        }

    except Exception as e:
        return {
            "title":   "Today's AI Daily Digest",
            "summary": f"Failed to fetch YouTube updates: {e}",
            "items":   [],
            "meta": {
                "source":     "AI Daily Digest Playlist",
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "video_count": 0,
                "error":      str(e)[:200],
            },
        }


def _empty(message: str) -> Dict:
    return {
        "title":   "Today's AI Daily Digest",
        "summary": message,
        "items":   [],
        "meta": {
            "source":      "AI Daily Digest Playlist",
            "updated_at":  datetime.now(timezone.utc).isoformat(),
            "video_count": 0,
        },
    }


def _fallback(video_ids: List[str], error: str) -> Dict:
    """Return basic link items when we can't fetch full details."""
    return {
        "title":   "Today's AI Daily Digest",
        "summary": f"{len(video_ids)} video(s) added today",
        "items": [
            {
                "video_id":     vid,
                "title":        "YouTube Video",
                "channel":      "AI Daily Digest",
                "published_at": "",
                "thumbnail":    f"https://img.youtube.com/vi/{vid}/hqdefault.jpg",
                "url":          f"https://www.youtube.com/watch?v={vid}",
            }
            for vid in video_ids
        ],
        "meta": {
            "source":      "AI Daily Digest Playlist",
            "updated_at":  datetime.now(timezone.utc).isoformat(),
            "video_count": len(video_ids),
            "error":       error,
        },
    }


if __name__ == "__main__":
    section = get_youtube_updates()
    print(json.dumps(section, indent=2))
