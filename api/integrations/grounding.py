"""PRAXIS Google Grounding Search Integration.

Leverages Gemini Search Tool to query Google and retrieve real grounded web URLs.
"""

import logging
from typing import List, Any
from google.genai import types
from api.agents.llm import get_next_client

logger = logging.getLogger("praxis.grounding")


async def fetch_grounding_candidates(query: str, limit: int = 5) -> List[dict[str, Any]]:
    """Query Gemini with Google Search tool and extract grounded web links."""
    client_info = get_next_client()
    if not client_info:
        logger.warning("No Gemini API keys found. Skipping Google Grounding Ingestion.")
        return []

    client, key = client_info
    prompt = f"Search Google and find high-quality, practical, non-sensational guides/essays about: {query}."

    try:
        # Request content generation with Search Grounding tool enabled
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{"google_search": {}}],
            ),
        )

        candidates = []
        
        # Verify grounding metadata exists
        candidate = response.candidates[0] if response.candidates else None
        grounding_metadata = candidate.grounding_metadata if candidate else None
        
        if grounding_metadata and grounding_metadata.grounding_chunks:
            # We extract web source chunks
            chunks = grounding_metadata.grounding_chunks
            
            for chunk in chunks[:limit]:
                web = chunk.web
                if not web:
                    continue
                
                title = web.title or "Grounded Search Result"
                url = web.uri
                if not url:
                    continue

                # Normalise provider
                provider = "Web Search"
                domain = url.split("//")[-1].split("/")[0]
                if domain:
                    provider = domain.replace("www.", "")

                candidates.append({
                    "title": title,
                    "url": url,
                    "provider": provider,
                    "kind": "essay",
                    "minutes": 15,  # Default estimated minutes for essays
                    "view_count": 1200,  # Default search popularity
                    "description": title
                })

        return candidates

    except Exception as e:
        logger.error(f"Google Grounding query failed: {e}")
        return []
