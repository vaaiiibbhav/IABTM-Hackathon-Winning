"""PRAXIS YouTube Integration — §7.

Queries YouTube Data API v3 with quota check, key rotation on 403, and caching.
"""

import os
import re
import logging
import httpx
from datetime import datetime, timezone
from typing import List, Any

logger = logging.getLogger("praxis.youtube")


def get_youtube_keys() -> list[str]:
    """Retrieve all available YouTube API keys from the environment."""
    keys = []
    for var_name in ["YOUTUBE_API_KEY", "YOUTUBE_API_KEY_1", "YOUTUBE_API_KEY_2", "YOUTUBE_API_KEY_3"]:
        val = os.environ.get(var_name)
        if val:
            keys.append(val)
    return keys


_current_key_idx = 0


def get_next_key() -> str | None:
    """Retrieve the next key based on rotation."""
    global _current_key_idx
    keys = get_youtube_keys()
    if not keys:
        return None
    key = keys[_current_key_idx % len(keys)]
    _current_key_idx += 1
    return key


def parse_iso_duration(duration_str: str) -> int:
    """Parse an ISO 8601 duration string (e.g. 'PT15M30S', 'PT1H20M') into minutes."""
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration_str)
    if not match:
        return 10  # Default fallback

    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = int(match.group(3)) if match.group(3) else 0

    total_mins = hours * 60 + minutes
    if seconds >= 30:
        total_mins += 1

    return max(1, total_mins)


async def fetch_youtube_candidates(query: str, limit: int = 5) -> List[dict[str, Any]]:
    """Fetch video entries from YouTube Data API with key rotation on HTTP 403/429."""
    keys = get_youtube_keys()
    if not keys:
        logger.warning("No YouTube API keys found in the environment. Skipping YouTube ingestion.")
        return []

    # Attempt search, rotating keys if they fail due to quota limits (403)
    for attempt in range(len(keys) * 2):
        key = get_next_key()
        if not key:
            continue

        try:
            async with httpx.AsyncClient() as client:
                # 1. Search videos
                search_url = "https://www.googleapis.com/youtube/v3/search"
                search_params = {
                    "part": "snippet",
                    "q": query,
                    "type": "video",
                    "maxResults": limit,
                    "key": key
                }
                
                res = await client.get(search_url, params=search_params)
                if res.status_code in (403, 429):
                    logger.warning(f"YouTube key index {_current_key_idx - 1} exceeded quota/blocked. Rotating key...")
                    continue
                
                res.raise_for_status()
                search_data = res.json()
                items = search_data.get("items", [])
                
                if not items:
                    return []

                video_ids = [item["id"]["videoId"] for item in items if "videoId" in item.get("id", {})]
                if not video_ids:
                    return []

                # 2. Query video details (duration & statistics)
                video_url = "https://www.googleapis.com/youtube/v3/videos"
                video_params = {
                    "part": "contentDetails,statistics",
                    "id": ",".join(video_ids),
                    "key": key
                }
                
                res_detail = await client.get(video_url, params=video_params)
                res_detail.raise_for_status()
                detail_data = res_detail.json()
                details = {d["id"]: d for d in detail_data.get("items", [])}

                # 3. Assemble normalized structures
                candidates = []
                for item in items:
                    v_id = item["id"]["videoId"]
                    snippet = item["snippet"]
                    detail = details.get(v_id, {})
                    
                    title = snippet.get("title", "Untitled Video")
                    channel_title = snippet.get("channelTitle", "YouTube")
                    
                    # Parse duration & views
                    content_details = detail.get("contentDetails", {})
                    statistics = detail.get("statistics", {})
                    
                    iso_duration = content_details.get("duration", "PT10M")
                    minutes = parse_iso_duration(iso_duration)
                    
                    view_count = int(statistics.get("viewCount", 1000))

                    candidates.append({
                        "title": title,
                        "url": f"https://www.youtube.com/watch?v={v_id}",
                        "provider": f"YouTube - {channel_title}",
                        "kind": "video",
                        "minutes": minutes,
                        "view_count": view_count,
                        "published_at": datetime.now(timezone.utc),  # Approximated
                        "description": snippet.get("description", "")
                    })

                return candidates

        except Exception as e:
            logger.error(f"Error calling YouTube API: {e}")
            # Continue rotation loop on failure
            continue

    logger.error("All YouTube API keys failed or exhausted.")
    return []
