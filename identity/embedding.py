"""Embedding extraction using InsightFace ArcFace."""

from __future__ import annotations

import threading
from typing import Optional

import numpy as np

try:
    import cv2  # type: ignore
    from insightface.app import FaceAnalysis  # type: ignore
except Exception as exc:  # pragma: no cover - optional dependency in runtime
    raise ImportError(
        "InsightFace and OpenCV are required for embedding extraction."
    ) from exc


_FACE_APP: Optional[FaceAnalysis] = None
_FACE_APP_LOCK = threading.Lock()


def _get_face_app() -> FaceAnalysis:
    """Initialize a singleton FaceAnalysis app."""

    global _FACE_APP
    if _FACE_APP is None:
        with _FACE_APP_LOCK:
            if _FACE_APP is None:
                app = FaceAnalysis(name="buffalo_l")
                app.prepare(ctx_id=0, det_size=(640, 640))
                _FACE_APP = app
    return _FACE_APP


def extract_embedding(image_bytes: bytes) -> np.ndarray:
    """Extract a normalized embedding from image bytes using ArcFace.

    Args:
        image_bytes: Raw image bytes.

    Returns:
        A normalized embedding vector as a NumPy array.

    Raises:
        ValueError: If no face is detected or image is invalid.
    """

    img_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Invalid image bytes.")

    app = _get_face_app()
    faces = app.get(image)
    if not faces:
        raise ValueError("No face detected.")

    if len(faces) > 1:
        faces.sort(key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]), reverse=True)

    face = faces[0]
    embedding = getattr(face, "normed_embedding", None)
    if embedding is None:
        embedding = face.embedding
        norm = np.linalg.norm(embedding)
        if norm == 0:
            raise ValueError("Invalid embedding.")
        embedding = embedding / norm

    return np.asarray(embedding, dtype=np.float32)
