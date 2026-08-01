"""PRAXIS RSS Integration.

Fetches and parses articles/podcasts from RSS feeds using feedparser.
"""

import feedparser
import asyncio
from datetime import datetime
from typing import List, Any
import logging

logger = logging.getLogger("praxis.rss")


def _parse_feed(url: str) -> Any:
    """Synchronous feed parsing to run in a threadpool."""
    return feedparser.parse(url)


async def fetch_rss_candidates(feed_url: str, limit: int = 5) -> List[dict[str, Any]]:
    """Fetch entries from an RSS feed asynchronously, returning normalized candidate dicts."""
    try:
        # Run synchronous feed parser in asyncio threadpool to avoid blocking
        feed = await asyncio.to_thread(_parse_feed, feed_url)
        
        candidates = []
        entries = feed.entries[:limit]
        
        for entry in entries:
            # Normalize title and URL
            title = entry.get("title", "Untitled Essay")
            url = entry.get("link")
            if not url:
                continue

            # Determine provider name from feed title or URL domain
            provider = feed.feed.get("title", "RSS Feed")
            
            # Determine candidate kind (defaulting to essay for RSS feeds)
            kind = "essay"
            if "podcast" in feed_url.lower() or "podcast" in provider.lower():
                kind = "video"  # audio/video podcast media

            # Parse date
            published_parsed = entry.get("published_parsed")
            if published_parsed:
                published_at = datetime(*published_parsed[:6])
            else:
                published_at = datetime.utcnow()

            candidates.append({
                "title": title,
                "url": url,
                "provider": provider,
                "kind": kind,
                "published_at": published_at,
                "view_count": 500,  # Arbitrary lower baseline view count for RSS items
                "description": entry.get("summary", "")
            })
            
        return candidates
    except Exception as e:
        logger.error(f"Failed to fetch RSS entries from {feed_url}: {e}")
        return []
