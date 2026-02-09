import numpy as np


def compute_confidence(final_scores: list[float]) -> float:
    final_scores = [s for s in final_scores if not np.isnan(s)]

    if not final_scores:
        return 0.0

    scores = np.array(final_scores)

    mean_score = scores.mean()
    variance = scores.var()
    agreement = 1 / (1 + variance)

    scores_sorted = np.sort(scores)[::-1]
    dominance = (
        scores_sorted[0] - scores_sorted[1]
        if len(scores_sorted) > 1
        else scores_sorted[0]
    )

    confidence = (
        0.5 * mean_score
        + 0.3 * agreement
        + 0.2 * dominance
    )

    return round(float(np.clip(confidence, 0.0, 1.0)), 5)
