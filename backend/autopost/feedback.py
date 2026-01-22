from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Tuple


MIN_SAMPLES = 5
MIN_WEIGHT = 0.6
MAX_WEIGHT = 1.6


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _engagement_rate(views: int, likes: int, comments: int, shares: int) -> float:
    if views <= 0:
        return 0.0
    return (likes + comments + shares) / views


def _extract_hook_pattern(text: Optional[str]) -> str:
    if not text:
        return "none"
    lowered = text.strip().lower()
    if lowered.startswith("stop scroll"):
        return "stop_scroll"
    if lowered.startswith("aku baru sadar"):
        return "realization"
    if lowered.startswith("biar"):
        return "benefit"
    return "other"


def _extract_cta_pattern(text: Optional[str]) -> str:
    if not text:
        return "none"
    lowered = text.lower()
    if "komen" in lowered or "comment" in lowered:
        return "comment"
    if "tag" in lowered:
        return "tag"
    if "save" in lowered:
        return "save"
    if "follow" in lowered:
        return "follow"
    if "dm" in lowered:
        return "dm"
    return "other"


def _extract_hashtag_group(hashtags: Optional[str]) -> str:
    if not hashtags:
        return "none"
    lowered = hashtags.lower()
    if "#fyp" in lowered or "#foryou" in lowered:
        return "fyp"
    if "#viral" in lowered or "#trending" in lowered:
        return "viral"
    if "#ootd" in lowered:
        return "ootd"
    if "#skincare" in lowered:
        return "skincare"
    return "other"


def refresh_feedback_weights(conn, user_id: str) -> Dict[str, Dict[str, float]]:
    rows = conn.execute(
        """
        SELECT v.hook_text, v.cta_text, v.hashtags,
               m.views, m.likes, m.comments, m.shares
        FROM autopost_metrics m
        JOIN autopost_videos v ON v.id = m.video_id
        WHERE m.user_id = ?
        ORDER BY m.created_at DESC
        LIMIT 200
        """,
        (user_id,)
    ).fetchall()
    if len(rows) < MIN_SAMPLES:
        return {}

    overall_rates: List[float] = []
    hooks: Dict[str, List[float]] = {}
    ctas: Dict[str, List[float]] = {}
    hashtags: Dict[str, List[float]] = {}

    for row in rows:
        rate = _engagement_rate(
            int(row["views"] or 0),
            int(row["likes"] or 0),
            int(row["comments"] or 0),
            int(row["shares"] or 0)
        )
        overall_rates.append(rate)
        hook_key = _extract_hook_pattern(row["hook_text"])
        cta_key = _extract_cta_pattern(row["cta_text"])
        tag_key = _extract_hashtag_group(row["hashtags"])
        hooks.setdefault(hook_key, []).append(rate)
        ctas.setdefault(cta_key, []).append(rate)
        hashtags.setdefault(tag_key, []).append(rate)

    baseline = (sum(overall_rates) / len(overall_rates)) if overall_rates else 0.0
    baseline = baseline if baseline > 0 else 0.03

    def _weights_from_bucket(bucket: Dict[str, List[float]]) -> Dict[str, float]:
        weights: Dict[str, float] = {}
        for key, values in bucket.items():
            avg = sum(values) / max(1, len(values))
            ratio = avg / baseline if baseline > 0 else 1.0
            weights[key] = _clamp(ratio, MIN_WEIGHT, MAX_WEIGHT)
        return weights

    hook_weights = _weights_from_bucket(hooks)
    cta_weights = _weights_from_bucket(ctas)
    hashtag_weights = _weights_from_bucket(hashtags)

    now = datetime.utcnow().isoformat()
    for pattern_type, weights in (
        ("hook", hook_weights),
        ("cta", cta_weights),
        ("hashtag", hashtag_weights)
    ):
        for key, weight in weights.items():
            conn.execute(
                """
                INSERT INTO autopost_pattern_feedback (user_id, pattern_type, pattern_key, weight, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, pattern_type, pattern_key)
                DO UPDATE SET weight = excluded.weight, updated_at = excluded.updated_at
                """,
                (user_id, pattern_type, key, float(weight), now)
            )
    conn.commit()

    return {
        "hook": hook_weights,
        "cta": cta_weights,
        "hashtag": hashtag_weights
    }


def get_feedback_weights(conn, user_id: str) -> Dict[str, Dict[str, float]]:
    rows = conn.execute(
        """
        SELECT pattern_type, pattern_key, weight
        FROM autopost_pattern_feedback
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchall()
    result: Dict[str, Dict[str, float]] = {}
    for row in rows:
        pattern_type = row["pattern_type"]
        result.setdefault(pattern_type, {})
        result[pattern_type][row["pattern_key"]] = float(row["weight"] or 1.0)
    return result
