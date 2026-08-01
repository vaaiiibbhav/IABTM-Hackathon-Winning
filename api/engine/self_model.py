"""PRAXIS Self Model Engine.

Implements Beta-Bernoulli knowledge tracing, momentum tracking, and saturation.
"""

import math
from datetime import datetime, timezone
from typing import Any, List
from api.models import DbTheme


def compute_depth(alpha: float, beta: float) -> float:
    """Compute the posterior mean for theme depth."""
    if alpha + beta <= 0:
        return 0.5
    return alpha / (alpha + beta)


def decay_theme_state(theme: DbTheme, elapsed_days: float) -> None:
    """Decay theme evidence, momentum, and saturation over elapsed days.

    21-day half-life decay towards prior.
    """
    if elapsed_days <= 0:
        return

    # 21-day decay constant: half-life formula => decay = exp(-t / tau)
    # Let's say half-life is 21 days => 0.5 = exp(-21 / tau) => tau = 21 / ln(2) ~= 30.3
    # Or simply: decay_factor = 0.5 ** (elapsed_days / 21)
    decay_factor = 0.5 ** (elapsed_days / 21.0)

    # Decay alpha and beta towards the prior (1.0, 1.0)
    theme.alpha = 1.0 + (theme.alpha - 1.0) * decay_factor
    theme.beta = 1.0 + (theme.beta - 1.0) * decay_factor

    # Decay momentum and saturation towards 0.0
    theme.momentum = max(0.0, theme.momentum * decay_factor)
    theme.saturation = max(0.0, theme.saturation * decay_factor)


def apply_signal_to_theme(theme: DbTheme, signal_kind: str, signal_value: str | None = None) -> dict[str, float]:
    """Update theme alpha, beta, momentum, and saturation based on a signal.

    Returns the change in values (delta) for reporting.
    """
    old_alpha = theme.alpha
    old_beta = theme.beta
    old_momentum = theme.momentum
    old_saturation = theme.saturation

    if signal_kind == "opened":
        # Increment saturation slightly on open
        theme.saturation = min(1.0, theme.saturation + 0.15)
        # Low-level momentum boost
        theme.momentum = min(1.0, theme.momentum + 0.05)

    elif signal_kind == "completed":
        # Baseline completion boost
        theme.alpha += 0.2
        theme.saturation = min(1.0, theme.saturation + 0.25)
        theme.momentum = min(1.0, theme.momentum + 0.1)

    elif signal_kind == "reflected":
        # Reflection signal adjusts knowledge depth (ZPD response)
        if signal_value == "too_easy":
            # Mastered current level, shift focus up
            theme.alpha += 0.5
            theme.momentum = min(1.0, theme.momentum + 0.15)
        elif signal_value == "right":
            # Optimal ZPD
            theme.alpha += 1.0
            theme.momentum = min(1.0, theme.momentum + 0.2)
        elif signal_value == "too_hard":
            # Struggle, shift focus down
            theme.beta += 1.0
            theme.momentum = min(1.0, theme.momentum + 0.1)

    elif signal_kind == "acted":
        # Real-world application is the ultimate validation of mastery
        theme.alpha += 1.5
        # Action relieves saturation
        theme.saturation = max(0.0, theme.saturation - 0.6)
        # Maximum momentum boost
        theme.momentum = min(1.0, theme.momentum + 0.35)

    elif signal_kind == "skipped":
        # Decline in momentum
        theme.momentum = max(0.0, theme.momentum - 0.1)
        # Slight decrease in saturation (ignored it)
        theme.saturation = max(0.0, theme.saturation - 0.05)

    return {
        "alpha_delta": theme.alpha - old_alpha,
        "beta_delta": theme.beta - old_beta,
        "momentum_delta": theme.momentum - old_momentum,
        "saturation_delta": theme.saturation - old_saturation,
    }
