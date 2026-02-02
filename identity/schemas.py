"""Typed schemas for identity lifecycle operations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .enums import AvatarState


@dataclass(frozen=True)
class EmbeddingPayload:
    """Encrypted embedding payload for storage."""

    encrypted_embedding: bytes
    normalized: bool = True


@dataclass(frozen=True)
class EnrollmentResult:
    """Result of enrollment operation."""

    user_id: str
    state: AvatarState
    payload: EmbeddingPayload
    created_at: datetime


@dataclass(frozen=True)
class VerificationResult:
    """Result of verification operation."""

    user_id: str
    is_match: bool
    similarity: float
    state: AvatarState
    verified_at: datetime


@dataclass(frozen=True)
class RefineResult:
    """Result of refinement operation."""

    user_id: str
    state: AvatarState
    payload: EmbeddingPayload
    avatar_version: int
    refined_at: datetime


@dataclass(frozen=True)
class AuditEvent:
    """Audit event schema."""

    event_type: str
    user_id: str
    occurred_at: datetime
    metadata: Dict[str, Any]
    actor: Optional[str] = None


def utc_now() -> datetime:
    """Return timezone-aware UTC timestamp."""

    return datetime.now(timezone.utc)
