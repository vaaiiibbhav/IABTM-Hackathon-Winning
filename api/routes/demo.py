"""PRAXIS Demo & Time Travel API Routes — §9.

Handles virtual clock advances, database resets, and seeding scenario states.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from api.database import get_db, Base
from datetime import timedelta
from api import clock
from api.schemas import DemoAdvanceRequest, DemoAdvanceResponse, Event, Intervention, FeedItem, Candidate, ScoreBreakdown
from api.engine.scheduler import run_scheduler_tick
from api.models import DbUser, DbSelfSpec, DbAspiration, DbTheme, DbCandidate, DbDecision, DbSignal, DbIntervention, DbEvent
from api.routes.feed import get_daily_feed

router = APIRouter(prefix="/api/demo", tags=["Demo Controls"])


@router.post("/advance", response_model=DemoAdvanceResponse)
async def advance_demo_time(req: DemoAdvanceRequest, db: AsyncSession = Depends(get_db)):
    """Advance the virtual clock by a specific number of days, running scheduler ticks synchronously."""
    # 1. Fetch user to run ticks for
    # For demo robustness, find the first user
    user_res = await db.execute(select(DbUser).limit(1))
    user = user_res.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="No users found to advance time for.")

    # 2. Advance the clock
    elapsed_seconds = req.days * 24 * 3600
    clock.advance(req.days)

    # 3. Execute scheduler tick logic to decay parameters and check triggers
    new_events = await run_scheduler_tick(db, elapsed_seconds)

    # 4. Fetch updated interventions created today
    int_stmt = select(DbIntervention).where(DbIntervention.user_id == user.id).order_by(DbIntervention.sent_at.desc())
    int_res = await db.execute(int_stmt)
    db_interventions = int_res.scalars().all()

    interventions_schema = [
        Intervention(
            id=i.id,
            user_id=i.user_id,
            type=i.type,
            tier=i.tier,
            body=i.body,
            state=i.state,
            sent_at=i.sent_at,
            resolved_at=i.resolved_at
        ) for i in db_interventions
    ]

    # Convert events to schemas
    events_schema = [
        Event(
            id=e.id,
            user_id=e.user_id,
            type=e.type,
            payload=e.payload,
            created_at=e.created_at
        ) for e in new_events
    ]

    # 5. Fetch the new feed changes after time shift
    # We call the get_daily_feed function helper
    feed_data = await get_daily_feed(user.id, db)

    return DemoAdvanceResponse(
        events=events_schema,
        interventions=interventions_schema,
        feed_changes=feed_data.items
    )


@router.post("/reset")
async def reset_demo_state(db: AsyncSession = Depends(get_db)):
    """Reset virtual clock and clear all data tables in the database."""
    clock.reset()

    # Clear tables in dependency order
    await db.execute(delete(DbSignal))
    await db.execute(delete(DbIntervention))
    await db.execute(delete(DbEvent))
    await db.execute(delete(DbDecision))
    await db.execute(delete(DbCandidate))
    await db.execute(delete(DbTheme))
    await db.execute(delete(DbAspiration))
    await db.execute(delete(DbSelfSpec))
    await db.execute(delete(DbUser))

    await db.commit()
    return {"status": "ok", "message": "Clock reset, all database tables truncated."}


@router.post("/seed")
async def seed_demo_scenario(db: AsyncSession = Depends(get_db)):
    """Seed the database with a user scenario three weeks into their aspiration."""
    # Reset first
    await reset_demo_state(db)

    # Seed User
    user_id = "u_demo"
    user = DbUser(
        id=user_id,
        name="Vaibhav",
        email="vaibhav@example.com",
        timezone="IST",
        created_at=clock.now()
    )
    db.add(user)
    await db.flush()

    # Seed SelfSpec
    spec_id = "ss_demo"
    spec = DbSelfSpec(
        id=spec_id,
        user_id=user_id,
        raw_input="become a confident public speaker",
        summary="Build public speaking structures, vocal variety, and stage presence.",
        daily_minutes=45,
        created_at=clock.now()
    )
    db.add(spec)
    await db.flush()

    # Seed Aspirations
    asp = DbAspiration(
        id="asp_1",
        self_spec_id=spec_id,
        text="become a confident public speaker",
        status="active",
        created_at=clock.now()
    )
    db.add(asp)

    t1 = DbTheme(
        id="th_public_speaking",
        self_spec_id=spec_id,
        slug="public-speaking",
        name="Public Speaking",
        alpha=3.0,
        beta=5.0,  # Prior depth = 3 / 8 = 0.375
        momentum=0.18,
        saturation=0.10
    )
    t2 = DbTheme(
        id="th_systems_design",
        self_spec_id=spec_id,
        slug="systems-design",
        name="Systems Design",
        alpha=9.0,
        beta=4.0,  # Prior depth = 9 / 13 = 0.69
        momentum=0.74,
        saturation=0.30
    )
    db.add(t1)
    db.add(t2)
    await db.flush()

    # Seed candidates
    c1 = DbCandidate(
        id="cand_sd_1",
        theme_id="th_systems_design",
        kind="essay",
        title="The Making of an Expert: 22 Minutes on Deliberate Practice",
        url="https://example.com/deliberate-practice",
        provider="Farnam Street",
        minutes=22,
        depth=3,
        has_practice=True,
        view_count=4500,
        verified=True,
        embedding=[0.8, 0.6, 0.0],
        appraised_at=clock.now()
    )
    c2 = DbCandidate(
        id="cand_sd_2",
        theme_id="th_systems_design",
        kind="video",
        title="10 PRODUCTIVITY HACKS THAT WILL CHANGE YOUR LIFE 🔥",
        url="https://example.com/productivity-hacks",
        provider="YouTube",
        minutes=8,
        depth=1,
        has_practice=False,
        view_count=4200000,
        verified=True,
        embedding=[0.1, 0.2, 0.9],
        appraised_at=clock.now()
    )
    c3 = DbCandidate(
        id="cand_ps_1",
        theme_id="th_public_speaking",
        kind="video",
        title="The 7 Rules of Vocal Variety",
        url="https://example.com/vocal-variety",
        provider="YouTube",
        minutes=14,
        depth=2,
        has_practice=True,
        view_count=89000,
        verified=True,
        embedding=[0.9, 0.4, 0.0],
        appraised_at=clock.now()
    )
    db.add(c1)
    db.add(c2)
    db.add(c3)
    await db.flush()

    # Seed some history signals (completions of SD but no actions to pre-condition saturation)
    s1 = DbSignal(
        id="sig_sd_completed_1",
        user_id=user_id,
        candidate_id="cand_sd_1",
        kind="completed",
        value="https://example.com/deliberate-practice",
        reflection_text="Very good insight on deliberate repetition.",
        created_at=clock.now() - timedelta(days=3)
    )
    s2 = DbSignal(
        id="sig_sd_completed_2",
        user_id=user_id,
        candidate_id="cand_sd_2",
        kind="completed",
        value="https://example.com/productivity-hacks",
        reflection_text="Mostly generic hacks.",
        created_at=clock.now() - timedelta(days=2)
    )
    db.add(s1)
    db.add(s2)

    await db.commit()
    return {"status": "ok", "message": "Demo scenario seeded successfully (user: u_demo)."}
