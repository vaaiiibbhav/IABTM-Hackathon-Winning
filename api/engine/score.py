"""PRAXIS Scoring Engine — §4.

Pure, deterministic, printable scoring functions with zero LLM calls.
"""

import math
import json
import os
from datetime import datetime
from typing import Any, List, Tuple
from api import clock

# Default source credibility mapping
DEFAULT_SOURCES = {
    "iambetterthanme.com": 1.2,
    "Farnam Street": 1.1,
    "O'Reilly": 1.1,
    "YouTube": 1.0,
    "rss": 1.0,
    "web": 0.8
}


def load_sources_config() -> dict[str, float]:
    """Load source trust weights from config/sources.json, fallback to defaults."""
    config_path = os.path.join("config", "sources.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return DEFAULT_SOURCES


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two float vectors. Clamped to 0..1."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_v1 = math.sqrt(sum(a * a for a in v1))
    norm_v2 = math.sqrt(sum(a * a for a in v2))
    if norm_v1 == 0.0 or norm_v2 == 0.0:
        return 0.0
    sim = dot_product / (norm_v1 * norm_v2)
    return max(0.0, min(1.0, sim))


def fit_to_level(item_depth: int, theme_depth: float) -> float:
    """Compare content depth (1-3) against user theme depth (0..1).

    Uses a continuous ZPD proximity band.
    """
    user_level = theme_depth * 3.0  # map 0..1 to 0..3 range
    diff = abs(item_depth - user_level)
    # If perfect match (diff = 0), returns 1.0. If diff >= 1.5, returns 0.0.
    return max(0.0, 1.0 - diff / 1.5)


def fits_available_time(item_minutes: int, today_budget: int) -> float:
    """Score how well the item length fits the available time budget."""
    if today_budget <= 0:
        return 0.0
    if item_minutes <= today_budget:
        return 1.0
    # Linear penalty for exceeding budget, down to 0.0 when double the budget
    return max(0.0, 1.0 - (item_minutes - today_budget) / today_budget)


def overlap_with_recent(item_url: str, item_id: str, history: List[dict[str, Any]]) -> float:
    """Compute overlap with recently consumed content.

    Returns 1.0 if already consumed/opened recently, 0.0 otherwise.
    History is a list of dictionary representations of signals.
    """
    for signal in history:
        # Check if user already opened or completed this item
        if signal.get("candidate_id") == item_id or signal.get("value") == item_url:
            if signal.get("kind") in ("opened", "completed", "saved"):
                return 1.0
    return 0.0


def consumed_without_action(theme_id: str, history: List[dict[str, Any]]) -> float:
    """Calculate the saturation penalty.

    Counts items completed/opened in the theme without a corresponding action.
    """
    # Find signals in history for the specified theme
    theme_signals = [s for s in history if s.get("theme_id") == theme_id]
    # Sort signals by created_at descending (newest first)
    theme_signals = sorted(
        theme_signals,
        key=lambda s: s.get("created_at") if isinstance(s.get("created_at"), datetime) else datetime.fromisoformat(str(s.get("created_at"))),
        reverse=True
    )

    # Find the index of the most recent 'acted' signal
    last_action_idx = -1
    for i, s in enumerate(theme_signals):
        if s.get("kind") == "acted":
            last_action_idx = i
            break

    # Slice history to only look at signals since the last action
    signals_since_action = theme_signals[:last_action_idx] if last_action_idx != -1 else theme_signals

    # Count how many articles have been consumed ('completed' or 'opened' if not completed)
    consumed_ids = set()
    for s in signals_since_action:
        if s.get("kind") in ("completed", "opened"):
            consumed_ids.add(s.get("candidate_id"))

    consumed_count = len(consumed_ids)

    # Saturation threshold starts building at 3 completed items without action
    if consumed_count >= 3:
        # Penalty grows by 0.25 per item beyond 2, capped at 1.0
        return min(1.0, (consumed_count - 2) * 0.25)
    return 0.0


def source_credibility(provider: str) -> float:
    """Return trust weight from config, default to 1.0."""
    sources = load_sources_config()
    return sources.get(provider, sources.get(provider.lower(), 1.0))


def growth_score(
    item_id: str,
    item_url: str,
    item_provider: str,
    item_minutes: int,
    item_depth: int,
    item_has_practice: bool,
    item_embedding: List[float],
    theme_id: str,
    theme_depth: float,
    aspiration_embedding: List[float],
    today_budget: int,
    history: List[dict[str, Any]]
) -> Tuple[float, dict[str, float]]:
    """Calculate the growth score for a candidate item.

    Returns the score and the parameter breakdown.
    """
    alignment = cosine_similarity(item_embedding, aspiration_embedding)
    readiness = fit_to_level(item_depth, theme_depth)
    actionability = 1.0 if item_has_practice else 0.0
    novelty = 1.0 - overlap_with_recent(item_url, item_id, history)
    effort_fit = fits_available_time(item_minutes, today_budget)
    trust_weight = source_credibility(item_provider)

    saturation_penalty = consumed_without_action(theme_id, history)

    # Score calculation
    weighted_components = (
        0.30 * alignment +
        0.20 * readiness +
        0.20 * actionability +
        0.15 * novelty +
        0.15 * effort_fit
    )
    score = trust_weight * weighted_components - 0.40 * saturation_penalty

    # Breakdown mapping
    breakdown = {
        "alignment": alignment,
        "readiness": readiness,
        "actionability": actionability,
        "novelty": novelty,
        "effort_fit": effort_fit,
        "trust_weight": trust_weight,
        "saturation_penalty": saturation_penalty,
        "score": score
    }
    return score, breakdown


def clickbait_score(title: str) -> float:
    """Return a clickbait score between 0.0 and 1.0 based on title text features."""
    score = 0.0
    title_lower = title.lower()

    # Match clickbait keywords
    keywords = ["hack", "secret", "reveal", "mindblowing", "shocking", "changed my life", "easy way", "don't want you to", "destroy", "ruin", "🔥", "shut up"]
    for kw in keywords:
        if kw in title_lower:
            score += 0.25

    # Check for excessive uppercase letters
    letters = [c for c in title if c.isalpha()]
    if letters:
        uppercase_ratio = sum(1 for c in title if c.isupper()) / len(letters)
        if uppercase_ratio > 0.4:
            score += 0.25

    # Check for multiple exclamation marks or question marks
    if "!!" in title or "!?" in title or "??" in title:
        score += 0.25
    elif "!" in title:
        score += 0.1

    return min(1.0, score)


def normalized_views(view_count: int) -> float:
    """Log-normalize view count to 0..1 scale. Clamps at 100M views."""
    if view_count <= 0:
        return 0.0
    # log10(100,000,000) = 8
    score = math.log10(view_count) / 8.0
    return max(0.0, min(1.0, score))


def shortness_score(minutes: int) -> float:
    """Prefer short content for high attention engagement. Maximize score at <= 5 mins."""
    if minutes <= 5:
        return 1.0
    if minutes >= 60:
        return 0.0
    return max(0.0, 1.0 - (minutes - 5) / 55.0)


def recency_score(appraised_at: datetime) -> float:
    """Prefer newer content. Score decays from 1.0 to 0.0 over 7 days."""
    try:
        now_time = clock.now()
        age_seconds = (now_time - appraised_at).total_seconds()
        # 7 days = 604800 seconds
        return max(0.0, 1.0 - age_seconds / 604800.0)
    except Exception:
        return 0.5


def engagement_score(title: str, view_count: int, minutes: int, appraised_at: datetime) -> float:
    """Calculate the adversary engagement score (deliberately optimized for attention)."""
    norm_views = normalized_views(view_count)
    cb = clickbait_score(title)
    short = shortness_score(minutes)
    recency = recency_score(appraised_at)

    return (
        0.40 * norm_views +
        0.25 * cb +
        0.20 * short +
        0.15 * recency
    )
