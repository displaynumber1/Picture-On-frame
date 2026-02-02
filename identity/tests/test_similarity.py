import numpy as np
import pytest

from identity.similarity import cosine_similarity


def test_cosine_similarity_basic() -> None:
    vec_a = np.array([1.0, 0.0], dtype=np.float32)
    vec_b = np.array([1.0, 0.0], dtype=np.float32)
    vec_c = np.array([0.0, 1.0], dtype=np.float32)
    vec_d = np.array([-1.0, 0.0], dtype=np.float32)

    assert cosine_similarity(vec_a, vec_b) == pytest.approx(1.0)
    assert cosine_similarity(vec_a, vec_c) == pytest.approx(0.0)
    assert cosine_similarity(vec_a, vec_d) == pytest.approx(-1.0)
