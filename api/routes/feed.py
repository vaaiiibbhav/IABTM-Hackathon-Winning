"""GET /api/feed/{user_id} — §9. DB not wired yet (Phase 2); serves fixture data."""

from __future__ import annotations

from fastapi import APIRouter

from api.routes.fixtures import build_feed
from api.schemas import FeedResponse

router = APIRouter(prefix="/api/feed", tags=["feed"])


@router.get("/{user_id}")
async def get_feed(user_id: str) -> FeedResponse:
    return build_feed(user_id)
