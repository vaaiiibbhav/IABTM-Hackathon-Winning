"""PRAXIS Self State API Routes — §9.

Handles onboarding interviews, self twin state, and trace streams.
"""

import uuid
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from api.database import get_db
from api.schemas import (
    InterviewQuestion,
    InterviewAnswerRequest,
    InterviewAnswerResponse,
    SelfState,
    Aspiration,
    Theme,
    Decision,
    RiskLikeState,
    Metric,
)
from api.agents.interviewer import get_onboarding_question, get_total_steps
from api.agents.graph import execute_onboarding
from api.agents.trace import trace_stream
from api.models import DbUser, DbSelfSpec, DbAspiration, DbTheme, DbDecision

router = APIRouter(prefix="/api/self", tags=["Self"])

# In-memory onboarding answers accumulator for demo ease
_onboarding_answers: list[str] = []


@router.post("/interview/start", response_model=InterviewQuestion)
async def start_interview():
    """Start onboarding and return the first question."""
    global _onboarding_answers
    _onboarding_answers.clear()  # Reset onboarding session
    
    first_q = get_onboarding_question(1)
    if not first_q:
        raise HTTPException(status_code=500, detail="Could not load first onboarding question.")
    return first_q


@router.post("/interview/answer", response_model=InterviewAnswerResponse)
async def answer_question(req: InterviewAnswerRequest, db: AsyncSession = Depends(get_db)):
    """Answer a step question. Returns next question or user_id on final step."""
    global _onboarding_answers
    
    total_steps = get_total_steps()
    step = req.step
    
    # Store answer
    if step == 1:
        _onboarding_answers = [req.answer]
    else:
        # Pad list if user skipped a step
        while len(_onboarding_answers) < step - 1:
            _onboarding_answers.append("")
        _onboarding_answers.append(req.answer)

    if step < total_steps:
        # Return next question
        next_q = get_onboarding_question(step + 1)
        return InterviewAnswerResponse(next_question=next_q)
    else:
        # Final step completed! Run intake agent graph to synthesize
        user_id = f"usr_{uuid.uuid4().hex[:8]}"
        try:
            # Run the onboarding graph node sequence
            await execute_onboarding(user_id, _onboarding_answers, db)
            _onboarding_answers.clear()
            return InterviewAnswerResponse(user_id=user_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Intake agent execution failed: {str(e)}")


@router.get("/{user_id}", response_model=SelfState)
async def get_self_state(user_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve the unified SelfState container for the user."""
    # 1. Fetch user
    user = await db.get(DbUser, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # 2. Fetch latest spec
    spec_stmt = select(DbSelfSpec).where(DbSelfSpec.user_id == user_id).order_by(desc(DbSelfSpec.created_at))
    spec_res = await db.execute(spec_stmt)
    self_spec = spec_res.scalars().first()
    if not self_spec:
        raise HTTPException(status_code=404, detail="Self specification not found.")

    # 3. Fetch active aspirations
    asp_stmt = select(DbAspiration).where(DbAspiration.self_spec_id == self_spec.id)
    asp_res = await db.execute(asp_stmt)
    aspirations = [
        Aspiration(
            id=a.id,
            self_spec_id=a.self_spec_id,
            text=a.text,
            status=a.status,
            created_at=a.created_at,
            retired_at=a.retired_at
        ) for a in asp_res.scalars().all()
    ]

    # 4. Fetch themes
    theme_stmt = select(DbTheme).where(DbTheme.self_spec_id == self_spec.id)
    theme_res = await db.execute(theme_stmt)
    themes = [
        Theme(
            id=t.id,
            self_spec_id=t.self_spec_id,
            slug=t.slug,
            name=t.name,
            alpha=t.alpha,
            beta=t.beta,
            last_engaged_at=t.last_engaged_at,
            momentum=t.momentum,
            saturation=t.saturation,
            depth=t.alpha / (t.alpha + t.beta) if (t.alpha + t.beta) > 0 else 0.5
        ) for t in theme_res.scalars().all()
    ]

    # 5. Fetch decisions
    dec_stmt = select(DbDecision).where(DbDecision.user_id == user_id).order_by(desc(DbDecision.served_at)).limit(10)
    dec_res = await db.execute(dec_stmt)
    decisions = [
        Decision(
            id=d.id,
            user_id=d.user_id,
            candidate_id=d.candidate_id,
            served_at=d.served_at,
            growth_score=d.growth_score,
            breakdown=d.breakdown,
            counterfactual_id=d.counterfactual_id,
            counterfactual_score=d.counterfactual_score
        ) for d in dec_res.scalars().all()
    ]

    # 6. §10 risk-like-state tiles — derived from theme momentum/saturation until
    # engine/drift.py computes a real rolling divergence score (Phase 3/4).
    drift_value = 0.15
    drift_driver = "Stated goals match consumption profile."
    if themes:
        momentums = [t.momentum for t in themes]
        if max(momentums) - min(momentums) > 0.5:
            drift_value = 0.42
            drift_driver = "Engagement is concentrated on one theme, diverging from the others."

    avg_momentum = sum(t.momentum for t in themes) / len(themes) if themes else 0.0
    avg_saturation = sum(t.saturation for t in themes) / len(themes) if themes else 0.0

    risk_like_state = RiskLikeState(
        alignment=Metric(value=round(1 - drift_value, 2), driver=drift_driver),
        momentum=Metric(
            value=round(avg_momentum, 2),
            driver="High action-taking speed." if avg_momentum > 0.5 else "Low action-taking speed.",
        ),
        saturation=Metric(
            value=round(avg_saturation, 2),
            driver="Consumption without action is building up." if avg_saturation >= 0.7 else "Balanced intake with real execution.",
        ),
        drift=Metric(value=drift_value, driver=drift_driver),
    )

    return SelfState(
        user_id=user_id,
        aspirations=aspirations,
        themes=themes,
        today_budget_minutes=self_spec.daily_minutes,
        risk_like_state=risk_like_state,
        recent_decisions=decisions
    )


@router.get("/{user_id}/stream")
async def sse_trace_stream(user_id: str):
    """SSE telemetry endpoint for streaming trace frames."""
    return StreamingResponse(
        trace_stream(user_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
