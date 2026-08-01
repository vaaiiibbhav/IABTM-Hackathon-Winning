"""PRAXIS Appraiser Agent — §5.

Appraises scouted content, generating depth, duration, practice metadata,
and semantic text embeddings.
"""

import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from api.agents.llm import generate_structured_output, get_next_client

logger = logging.getLogger("praxis.appraiser")


class AppraisalMetadata(BaseModel):
    depth: int = Field(description="Depth rating of the content: 1 (basic concepts), 2 (intermediate application details), 3 (deep masterclass or advanced specifications).")
    minutes: int = Field(description="Estimated reading or watch time in minutes.")
    has_practice: bool = Field(description="Does this content feature concrete exercises, a checklist, code tutorials, or actionable practice tasks?")


async def appraise_candidate_metadata(title: str, description: str) -> AppraisalMetadata:
    """Analyze candidate title and description using LLM to extract learning metadata."""
    prompt = (
        "You are the Content Appraiser agent in the PRAXIS curation platform.\n"
        "Analyze the content candidate below and extract structured metadata.\n\n"
        f"Title: {title}\n"
        f"Description: {description}\n"
    )

    try:
        return generate_structured_output(prompt, AppraisalMetadata, model_tier="easy")
    except Exception as e:
        logger.error(f"Failed to appraise metadata for '{title}': {e}. Returning default.")
        # Fallback default metadata
        return AppraisalMetadata(depth=2, minutes=15, has_practice=True)


async def generate_text_embedding(text: str) -> List[float]:
    """Generate vector embedding for the content text using text-embedding-004."""
    client_info = get_next_client()
    if not client_info:
        # Return fallback dummy embedding vector if offline/no key
        return [0.5, 0.5, 0.0]

    client, key = client_info
    
    try:
        # Call Google GenAI Embeddings service
        res = client.models.embed_content(
            model="text-embedding-004",
            contents=text
        )
        if res.embeddings:
            return res.embeddings[0].values
    except Exception as e:
        logger.warning(f"Embeddings API request failed: {e}. Falling back to default vector.")

    # Return standard 3D mock vector
    return [0.5, 0.5, 0.0]
