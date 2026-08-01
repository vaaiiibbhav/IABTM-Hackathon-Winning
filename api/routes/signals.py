"""PRAXIS Signals API Route — §9.

Records user signal interactions (opened, completed, saved, skipped, acted, reflected)
and runs the reflector agent node.
"""

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from api.database import get_db
from api.schemas import SignalRequest, SignalResponse, Event
from api.agents.graph import execute_signal
from api.models import DbUser, DbEvent

router = APIRouter(prefix="/api/signal", tags=["Signals"])


@router.post("", response_model=SignalResponse)
async def log_user_signal(
    req: SignalRequest,
    x_user_id: str | None = Header(None, alias="X-User-Id"),
    db: AsyncSession = Depends(get_db)
):
    """Log an interaction signal (opened, completed, saved, skipped, acted, reflected) for a candidate link."""
    # 1. Determine user ID
    user_id = x_user_id
    if not user_id:
        # Fallback to first user in database for demo robustness
        user_res = await db.execute(select(DbUser).limit(1))
        user = user_res.scalars().first()
        if user:
            user_id = user.id
        else:
            raise HTTPException(
                status_code=400, 
                detail="X-User-Id header missing and no seeded users found."
            )

    # 2. Trigger the Reflector node in the Agent Graph
    try:
        # We pass signal kind and reflection parameters to the agent workflow
        # Value is set to None (or could be URL if available, but candidate ID is main key)
        await execute_signal(
            user_id=user_id,
            candidate_id=req.candidate_id,
            kind=req.kind,
            value=None,
            reflection=req.reflection,
            db_session=db
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Reflector agent node execution failed: {str(e)}"
        )

    # 3. Retrieve any new events emitted during this reflection update
    # (events created in the last 5 seconds as part of this transaction)
    # We query the database for events
    stmt = (
        select(DbEvent)
        .where(DbEvent.user_id == user_id)
        .order_by(DbEvent.created_at.desc())
        .limit(3)
    )
    event_res = await db.execute(stmt)
    db_events = event_res.scalars().all()

    events_schema = [
        Event(
            id=e.id,
            user_id=e.user_id,
            type=e.type,
            payload=e.payload,
            created_at=e.created_at
        ) for e in db_events
    ]

    # Return change delta
    return SignalResponse(
        events=events_schema,
        model_delta={"timestamp": clock.now().isoformat()}
    )
# We import clock relative to clock.py
from api import clock
