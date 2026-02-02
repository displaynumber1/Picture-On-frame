"""Identity module for avatar lifecycle and verification."""

from .enums import AvatarState
from .schemas import (
    AuditEvent,
    EmbeddingPayload,
    EnrollmentResult,
    RefineResult,
    VerificationResult,
)
from .lifecycle import apply_lock_if_needed, enroll, refine, verify

__all__ = [
    "AvatarState",
    "AuditEvent",
    "EmbeddingPayload",
    "EnrollmentResult",
    "RefineResult",
    "VerificationResult",
    "apply_lock_if_needed",
    "enroll",
    "refine",
    "verify",
]
