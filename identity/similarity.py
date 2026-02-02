"""Similarity utilities for embedding comparisons."""

from __future__ import annotations

import numpy as np

VERIFY_THRESHOLD = 0.68
REFINE_THRESHOLD = 0.72


def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""

    denom = np.linalg.norm(vec_a) * np.linalg.norm(vec_b)
    if denom == 0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / denom)
