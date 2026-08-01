"""PRAXIS Interviewer Agent — §5, §5a.

Drives the onboarding interview and calibration questions.
"""

from typing import List, Optional
from api.schemas import InterviewQuestion

# Hardcoded onboarding questions.
# Step 1 is free-text (options=None), others are structured tap options.
ONBOARDING_QUESTIONS = [
    InterviewQuestion(
        question="What is the primary skill, identity, or long-term aspiration you are trying to cultivate?",
        step=1,
        of=4,
        options=None  # Free-text input
    ),
    InterviewQuestion(
        question="How many minutes can you realistically dedicate today (and daily) to this goal?",
        step=2,
        of=4,
        options=["15 minutes", "30 minutes", "45 minutes", "60 minutes", "90 minutes"]
    ),
    InterviewQuestion(
        question="What is your current level of understanding or experience in this field?",
        step=3,
        of=4,
        options=[
            "Novice (completely new, starting from zero)",
            "Intermediate (have foundational knowledge, want execution details)",
            "Advanced (active practitioner, looking for deep technical mastery)"
        ]
    ),
    InterviewQuestion(
        question="What has historically been your biggest barrier to achieving this goal?",
        step=4,
        of=4,
        options=[
            "Distraction & clickbait content overload",
            "Lack of concrete practice or action steps",
            "Saturating on research without implementing",
            "Time constraints & busy schedule"
        ]
    )
]


def get_onboarding_question(step: int) -> Optional[InterviewQuestion]:
    """Retrieve the onboarding question for a specific step (1-indexed)."""
    if 1 <= step <= len(ONBOARDING_QUESTIONS):
        return ONBOARDING_QUESTIONS[step - 1]
    return None


def get_total_steps() -> int:
    """Get total steps in the onboarding interview."""
    return len(ONBOARDING_QUESTIONS)
