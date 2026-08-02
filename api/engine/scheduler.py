"""PRAXIS Scheduler and Tick Manager.

Handles theme state decays, drift calculations, and trigger evaluations
either periodically or synchronously for time-travel simulation.
"""

from typing import List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from api import clock
from api.models import DbUser, DbSelfSpec, DbAspiration, DbTheme, DbCandidate, DbSignal, DbIntervention, DbEvent
from api.engine.self_model import decay_theme_state
from api.engine.events import evaluate_triggers


async def run_scheduler_tick(session: AsyncSession, elapsed_seconds: int) -> list[DbEvent]:
    """Execute a single scheduler tick, simulating the passage of elapsed_seconds.

    Does the following:
    1. Decays theme alpha, beta, momentum, and saturation for all users.
    2. Computes the user's drift score based on recent engagement vs stated aspirations.
    3. Runs the event trigger evaluator to detect and flag saturation, budget stops, or stalled states.
    """
    new_events: list[DbEvent] = []
    elapsed_days = elapsed_seconds / 86400.0

    # 1. Fetch all users
    users_res = await session.execute(select(DbUser))
    users = users_res.scalars().all()

    for user in users:
        # Fetch their latest self spec
        spec_res = await session.execute(
            select(DbSelfSpec).where(DbSelfSpec.user_id == user.id).order_by(desc(DbSelfSpec.created_at))
        )
        self_spec = spec_res.scalars().first()
        if not self_spec:
            continue

        # 2. Decay themes if time has elapsed
        if elapsed_seconds > 0:
            theme_res = await session.execute(select(DbTheme).where(DbTheme.self_spec_id == self_spec.id))
            themes = theme_res.scalars().all()
            for theme in themes:
                decay_theme_state(theme, elapsed_days)

        # 3. Evaluate event triggers (SATURATED, DRIFT_DETECTED, STALLED, BREAKTHROUGH, BUDGET_EXCEEDED)
        new_events.extend(await evaluate_triggers(user.id, session))

    await session.commit()
    return new_events
