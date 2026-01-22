from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable, List, Optional, Tuple


DEFAULT_WINDOWS: List[Tuple[int, int]] = [(11, 13), (19, 22)]
MIN_METRICS_FOR_ADAPTIVE = 5


def _within_window(now: datetime, start_hour: int, end_hour: int) -> bool:
    return start_hour <= now.hour < end_hour


def _next_window_start(now: datetime, windows: Iterable[Tuple[int, int]]) -> datetime:
    candidates = []
    for start_hour, _ in windows:
        candidate = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(days=1)
        candidates.append(candidate)
    return min(candidates)


def resolve_schedule_time(
    now: datetime,
    preferred_window: Optional[Tuple[int, int]] = None
) -> Optional[datetime]:
    windows = [preferred_window] if preferred_window else DEFAULT_WINDOWS
    for start_hour, end_hour in windows:
        if _within_window(now, start_hour, end_hour):
            return None
    return _next_window_start(now, windows)


def get_best_posting_window(conn, user_id: str) -> Optional[Tuple[int, int]]:
    """
    Compute best posting window per user using autopost_metrics.
    Returns (start_hour, end_hour) or None if insufficient data.
    """
    rows = conn.execute(
        """
        SELECT views, likes, comments, shares, posted_at, created_at
        FROM autopost_metrics
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 200
        """,
        (user_id,)
    ).fetchall()
    if not rows or len(rows) < MIN_METRICS_FOR_ADAPTIVE:
        return None

    hourly_scores = {}
    hourly_counts = {}
    for row in rows:
        timestamp = row["posted_at"] or row["created_at"]
        if not timestamp:
            continue
        try:
            dt = datetime.fromisoformat(timestamp)
        except ValueError:
            continue
        hour = dt.hour
        views = int(row["views"] or 0)
        likes = int(row["likes"] or 0)
        comments = int(row["comments"] or 0)
        shares = int(row["shares"] or 0)
        engagement = (likes + comments + shares) / max(1, views)
        hourly_scores[hour] = hourly_scores.get(hour, 0.0) + engagement
        hourly_counts[hour] = hourly_counts.get(hour, 0) + 1

    if not hourly_scores:
        return None

    best_hour = max(hourly_scores.keys(), key=lambda h: hourly_scores[h] / max(1, hourly_counts.get(h, 1)))
    return (best_hour, min(24, best_hour + 2))
