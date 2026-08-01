"""PRAXIS SQLAlchemy 2.0 async models — mirrors api/schemas.py (§8 data model, I2).

Field names/types match the Pydantic contract. IDs are UUID4 strings (client-side
default, not a DB server_default — consistent with the Pydantic `id: str` fields).
Class names are Db-prefixed (DbUser, DbTheme, ...) to stay distinct from the
Pydantic contract classes of the same name in api/schemas.py.

I1: no `server_default=func.now()` anywhere. Timestamp columns are plain nullable
DateTime columns; application code sets them explicitly via `clock.now()` at
insert time.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class DbUser(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String, unique=True)
    timezone: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DbSelfSpec(Base):
    __tablename__ = "self_specs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    raw_input: Mapped[str] = mapped_column(String)
    summary: Mapped[str] = mapped_column(String)
    daily_minutes: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DbAspiration(Base):
    __tablename__ = "aspirations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    self_spec_id: Mapped[str] = mapped_column(ForeignKey("self_specs.id"))
    text: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)  # active | drifting | retired
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)  # §4: plain float array, no vector DB
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    retired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DbTheme(Base):
    __tablename__ = "themes"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    self_spec_id: Mapped[str] = mapped_column(ForeignKey("self_specs.id"))
    slug: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    alpha: Mapped[float] = mapped_column(Float)
    beta: Mapped[float] = mapped_column(Float)
    last_engaged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    momentum: Mapped[float] = mapped_column(Float)
    saturation: Mapped[float] = mapped_column(Float)
    # NOTE: Theme.depth in schemas.py is a computed posterior mean (alpha/(alpha+beta)),
    # not a stored column — deliberately omitted here, see schemas.py:62.


class DbCandidate(Base):
    __tablename__ = "candidates"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    theme_id: Mapped[str] = mapped_column(ForeignKey("themes.id"))
    kind: Mapped[str] = mapped_column(String)  # video|essay|book|tool|person|experience
    title: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)
    provider: Mapped[str] = mapped_column(String)
    minutes: Mapped[int] = mapped_column(Integer)
    depth: Mapped[int] = mapped_column(Integer)  # 1-3 content depth
    has_practice: Mapped[bool] = mapped_column(Boolean)
    view_count: Mapped[int] = mapped_column(Integer)
    verified: Mapped[bool] = mapped_column(Boolean)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)  # §4: plain float array, no vector DB
    appraised_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DbDecision(Base):
    __tablename__ = "decisions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"))
    served_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    growth_score: Mapped[float] = mapped_column(Float)
    breakdown: Mapped[dict] = mapped_column(JSON)
    counterfactual_id: Mapped[str | None] = mapped_column(
        ForeignKey("candidates.id"), nullable=True
    )
    counterfactual_score: Mapped[float | None] = mapped_column(Float, nullable=True)


class DbSignal(Base):
    __tablename__ = "signals"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"))
    kind: Mapped[str] = mapped_column(String)  # opened|completed|saved|skipped|acted|reflected
    value: Mapped[str | None] = mapped_column(String, nullable=True)
    reflection_text: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DbIntervention(Base):
    __tablename__ = "interventions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(String)  # nudge|do_block|drift_proposal|calibration|budget_stop
    tier: Mapped[int] = mapped_column(Integer)
    body: Mapped[str] = mapped_column(String)
    state: Mapped[dict] = mapped_column(JSON)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class DbEvent(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    type: Mapped[str] = mapped_column(String)  # SATURATED|DRIFT_DETECTED|STALLED|BREAKTHROUGH|BUDGET_EXCEEDED
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DbClock(Base):
    """DB-backed mirror of api/clock.py's offset (§8). Not read/written yet —
    clock.py is process-local until Postgres is wired up in Phase 2."""

    __tablename__ = "clock"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    virtual_offset_seconds: Mapped[int] = mapped_column(Integer, default=0)
