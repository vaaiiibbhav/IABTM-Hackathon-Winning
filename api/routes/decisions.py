"""PRAXIS Decisions API Route — §9.

The full decision log: every item ever served to a user, its score breakdown,
and the counterfactual it beat. Backs the /why page.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from api.database import get_db
from api.schemas import FeedItem
from api.models import DbUser, DbDecision
from api.routes.feed import resolve_feed_item

router = APIRouter(prefix="/api/decisions", tags=["Decisions"])


@router.get("/{user_id}", response_model=list[FeedItem])
async def get_decision_log(user_id: str, db: AsyncSession = Depends(get_db)):
    """Every decision ever served to this user, most recent first."""
    user = await db.get(DbUser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    dec_stmt = (
        select(DbDecision)
        .where(DbDecision.user_id == user_id)
        .order_by(desc(DbDecision.served_at))
    )
    dec_res = await db.execute(dec_stmt)
    decisions = dec_res.scalars().all()

    items: list[FeedItem] = []
    for dec in decisions:
        item = await resolve_feed_item(db, dec)
        if item:
            items.append(item)

    return items
