"""PRAXIS Scout Agent — §5.

Scouts candidate pools for a theme concurrently across all three ingestion layers
and verifies URL liveness.
"""

import asyncio
import logging
from typing import List, Any
from sqlalchemy.ext.asyncio import AsyncSession
from api.integrations.youtube import fetch_youtube_candidates
from api.integrations.rss import fetch_rss_candidates
from api.integrations.grounding import fetch_grounding_candidates
from api.integrations.verify import verify_url

logger = logging.getLogger("praxis.scout")


async def scout_candidates_for_theme(theme_name: str, theme_id: str, limit: int = 5) -> List[dict[str, Any]]:
    """Query YouTube, RSS, and Grounded search concurrently to discover content candidates.

    Performs parallel queries and filters out broken links.
    """
    logger.info(f"Scout running for theme '{theme_name}'...")
    
    # 1. Fetch from all sources in parallel
    # RSS url: We can query a default feed or search.
    # For this hackathon, we search YouTube and Grounding, and fallback to RSS if urls are found.
    # We can query some default RSS feeds if needed, e.g. Farnam Street or similar blogs.
    rss_feeds = [
        "https://fs.blog/feed/",
        "https://podcast.iambetterthanme.com/rss"
    ]
    
    tasks = [
        fetch_youtube_candidates(theme_name, limit),
        fetch_grounding_candidates(theme_name, limit)
    ]
    for feed in rss_feeds:
        tasks.append(fetch_rss_candidates(feed, limit=2))

    results = await asyncio.gather(*tasks)

    # Combine lists
    raw_candidates = []
    for r in results:
        raw_candidates.extend(r)

    # 2. Deduplicate by URL
    seen_urls = set()
    unique_candidates = []
    for cand in raw_candidates:
        url = cand.get("url")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_candidates.append(cand)

    # Limit search scope
    unique_candidates = unique_candidates[:12]

    # 3. Validate URL liveness in parallel with Semaphore limit (max 8 concurrent checks)
    sem = asyncio.Semaphore(8)
    verified_candidates = []

    async def check_liveness(cand_item: dict[str, Any]):
        async with sem:
            is_alive = await verify_url(cand_item["url"])
            if is_alive:
                # Add theme metadata
                cand_item["theme_id"] = theme_id
                verified_candidates.append(cand_item)

    await asyncio.gather(*(check_liveness(c) for c in unique_candidates))
    
    logger.info(f"Scout complete. Verified {len(verified_candidates)} candidate links for '{theme_name}'.")
    return verified_candidates
