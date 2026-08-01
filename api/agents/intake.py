"""PRAXIS Intake Agent — §5.

Synthesizes onboarding interview answers into a SelfSpec and starting Themes.
"""

import uuid
from typing import List
from pydantic import BaseModel, Field
from api.schemas import SelfSpec, Aspiration, Theme
from api.agents.llm import generate_structured_output
from api import clock


class IntakeThemeSchema(BaseModel):
    name: str = Field(description="Name of the theme, e.g., 'Vocal delivery' or 'Speech preparation'")
    slug: str = Field(description="Lower-case URL-friendly slug, e.g., 'vocal-delivery' or 'speech-prep'")
    description: str = Field(description="Brief explanation of what this theme focuses on")


class IntakeSynthesisResponse(BaseModel):
    summary: str = Field(description="A one-sentence summary of the user's primary objective and context.")
    themes: List[IntakeThemeSchema] = Field(description="Exactly 2 or 3 learning themes derived from their aspiration.")


def parse_daily_minutes(budget_answer: str) -> int:
    """Parse minutes budget string (e.g. '30 minutes') into an integer."""
    try:
        # Extract first digits
        digits = "".join(filter(str.isdigit, budget_answer))
        if digits:
            return int(digits)
    except Exception:
        pass
    return 30  # Default fallback


def get_initial_beta_parameters(experience_answer: str) -> tuple[float, float]:
    """Map experience level answer to Beta-Bernoulli alpha/beta priors."""
    level = experience_answer.lower()
    if "novice" in level or "beginner" in level:
        # Expected depth: 1.0 / (1.0 + 2.0) = 0.33
        return 1.0, 2.0
    elif "advanced" in level or "mastery" in level:
        # Expected depth: 3.0 / (3.0 + 1.5) = 0.66
        return 3.0, 1.5
    else:
        # Intermediate/default: Expected depth: 2.0 / (2.0 + 2.0) = 0.50
        return 2.0, 2.0


def synthesize_intake(
    aspiration_text: str,
    budget_answer: str,
    experience_answer: str,
    blocker_answer: str
) -> IntakeSynthesisResponse:
    """Query Gemini to synthesize the raw inputs into structured themes and a summary."""
    prompt = (
        "You are the Intake node in the PRAXIS curation platform.\n"
        "Your task is to take a user's stated aspiration and interview answers, and synthesize them.\n\n"
        f"User Stated Aspiration: {aspiration_text}\n"
        f"Time Budget: {budget_answer}\n"
        f"Prior Experience Level: {experience_answer}\n"
        f"Biggest Barrier: {blocker_answer}\n\n"
        "Generate a clear summary of what they are trying to achieve, and identify exactly 2 or 3 distinct learning "
        "themes (knowledge areas) they must study to achieve this aspiration. Keep the theme names concise."
    )

    return generate_structured_output(prompt, IntakeSynthesisResponse, model_tier="hard")


def create_initial_spec(
    user_id: str,
    answers: List[str]
) -> tuple[SelfSpec, Aspiration, List[Theme]]:
    """Convert answers list into Pydantic model schemas ready for database persistence."""
    # Ensure we have 4 answers
    aspiration_text = answers[0] if len(answers) > 0 else "Learn new skills"
    budget_ans = answers[1] if len(answers) > 1 else "30 minutes"
    experience_ans = answers[2] if len(answers) > 2 else "Intermediate"
    blocker_ans = answers[3] if len(answers) > 3 else "Lack of practice"

    # 1. Parse primitives
    daily_minutes = parse_daily_minutes(budget_ans)
    alpha, beta = get_initial_beta_parameters(experience_ans)
    now_time = clock.now()

    # 2. Call LLM for themes & summary synthesis
    synthesis = synthesize_intake(aspiration_text, budget_ans, experience_ans, blocker_ans)

    spec_id = f"ss_{uuid.uuid4().hex[:12]}"
    self_spec = SelfSpec(
        id=spec_id,
        user_id=user_id,
        raw_input=aspiration_text,
        summary=synthesis.summary,
        daily_minutes=daily_minutes,
        created_at=now_time
    )

    aspiration = Aspiration(
        id=f"asp_{uuid.uuid4().hex[:12]}",
        self_spec_id=spec_id,
        text=aspiration_text,
        status="active",
        created_at=now_time
    )

    themes = []
    for t_schema in synthesis.themes:
        themes.append(
            Theme(
                id=f"th_{uuid.uuid4().hex[:12]}",
                self_spec_id=spec_id,
                slug=t_schema.slug,
                name=t_schema.name,
                alpha=alpha,
                beta=beta,
                last_engaged_at=None,
                momentum=0.0,
                saturation=0.0,
                depth=alpha / (alpha + beta)
            )
        )

    return self_spec, aspiration, themes
