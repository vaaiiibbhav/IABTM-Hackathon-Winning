"""PRAXIS Feed API Route — §9.

Serves the bounded recommendation feed paired with attention adversary counterfactuals.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from api.database import get_db
from api import clock
from api.schemas import FeedResponse, FeedItem, Candidate, ScoreBreakdown
from api.agents.graph import execute_curation
from api.models import DbUser, DbSelfSpec, DbTheme, DbDecision, DbCandidate, DbSignal

router = APIRouter(prefix="/api/feed", tags=["Feed"])


async def resolve_feed_item(db: AsyncSession, dec: DbDecision) -> FeedItem | None:
    """Resolve a DbDecision row into a FeedItem (candidate + breakdown + counterfactual).

    Shared with the decisions log route (api/routes/decisions.py) so the
    candidate/breakdown mapping lives in exactly one place.
    """
    cand = await db.get(DbCandidate, dec.candidate_id)
    if not cand:
        return None

    cand_schema = Candidate(
        id=cand.id,
        theme_id=cand.theme_id,
        kind=cand.kind,
        title=cand.title,
        url=cand.url,
        provider=cand.provider,
        minutes=cand.minutes,
        depth=cand.depth,
        has_practice=cand.has_practice,
        view_count=cand.view_count,
        verified=cand.verified,
        appraised_at=cand.appraised_at
    )

    cf_cand_schema = None
    if dec.counterfactual_id:
        cf = await db.get(DbCandidate, dec.counterfactual_id)
        if cf:
            cf_cand_schema = Candidate(
                id=cf.id,
                theme_id=cf.theme_id,
                kind=cf.kind,
                title=cf.title,
                url=cf.url,
                provider=cf.provider,
                minutes=cf.minutes,
                depth=cf.depth,
                has_practice=cf.has_practice,
                view_count=cf.view_count,
                verified=cf.verified,
                appraised_at=cf.appraised_at
            )

    b = dec.breakdown
    breakdown_schema = ScoreBreakdown(
        alignment=b.get("alignment", 0.0),
        readiness=b.get("readiness", 0.0),
        actionability=b.get("actionability", 0.0),
        novelty=b.get("novelty", 0.0),
        effort_fit=b.get("effort_fit", 0.0),
        trust_weight=b.get("trust_weight", 1.0),
        saturation_penalty=b.get("saturation_penalty", 0.0),
        score=dec.growth_score
    )

    return FeedItem(
        candidate=cand_schema,
        breakdown=breakdown_schema,
        counterfactual_candidate=cf_cand_schema,
        counterfactual_engagement_score=dec.counterfactual_score
    )


@router.get("/{user_id}", response_model=FeedResponse)
async def get_daily_feed(user_id: str, db: AsyncSession = Depends(get_db)):
    """Assemble today's bounded feed and counterfactuals. Runs agent nodes synchronously."""
    # 1. Verify user exists
    user = await db.get(DbUser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # 2. Check saturation status
    spec_stmt = select(DbSelfSpec).where(DbSelfSpec.user_id == user_id).order_by(desc(DbSelfSpec.created_at))
    spec_res = await db.execute(spec_stmt)
    self_spec = spec_res.scalars().first()
    if not self_spec:
        raise HTTPException(status_code=404, detail="Self specification not found.")

    theme_res = await db.execute(select(DbTheme).where(DbTheme.self_spec_id == self_spec.id))
    themes = theme_res.scalars().all()
    
    # Check if user is saturated on any active theme
    is_saturated = any(t.saturation >= 0.85 for t in themes)
    
    # If saturated, return empty items and saturated=True
    if is_saturated:
        return FeedResponse(
            user_id=user_id,
            date=clock.now().date().isoformat(),
            items=[],
            saturated=True
        )

    # 3. Trigger Agentic Curation Graph nodes (scout -> appraiser -> scorer -> curator)
    try:
        await execute_curation(user_id, db)
    except Exception as e:
        # If agent execution errors, fallback to pre-existing decisions or empty
        print(f"Agent curation failed: {e}")

    # 4. Fetch the decisions served today
    now_time = clock.now()
    today_start = datetime(now_time.year, now_time.month, now_time.day, tzinfo=now_time.tzinfo)
    
    dec_stmt = (
        select(DbDecision)
        .where(DbDecision.user_id == user_id, DbDecision.served_at >= today_start)
        .order_by(desc(DbDecision.served_at))
    )
    dec_res = await db.execute(dec_stmt)
    decisions = dec_res.scalars().all()

    # Map database rows to schemas
    feed_items: list[FeedItem] = []
    for dec in decisions:
        item = await resolve_feed_item(db, dec)
        if item:
            feed_items.append(item)

    return FeedResponse(
        user_id=user_id,
        date=now_time.date().isoformat(),
        items=feed_items,
        saturated=False
    )
