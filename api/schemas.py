"""PRAXIS API contract — Pydantic v2 models.

Mirrored field-for-field in web/lib/types.ts (I2). Any change here needs a
CONTRACT: commit and a heads-up to the team (see CLAUDE.md I2).
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

# ---- enums (Literal here, string unions in TS) ----

AspirationStatus = Literal["active", "drifting", "retired"]
CandidateKind = Literal["video", "essay", "book", "tool", "person", "experience"]
SignalKind = Literal["opened", "completed", "saved", "skipped", "acted", "reflected"]
InterventionType = Literal["nudge", "do_block", "drift_proposal", "calibration", "budget_stop"]
EventType = Literal["SATURATED", "DRIFT_DETECTED", "STALLED", "BREAKTHROUGH", "BUDGET_EXCEEDED"]
TraceStatus = Literal["started", "ok", "error"]

# ---- entities (§8 data model) ----


class User(BaseModel):
    id: str
    name: str
    email: str
    timezone: str
    created_at: datetime


class SelfSpec(BaseModel):
    id: str
    user_id: str
    raw_input: str
    summary: str
    daily_minutes: int
    created_at: datetime


class Aspiration(BaseModel):
    id: str
    self_spec_id: str
    text: str
    status: AspirationStatus
    created_at: datetime
    retired_at: datetime | None = None


class Theme(BaseModel):
    id: str
    self_spec_id: str
    slug: str
    name: str
    alpha: float
    beta: float
    last_engaged_at: datetime | None = None
    momentum: float
    saturation: float
    depth: float  # posterior mean alpha/(alpha+beta) — computed for display, not a DB column


class Candidate(BaseModel):
    id: str
    theme_id: str
    kind: CandidateKind
    title: str
    url: str
    provider: str
    minutes: int
    depth: int  # 1-3 content depth, unrelated to Theme.depth
    has_practice: bool
    view_count: int
    verified: bool
    appraised_at: datetime | None = None


class ScoreBreakdown(BaseModel):
    """locals() from engine/score.py::growth_score (§4)."""

    alignment: float
    readiness: float
    actionability: float
    novelty: float
    effort_fit: float
    trust_weight: float
    saturation_penalty: float
    score: float


class Decision(BaseModel):
    id: str
    user_id: str
    candidate_id: str
    served_at: datetime
    growth_score: float
    breakdown: ScoreBreakdown
    counterfactual_id: str | None = None
    counterfactual_score: float | None = None


class Signal(BaseModel):
    id: str
    user_id: str
    candidate_id: str
    kind: SignalKind
    value: str | None = None
    reflection_text: str | None = None
    created_at: datetime


class Intervention(BaseModel):
    id: str
    user_id: str
    type: InterventionType
    tier: int
    body: str
    state: dict
    sent_at: datetime
    resolved_at: datetime | None = None


class Event(BaseModel):
    id: str
    user_id: str
    type: EventType
    payload: dict
    created_at: datetime


class Clock(BaseModel):
    id: int = 1
    virtual_offset_seconds: int = 0


# ---- composite response shapes (§9 API) ----


class FeedItem(BaseModel):
    """One served candidate plus what the engagement objective would have picked instead (Moat 1)."""

    candidate: Candidate
    breakdown: ScoreBreakdown
    counterfactual_candidate: Candidate | None = None
    counterfactual_engagement_score: float | None = None


class FeedResponse(BaseModel):
    user_id: str
    date: str
    items: list[FeedItem]
    saturated: bool


class SelfState(BaseModel):
    """The one fat object §9 says to fetch — no chatty per-field endpoints."""

    user_id: str
    aspirations: list[Aspiration]
    themes: list[Theme]
    today_budget_minutes: int
    drift_score: float
    recent_decisions: list[Decision]


class TraceFrame(BaseModel):
    """One SSE frame per agent-graph node (§5)."""

    node: str
    status: TraceStatus
    ms: int
    summary: str


class InterviewQuestion(BaseModel):
    question: str
    step: int
    of: int
    options: list[str] | None = None  # None => free text (aspiration step only, §5a)


class InterviewAnswerRequest(BaseModel):
    step: int
    answer: str


class InterviewAnswerResponse(BaseModel):
    next_question: InterviewQuestion | None = None
    user_id: str | None = None  # set on the final step


class SignalRequest(BaseModel):
    candidate_id: str
    kind: SignalKind
    reflection: str | None = None


class SignalResponse(BaseModel):
    events: list[Event]
    model_delta: dict


class InterventionResolveRequest(BaseModel):
    accept: bool
    answer: str | None = None


class InterventionResolveResponse(BaseModel):
    result: dict


class DemoAdvanceRequest(BaseModel):
    days: int


class DemoAdvanceResponse(BaseModel):
    events: list[Event]
    interventions: list[Intervention]
    feed_changes: list[FeedItem]


class DemoSeedRequest(BaseModel):
    scenario: str
