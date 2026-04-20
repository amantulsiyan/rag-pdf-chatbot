import numpy as np


def compute_confidence(final_scores: list[float]):
    final_scores = [s for s in final_scores if not np.isnan(s)]

    if not final_scores:
        return 0.0, {"mean_score": 0.0, "agreement": 0.0, "dominance": 0.0, "variance": 0.0}

    scores = np.array(final_scores)

    mean_score = scores.mean()
    variance = scores.var()
    agreement = 1 / (1 + variance)

    scores_sorted = np.sort(scores)[::-1]
    dominance = (
        scores_sorted[0] - scores_sorted[1]
        if len(scores_sorted) > 1
        else 0.0  # No dominance with single chunk
    )

    confidence = (
        0.5 * mean_score
        + 0.3 * agreement
        + 0.2 * dominance
    )

    breakdown = {
        "mean_score": round(float(mean_score), 4),
        "agreement": round(float(agreement), 4),
        "dominance": round(float(dominance), 4),
        "variance": round(float(variance), 4)
    }

    return round(float(np.clip(confidence, 0.0, 1.0)), 5), breakdown
