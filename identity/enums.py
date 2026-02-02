"""Enums for identity lifecycle."""

from enum import Enum


class AvatarState(str, Enum):
    """Possible lifecycle states for an avatar identity."""

    NO_AVATAR = "NO_AVATAR"
    PENDING_ENROLL = "PENDING_ENROLL"
    ACTIVE = "ACTIVE"
    PENDING_REFINE = "PENDING_REFINE"
    LOCKED = "LOCKED"
    REVOKED = "REVOKED"
