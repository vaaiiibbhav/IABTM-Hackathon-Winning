"""PRAXIS Drift Detection Engine.

Computes the divergence between a user's stated aspirations and their actual revealed engagement.
"""

from typing import List
from api.engine.score import cosine_similarity

# Standard threshold above which drift is flagged
DRIFT_THRESHOLD = 0.35


def compute_average_vector(vectors: List[List[float]]) -> List[float]:
    """Compute the mean vector from a list of vectors."""
    if not vectors:
        return []
    vec_len = len(vectors[0])
    mean_vec = [0.0] * vec_len
    for vec in vectors:
        if len(vec) != vec_len:
            continue
        for i in range(vec_len):
            mean_vec[i] += vec[i]
    for i in range(vec_len):
        mean_vec[i] /= len(vectors)
    return mean_vec


def calculate_drift_score(
    aspiration_embeddings: List[List[float]],
    engagement_embeddings: List[List[float]]
) -> float:
    """Calculate the drift score (1.0 - similarity between aspirations and engagement).

    Returns a score between 0.0 (no drift) and 1.0 (complete drift).
    """
    if not aspiration_embeddings or not engagement_embeddings:
        return 0.0

    avg_asp = compute_average_vector(aspiration_embeddings)
    avg_eng = compute_average_vector(engagement_embeddings)

    if not avg_asp or not avg_eng:
        return 0.0

    similarity = cosine_similarity(avg_asp, avg_eng)
    # Drift is the complement of similarity (distance)
    return 1.0 - similarity


def is_drift_detected(drift_score: float) -> bool:
    """Check if the drift score exceeds the threshold."""
    return drift_score >= DRIFT_THRESHOLD
