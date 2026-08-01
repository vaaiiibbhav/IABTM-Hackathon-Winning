"""Tests for the pure Python scoring engine."""

from datetime import datetime, timezone
from api.engine.score import growth_score, engagement_score, fit_to_level


def test_fit_to_level():
    """Test the Zone of Proximal Development (ZPD) readiness fit."""
    # theme_depth = 0.5 => user_level = 1.5
    # item_depth = 1 => diff = 0.5 => fit = 1.0 - 0.5/1.5 = 0.67
    assert abs(fit_to_level(1, 0.5) - 0.6666) < 0.01
    
    # item_depth = 2 => diff = 0.5 => fit = 1.0 - 0.5/1.5 = 0.67
    assert abs(fit_to_level(2, 0.5) - 0.6666) < 0.01

    # theme_depth = 0.9 => user_level = 2.7
    # item_depth = 3 => diff = 0.3 => fit = 1.0 - 0.3/1.5 = 0.80
    assert abs(fit_to_level(3, 0.9) - 0.8) < 0.01

    # item_depth = 1 => diff = 1.7 => fit = max(0, 1.0 - 1.7/1.5) = 0.0
    assert fit_to_level(1, 0.9) == 0.0


def test_growth_vs_engagement():
    """Verify growth_score penalises clickbait and high view-count while engagement_score rewards it."""
    # Candidate A: high quality deliberate practice essay, low views
    embedding_a = [0.8, 0.6, 0.0]
    embedding_asp = [0.8, 0.6, 0.0]  # Perfect alignment
    
    score_a, breakdown_a = growth_score(
        item_id="cand_a",
        item_url="https://example.com/a",
        item_provider="Farnam Street",
        item_minutes=20,
        item_depth=2,
        item_has_practice=True,
        item_embedding=embedding_a,
        theme_id="theme_1",
        theme_depth=0.5,
        aspiration_embedding=embedding_asp,
        today_budget=45,
        history=[]
    )
    
    eng_a = engagement_score(
        title="Deliberate Practice Essay",
        view_count=1000,
        minutes=20,
        appraised_at=datetime.now(timezone.utc)
    )

    # Candidate B: low quality clickbait, high views
    embedding_b = [0.1, 0.2, 0.9]  # Poor alignment
    score_b, breakdown_b = growth_score(
        item_id="cand_b",
        item_url="https://example.com/b",
        item_provider="YouTube",
        item_minutes=5,
        item_depth=1,
        item_has_practice=False,
        item_embedding=embedding_b,
        theme_id="theme_1",
        theme_depth=0.5,
        aspiration_embedding=embedding_asp,
        today_budget=45,
        history=[]
    )

    eng_b = engagement_score(
        title="10 SECRETS THAT WILL CHANGE YOUR LIFE 🔥",
        view_count=5000000,
        minutes=5,
        appraised_at=datetime.now(timezone.utc)
    )

    # Growth score prioritises A over B
    assert score_a > score_b
    
    # Engagement score prioritises B over A (the clickbait adversary)
    assert eng_b > eng_a


def test_saturation_penalty():
    """Verify growth_score goes negative or decreases when saturation is high."""
    embedding = [0.8, 0.6, 0.0]
    embedding_asp = [0.8, 0.6, 0.0]
    
    # History with 4 completions and no actions for theme_1
    history_saturated = [
        {"candidate_id": "cand_1", "theme_id": "theme_1", "kind": "completed", "created_at": datetime.now(timezone.utc)},
        {"candidate_id": "cand_2", "theme_id": "theme_1", "kind": "completed", "created_at": datetime.now(timezone.utc)},
        {"candidate_id": "cand_3", "theme_id": "theme_1", "kind": "completed", "created_at": datetime.now(timezone.utc)},
        {"candidate_id": "cand_4", "theme_id": "theme_1", "kind": "completed", "created_at": datetime.now(timezone.utc)},
    ]

    score_fresh, breakdown_fresh = growth_score(
        item_id="cand_new",
        item_url="https://example.com/new",
        item_provider="Farnam Street",
        item_minutes=20,
        item_depth=2,
        item_has_practice=True,
        item_embedding=embedding,
        theme_id="theme_1",
        theme_depth=0.5,
        aspiration_embedding=embedding_asp,
        today_budget=45,
        history=[]
    )

    score_saturated, breakdown_saturated = growth_score(
        item_id="cand_new",
        item_url="https://example.com/new",
        item_provider="Farnam Street",
        item_minutes=20,
        item_depth=2,
        item_has_practice=True,
        item_embedding=embedding,
        theme_id="theme_1",
        theme_depth=0.5,
        aspiration_embedding=embedding_asp,
        today_budget=45,
        history=history_saturated
    )

    # Saturated theme has a lower score due to saturation penalty
    assert score_fresh > score_saturated
    assert breakdown_saturated["saturation_penalty"] > 0.0
