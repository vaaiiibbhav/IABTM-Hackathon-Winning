"""GET /api/self/{id} — §9. DB not wired yet (Phase 2); serves fixture data."""

from __future__ import annotations

from fastapi import APIRouter

from api.routes.fixtures import build_self_state
from api.schemas import SelfState

router = APIRouter(prefix="/api/self", tags=["self"])


@router.get("/{id}")
async def get_self_state(id: str) -> SelfState:
    return build_self_state(id)
