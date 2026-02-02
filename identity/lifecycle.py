"""Pure functions for avatar lifecycle operations."""

from __future__ import annotations

from typing import Sequence

import numpy as np

from .embedding import extract_embedding
from .encryption import decrypt_embedding, encrypt_embedding
from .enums import AvatarState
from .schemas import EmbeddingPayload, EnrollmentResult, RefineResult, VerificationResult, utc_now
from .similarity import REFINE_THRESHOLD, VERIFY_THRESHOLD, cosine_similarity


EMBEDDING_SIZE = 512
LOCK_AFTER_FAILED_ATTEMPTS = 5


def _serialize_embedding(embedding: np.ndarray) -> bytes:
    """Serialize a float32 embedding to bytes."""

    return np.asarray(embedding, dtype=np.float32).tobytes()


def _deserialize_embedding(data: bytes) -> np.ndarray:
    """Deserialize bytes into a float32 embedding."""

    embedding = np.frombuffer(data, dtype=np.float32)
    if embedding.size != EMBEDDING_SIZE:
        raise ValueError("Invalid embedding size.")
    return embedding


def _aggregate_embeddings(images: Sequence[bytes]) -> np.ndarray:
    """Aggregate multiple image embeddings into a normalized vector."""

    if not images:
        raise ValueError("At least one image is required.")

    embeddings = [extract_embedding(img) for img in images]
    stacked = np.vstack(embeddings)
    avg = np.mean(stacked, axis=0)
    norm = np.linalg.norm(avg)
    if norm == 0:
        raise ValueError("Invalid aggregated embedding.")
    return avg / norm


def enroll(user_id: str, images: Sequence[bytes]) -> EnrollmentResult:
    """Enroll a new avatar identity.

    Args:
        user_id: User identifier.
        images: Sequence of raw image bytes.

    Returns:
        EnrollmentResult containing encrypted embedding and ACTIVE state.
    """

    aggregated = _aggregate_embeddings(images)
    encrypted = encrypt_embedding(_serialize_embedding(aggregated))
    payload = EmbeddingPayload(encrypted_embedding=encrypted, normalized=True)

    return EnrollmentResult(
        user_id=user_id,
        state=AvatarState.ACTIVE,
        payload=payload,
        created_at=utc_now(),
    )


def verify(user_id: str, image: bytes, stored_embedding: bytes) -> VerificationResult:
    """Verify a user by comparing a live image to stored embedding.

    Args:
        user_id: User identifier.
        image: Raw image bytes.
        stored_embedding: Encrypted stored embedding bytes.

    Returns:
        VerificationResult with similarity score and state.
    """

    decrypted = decrypt_embedding(stored_embedding)
    stored = _deserialize_embedding(decrypted)
    current = extract_embedding(image)
    similarity = cosine_similarity(stored, current)
    is_match = similarity >= VERIFY_THRESHOLD
    state = AvatarState.ACTIVE if is_match else AvatarState.PENDING_REFINE

    return VerificationResult(
        user_id=user_id,
        is_match=is_match,
        similarity=similarity,
        state=state,
        verified_at=utc_now(),
    )


def refine(
    user_id: str,
    images: Sequence[bytes],
    stored_embedding: bytes,
    avatar_version: int,
) -> RefineResult:
    """Refine a stored embedding using new images.

    Args:
        user_id: User identifier.
        images: Sequence of raw image bytes.
        stored_embedding: Encrypted stored embedding bytes.
        avatar_version: Current avatar version.

    Returns:
        RefineResult with possibly updated embedding and state.
    """

    decrypted = decrypt_embedding(stored_embedding)
    stored = _deserialize_embedding(decrypted)
    fresh = _aggregate_embeddings(images)
    similarity = cosine_similarity(stored, fresh)

    if similarity < REFINE_THRESHOLD:
        payload = EmbeddingPayload(encrypted_embedding=stored_embedding, normalized=True)
        return RefineResult(
            user_id=user_id,
            state=AvatarState.PENDING_REFINE,
            payload=payload,
            avatar_version=avatar_version,
            refined_at=utc_now(),
        )

    updated = 0.7 * stored + 0.3 * fresh
    norm = np.linalg.norm(updated)
    if norm == 0:
        raise ValueError("Invalid refined embedding.")
    updated = updated / norm
    encrypted = encrypt_embedding(_serialize_embedding(updated))
    payload = EmbeddingPayload(encrypted_embedding=encrypted, normalized=True)

    return RefineResult(
        user_id=user_id,
        state=AvatarState.ACTIVE,
        payload=payload,
        avatar_version=avatar_version + 1,
        refined_at=utc_now(),
    )


def apply_lock_if_needed(failed_count: int) -> AvatarState:
    """Return LOCKED state if failed_count exceeds threshold."""

    if failed_count < 0:
        raise ValueError("failed_count must be non-negative.")
    if failed_count >= LOCK_AFTER_FAILED_ATTEMPTS:
        return AvatarState.LOCKED
    return AvatarState.ACTIVE
