"""Audit event generation utilities."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .schemas import AuditEvent, utc_now


def build_audit_event(
    event_type: str,
    user_id: str,
    metadata: Dict[str, Any],
    actor: Optional[str] = None,
) -> Dict[str, Any]:
    """Create an audit event dictionary.

    This function does not persist events.
    """

    event = AuditEvent(
        event_type=event_type,
        user_id=user_id,
        occurred_at=utc_now(),
        metadata=metadata,
        actor=actor,
    )
    return {
        "event_type": event.event_type,
        "user_id": event.user_id,
        "occurred_at": event.occurred_at.isoformat(),
        "metadata": event.metadata,
        "actor": event.actor,
    }
