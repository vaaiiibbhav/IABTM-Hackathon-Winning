"""Hardcoded demo fixture data for the not-yet-DB-backed routes (Phase 1).

Scenario mirrors CLAUDE.md's drift-detection demo beat (§11, Moat 3): a user
whose stated aspiration is "become a confident public speaker" but whose
revealed engagement has drifted toward a "systems design" theme.

Schema-valid against api/schemas.py, not byte-identical to web/lib/fixtures.ts
(that file belongs to a different concurrent workstream — not read here).
"""

from __future__ import annotations

from api import clock
from api.schemas import (
    Aspiration,
    Candidate,
    Decision,
    FeedItem,
    FeedResponse,
    Metric,
    RiskLikeState,
    ScoreBreakdown,
    SelfState,
    Theme,
)

DEMO_USER_ID = "demo-user-1"
_SELF_SPEC_ID = "demo-self-spec-1"

_SPEAKING_THEME_ID = "theme-public-speaking"
_SYSTEMS_THEME_ID = "theme-systems-design"

_CANDIDATE_ESSAY_ID = "cand-deliberate-practice-essay"
_CANDIDATE_CLICKBAIT_ID = "cand-10-productivity-hacks"
_CANDIDATE_SYSTEMS_TALK_ID = "cand-systems-design-talk"
_CANDIDATE_SHORTS_ID = "cand-systems-design-shorts"


def _speaking_aspiration(now) -> Aspiration:
    return Aspiration(
        id="asp-public-speaking",
        self_spec_id=_SELF_SPEC_ID,
        text="become a confident public speaker",
        status="drifting",
        created_at=now,
        retired_at=None,
    )


def _themes(now) -> list[Theme]:
    # depth = posterior mean alpha/(alpha+beta), computed here for display (schemas.py:62)
    speaking_alpha, speaking_beta = 2.0, 6.0
    systems_alpha, systems_beta = 9.0, 2.0
    return [
        Theme(
            id=_SPEAKING_THEME_ID,
            self_spec_id=_SELF_SPEC_ID,
            slug="public-speaking",
            name="Public Speaking",
            alpha=speaking_alpha,
            beta=speaking_beta,
            last_engaged_at=None,
            momentum=0.12,
            saturation=0.10,
            depth=speaking_alpha / (speaking_alpha + speaking_beta),
        ),
        Theme(
            id=_SYSTEMS_THEME_ID,
            self_spec_id=_SELF_SPEC_ID,
            slug="systems-design",
            name="Systems Design",
            alpha=systems_alpha,
            beta=systems_beta,
            last_engaged_at=now,
            momentum=0.78,
            saturation=0.35,
            depth=systems_alpha / (systems_alpha + systems_beta),
        ),
    ]


def _decisions(now) -> list[Decision]:
    breakdown = ScoreBreakdown(
        alignment=0.34,
        readiness=0.62,
        actionability=1.0,
        novelty=0.81,
        effort_fit=0.70,
        trust_weight=1.0,
        saturation_penalty=0.0,
        score=0.58,
    )
    return [
        Decision(
            id="dec-1",
            user_id=DEMO_USER_ID,
            candidate_id=_CANDIDATE_SYSTEMS_TALK_ID,
            served_at=now,
            growth_score=breakdown.score,
            breakdown=breakdown,
            counterfactual_id=_CANDIDATE_SHORTS_ID,
            counterfactual_score=0.71,
        )
    ]


def build_self_state(user_id: str) -> SelfState:
    now = clock.now()
    return SelfState(
        user_id=user_id,
        aspirations=[_speaking_aspiration(now)],
        themes=_themes(now),
        today_budget_minutes=45,
        risk_like_state=RiskLikeState(
            alignment=Metric(value=0.34, driver="stated aspiration is public speaking; recent engagement is systems design"),
            momentum=Metric(value=0.78, driver="systems design theme has 4x the recent engagement of any other"),
            saturation=Metric(value=0.10, driver="no theme has been consumed-without-action past threshold yet"),
            drift=Metric(value=0.66, driver="6 weeks of engagement diverging from the stated aspiration"),
        ),
        recent_decisions=_decisions(now),
    )


def build_feed(user_id: str) -> FeedResponse:
    now = clock.now()
    essay = Candidate(
        id=_CANDIDATE_ESSAY_ID,
        theme_id=_SPEAKING_THEME_ID,
        kind="essay",
        title="The Practice That Actually Builds Stage Presence",
        url="https://example.com/deliberate-practice-speaking",
        provider="Farnam Street",
        minutes=22,
        depth=2,
        has_practice=True,
        view_count=48_000,
        verified=True,
        appraised_at=now,
    )
    clickbait = Candidate(
        id=_CANDIDATE_CLICKBAIT_ID,
        theme_id=_SPEAKING_THEME_ID,
        kind="video",
        title="10 PRODUCTIVITY HACKS THAT WILL CHANGE YOUR LIFE",
        url="https://example.com/10-productivity-hacks",
        provider="YouTube",
        minutes=8,
        depth=1,
        has_practice=False,
        view_count=4_200_000,
        verified=True,
        appraised_at=now,
    )
    systems_talk = Candidate(
        id=_CANDIDATE_SYSTEMS_TALK_ID,
        theme_id=_SYSTEMS_THEME_ID,
        kind="video",
        title="A Philosophy of Software Design — full talk",
        url="https://example.com/systems-design-talk",
        provider="IABTM",
        minutes=48,
        depth=3,
        has_practice=True,
        view_count=210_000,
        verified=True,
        appraised_at=now,
    )
    systems_shorts = Candidate(
        id=_CANDIDATE_SHORTS_ID,
        theme_id=_SYSTEMS_THEME_ID,
        kind="video",
        title="Systems design in 60 SECONDS 🔥",
        url="https://example.com/systems-design-shorts",
        provider="YouTube",
        minutes=1,
        depth=1,
        has_practice=False,
        view_count=1_900_000,
        verified=True,
        appraised_at=now,
    )

    items = [
        FeedItem(
            candidate=essay,
            breakdown=ScoreBreakdown(
                alignment=0.91,
                readiness=0.84,
                actionability=1.0,
                novelty=0.9,
                effort_fit=0.8,
                trust_weight=1.0,
                saturation_penalty=0.0,
                score=0.89,
            ),
            counterfactual_candidate=clickbait,
            counterfactual_engagement_score=0.94,
        ),
        FeedItem(
            candidate=systems_talk,
            breakdown=ScoreBreakdown(
                alignment=0.34,
                readiness=0.62,
                actionability=1.0,
                novelty=0.81,
                effort_fit=0.70,
                trust_weight=1.2,
                saturation_penalty=0.0,
                score=0.58,
            ),
            counterfactual_candidate=systems_shorts,
            counterfactual_engagement_score=0.71,
        ),
    ]

    return FeedResponse(user_id=user_id, date=now.date().isoformat(), items=items, saturated=False)
