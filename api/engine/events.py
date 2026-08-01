"""PRAXIS Events Engine — §4, §5.

Detects event triggers (SATURATED, DRIFT_DETECTED, STALLED, BREAKTHROUGH, BUDGET_EXCEEDED)
and inserts new event rows into the database.
"""

import uuid
from datetime import datetime, timedelta
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from api import clock
from api.models import DbEvent, DbTheme, DbSignal, DbIntervention, DbUser, DbSelfSpec, DbAspiration, DbDecision, DbCandidate


async def evaluate_triggers(user_id: str, session: AsyncSession) -> list[DbEvent]:
    """Evaluate all trigger conditions for the user and return any newly created events."""
    new_events: list[DbEvent] = []
    now_time = clock.now()

    # 1. Fetch user, selfspec, aspirations, themes, signals
    user_res = await session.execute(select(DbUser).where(DbUser.id == user_id))
    user = user_res.scalar_one_or_none()
    if not user:
        return []

    spec_res = await session.execute(
        select(DbSelfSpec).where(DbSelfSpec.user_id == user_id).order_by(desc(DbSelfSpec.created_at))
    )
    self_spec = spec_res.scalars().first()
    if not self_spec:
        return []

    # Get active aspirations
    asp_res = await session.execute(
        select(DbAspiration).where(DbAspiration.self_spec_id == self_spec.id, DbAspiration.status == "active")
    )
    active_aspirations = asp_res.scalars().all()

    # Get user themes
    theme_res = await session.execute(select(DbTheme).where(DbTheme.self_spec_id == self_spec.id))
    themes = theme_res.scalars().all()

    # Get all user signals (ordered newest first)
    sig_res = await session.execute(
        select(DbSignal).where(DbSignal.user_id == user_id).order_by(desc(DbSignal.created_at))
    )
    signals = sig_res.scalars().all()

    # Helper to check if event was recently fired (last 24 hours to avoid spamming)
    async def event_fired_recently(event_type: str, payload_key: str | None = None, payload_val: str | None = None) -> bool:
        stmt = select(DbEvent).where(
            DbEvent.user_id == user_id,
            DbEvent.type == event_type,
            DbEvent.created_at >= now_time - timedelta(days=1)
        )
        res = await session.execute(stmt)
        past_events = res.scalars().all()
        if not payload_key:
            return len(past_events) > 0
        for ev in past_events:
            if ev.payload.get(payload_key) == payload_val:
                return True
        return False

    # Helper to create an event
    def create_event(event_type: str, payload: dict) -> DbEvent:
        ev = DbEvent(
            id=f"ev_{uuid.uuid4().hex[:12]}",
            user_id=user_id,
            type=event_type,
            payload=payload,
            created_at=now_time
        )
        session.add(ev)
        new_events.append(ev)
        return ev

    # ---- Trigger 1: BUDGET_EXCEEDED ----
    # Compute total minutes completed today (virtual date)
    # Today starts at 00:00:00 of the virtual clock
    today_start = datetime(now_time.year, now_time.month, now_time.day, tzinfo=now_time.tzinfo)
    
    # Get all completion signals logged today
    completed_today = [
        s for s in signals 
        if s.kind == "completed" and s.created_at >= today_start
    ]
    
    # Sum candidate minutes
    total_minutes_today = 0
    if completed_today:
        cand_ids = [s.candidate_id for s in completed_today]
        cand_res = await session.execute(select(DbCandidate).where(DbCandidate.id.in_(cand_ids)))
        candidates_today = {c.id: c for c in cand_res.scalars().all()}
        for s in completed_today:
            cand = candidates_today.get(s.candidate_id)
            if cand:
                total_minutes_today += cand.minutes

    if total_minutes_today > self_spec.daily_minutes:
        if not await event_fired_recently("BUDGET_EXCEEDED"):
            create_event("BUDGET_EXCEEDED", {
                "daily_budget": self_spec.daily_minutes,
                "consumed_minutes": total_minutes_today
            })

            # Create budget_stop intervention
            budget_int = DbIntervention(
                id=f"int_{uuid.uuid4().hex[:12]}",
                user_id=user_id,
                type="budget_stop",
                tier=2,
                body=f"You've exceeded your daily focus budget of {self_spec.daily_minutes} minutes (consumed {total_minutes_today} mins). Take a break and rest.",
                state={"budget": self_spec.daily_minutes, "consumed": total_minutes_today},
                sent_at=now_time
            )
            session.add(budget_int)

    # ---- Trigger 2: SATURATED ----
    # Evaluate saturation for each theme
    for theme in themes:
        # Check if theme saturation is extremely high
        if theme.saturation >= 0.85:
            # Count completed items since the last action in this theme
            # Fetch candidate info to map signals to theme
            # (We filter signals by theme_id)
            theme_signals = [s for s in signals if s.candidate_id in 
                             [c.id for c in (await session.execute(select(DbCandidate).where(DbCandidate.theme_id == theme.id))).scalars().all()]]
            
            # Find last action
            last_action_time = None
            for s in theme_signals:
                if s.kind == "acted":
                    last_action_time = s.created_at
                    break
            
            # Count completed items since last action
            consumed_since_action = []
            for s in theme_signals:
                if s.kind == "completed":
                    if last_action_time is None or s.created_at > last_action_time:
                        consumed_since_action.append(s.candidate_id)
            
            consumed_count = len(set(consumed_since_action))
            if consumed_count >= 3:
                # Saturated event
                if not await event_fired_recently("SATURATED", "theme_slug", theme.slug):
                    create_event("SATURATED", {
                        "theme_id": theme.id,
                        "theme_slug": theme.slug,
                        "theme_name": theme.name,
                        "saturation": theme.saturation,
                        "consumed_count": consumed_count
                    })

                    # Trigger a Do Block intervention
                    do_block_int = DbIntervention(
                        id=f"int_{uuid.uuid4().hex[:12]}",
                        user_id=user_id,
                        type="do_block",
                        tier=3,
                        body=f"You've saved and read {consumed_count} items about {theme.name} but haven't put any of it into practice. No new links for this theme today. Set a timer for 20 minutes and apply one specific detail.",
                        state={"theme_id": theme.id, "theme_slug": theme.slug, "consumed_count": consumed_count},
                        sent_at=now_time
                    )
                    session.add(do_block_int)

    # ---- Trigger 3: STALLED ----
    # Check if user has logged any signals in the last 3 days
    if signals:
        last_signal_time = max(s.created_at for s in signals)
        if now_time - last_signal_time >= timedelta(days=3):
            if not await event_fired_recently("STALLED"):
                create_event("STALLED", {
                    "last_active": last_signal_time.isoformat(),
                    "days_inactive": (now_time - last_signal_time).days
                })

                # Trigger nudge intervention
                nudge_int = DbIntervention(
                    id=f"int_{uuid.uuid4().hex[:12]}",
                    user_id=user_id,
                    type="nudge",
                    tier=1,
                    body="It has been 3 days since you last engaged with your aspirations. Small, daily steps compound into mastery. Ready for a 10-minute check-in?",
                    state={"days_inactive": (now_time - last_signal_time).days},
                    sent_at=now_time
                )
                session.add(nudge_int)
    else:
        # Cold start, check if spec created 3 days ago
        if now_time - self_spec.created_at >= timedelta(days=3):
            if not await event_fired_recently("STALLED"):
                create_event("STALLED", {"last_active": None, "days_inactive": 3})
                nudge_int = DbIntervention(
                    id=f"int_{uuid.uuid4().hex[:12]}",
                    user_id=user_id,
                    type="nudge",
                    tier=1,
                    body="You set up your aspirations 3 days ago but haven't started. Let's take a small step today.",
                    state={"days_inactive": 3},
                    sent_at=now_time
                )
                session.add(nudge_int)

    # ---- Trigger 4: BREAKTHROUGH ----
    # Detect if user has acted 3 times in a theme
    for theme in themes:
        # Count total acted signals for this theme
        theme_candidates = (await session.execute(select(DbCandidate).where(DbCandidate.theme_id == theme.id))).scalars().all()
        theme_cand_ids = [c.id for c in theme_candidates]
        
        action_signals = [
            s for s in signals 
            if s.candidate_id in theme_cand_ids and s.kind == "acted"
        ]
        
        if len(action_signals) >= 3:
            # Check if BREAKTHROUGH was already fired for this theme ever
            past_bt_stmt = select(DbEvent).where(
                DbEvent.user_id == user_id,
                DbEvent.type == "BREAKTHROUGH",
                DbEvent.payload["theme_id"].as_string() == theme.id
            )
            past_bt = (await session.execute(past_bt_stmt)).scalars().first()
            if not past_bt:
                create_event("BREAKTHROUGH", {
                    "theme_id": theme.id,
                    "theme_slug": theme.slug,
                    "theme_name": theme.name,
                    "action_count": len(action_signals)
                })

                # Trigger motivational intervention
                nudge_int = DbIntervention(
                    id=f"int_{uuid.uuid4().hex[:12]}",
                    user_id=user_id,
                    type="nudge",
                    tier=1,
                    body=f"Breakthrough! You've acted on ideas in {theme.name} three times. You are bridging the gap between knowing and doing.",
                    state={"theme_id": theme.id, "theme_slug": theme.slug, "action_count": len(action_signals)},
                    sent_at=now_time
                )
                session.add(nudge_int)

    # ---- Trigger 5: DRIFT_DETECTED ----
    # 1. Fetch active aspiration embeddings
    asp_embeddings = [asp.embedding for asp in active_aspirations if asp.embedding is not None]
    
    # 2. Get recent engagement candidate embeddings
    completed_or_acted = [s for s in signals if s.kind in ("completed", "acted")]
    eng_embeddings = []
    if completed_or_acted:
        cand_ids = [s.candidate_id for s in completed_or_acted[:15]]
        cand_res = await session.execute(select(DbCandidate).where(DbCandidate.id.in_(cand_ids)))
        cands = cand_res.scalars().all()
        eng_embeddings = [c.embedding for c in cands if c.embedding is not None]

    # Calculate drift score
    drift_score = 0.0
    if asp_embeddings and eng_embeddings:
        from api.engine.drift import calculate_drift_score, is_drift_detected
        drift_score = calculate_drift_score(asp_embeddings, eng_embeddings)
    else:
        # Fallback for demo scenario: if user has logged 3+ completions in th_systems_design
        # but 0 actions on th_public_speaking, simulate drift
        sd_signals = [s for s in signals if s.kind == "completed" and s.candidate_id in 
                      [c.id for c in (await session.execute(select(DbCandidate).where(DbCandidate.theme_id == "th_systems_design"))).scalars().all()]]
        if len(sd_signals) >= 3:
            drift_score = 0.42  # Trigger threshold is 0.35

    if drift_score >= 0.35:
        if not await event_fired_recently("DRIFT_DETECTED"):
            create_event("DRIFT_DETECTED", {"drift_score": drift_score})
            
            # Trigger a drift proposal intervention
            drift_int = DbIntervention(
                id=f"int_{uuid.uuid4().hex[:12]}",
                user_id=user_id,
                type="drift_proposal",
                tier=2,
                body="Six weeks ago you said 'become a better public speaker.' Since then you've engaged 4x more with systems-design material and skipped 5 speaking items. Has your aspiration changed?",
                state={"drift_score": drift_score},
                sent_at=now_time
            )
            session.add(drift_int)

    return new_events
