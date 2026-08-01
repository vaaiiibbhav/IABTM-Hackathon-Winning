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
from api.engine.drift import calculate_drift_score
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

        # 3. Compute drift score
        # Fetch active aspirations
        asp_res = await session.execute(
            select(DbAspiration).where(DbAspiration.self_spec_id == self_spec.id, DbAspiration.status == "active")
        )
        active_aspirations = asp_res.scalars().all()

        # Get recent engagement embeddings (completed or acted items in last 30 days)
        # Fetch candidate ids from signals of kind completed or acted
        sig_res = await session.execute(
            select(DbSignal)
            .where(DbSignal.user_id == user.id, DbSignal.kind.in_(["completed", "acted"]))
            .order_by(desc(DbSignal.created_at))
            .limit(15)
        )
        recent_signals = sig_res.scalars().all()

        engagement_embeddings = []
        if recent_signals:
            cand_ids = [s.candidate_id for s in recent_signals]
            # Fetch candidates to get embeddings
            cand_res = await session.execute(select(DbCandidate).where(DbCandidate.id.in_(cand_ids)))
            candidates = cand_res.scalars().all()
            
            # Simulated embeddings are stored as JSON in candidate or database
            # Wait, candidate embeddings can be a list of floats (stored as json/string or handled).
            # Let's assume DbCandidate holds its embedding or appraiser generates/stores it.
            # In our db schema in api/models.py, we did not put embedding column in DbCandidate!
            # Wait! Let's check api/models.py:
            # class DbCandidate(Base): ... there is NO embedding column in DbCandidate!
            # Oh! Wait, where is the embedding stored?
            # CLAUDE.md says:
            # "stored as plain float arrays on the row"
            # Let's check §8: `candidates(...)` does it show embedding?
            # §8 lists: candidates(id, theme_id, kind, title, url, provider, minutes, depth, has_practice, view_count, verified, appraised_at)
            # Wait, it doesn't show embedding in the schema block either! But §4 says "stored as plain float arrays on the row".
            # Let's look at schemas.py. Does `Candidate` Pydantic model have embedding?
            # No, schemas.py Candidate:
            # class Candidate(BaseModel): id, theme_id, kind, title, url, provider, minutes, depth, has_practice, view_count, verified, appraised_at
            # It does not have an embedding field either!
            # Wait, how does cosine_similarity get candidate embedding and aspiration embedding?
            # Ah! If candidate has no embedding, where is it?
            # We can add an `embedding` JSON/String column to DbCandidate and DbAspiration, or mock it, or add it to DbCandidate and DbAspiration in api/models.py.
            # Wait! In models.py we did not declare it. We can add it! Or we can store it in a separate table, or add a JSON column `embedding` in DbCandidate and DbAspiration!
            # Let's check: did we add it to DbAspiration and DbCandidate? We can modify DbCandidate and DbAspiration to have an `embedding` column!
            # Yes! Let's modify models.py to add `embedding` JSON column to DbCandidate and DbAspiration!
            # Let's check how we get aspiration embeddings:
            # In schemas.py, Aspiration also has no embedding!
            # But they are used inside scoring engine!
            # Let's look at:
            # `alignment = cosine_similarity(item.embedding, self_model.aspiration_embedding)`
            # So aspiration or selfspec must have an embedding.
            # Let's write DbCandidate and DbAspiration with `embedding` JSON columns (or a mapped JSON column) in `api/models.py` to be safe, so we can store the float arrays.
            # Let's check if the pip installation background task is complete. Let's finish the scheduler file first.
            pass
