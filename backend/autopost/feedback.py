from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Tuple


MIN_SAMPLES = 5
MIN_WEIGHT = 0.6
MAX_WEIGHT = 1.6
MIN_STRENGTH = 0.5
MAX_STRENGTH = 1.4
WEEKLY_DECAY = 0.88


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
    if "diskon" in lowered or "promo" in lowered:
        return "offer"
    if lowered.endswith("?") or lowered.startswith("kenapa"):
        return "question"
    if "viral" in lowered or "ramai" in lowered:
        return "social_proof"
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
    if "klik" in lowered or "cek" in lowered:
        return "click"
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
    if "#fashion" in lowered or "#outfit" in lowered:
        return "fashion"
    if "#beauty" in lowered or "#makeup" in lowered:
        return "beauty"
    return "other"


def get_learning_strength(conn, user_id: str) -> float:
    count_row = conn.execute(
        "SELECT COUNT(*) AS total FROM autopost_metrics WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    total = int(count_row["total"] or 0) if count_row else 0
    # Strength grows with data size; cap for stability
    strength = MIN_STRENGTH + min(total / 50.0, 1.0) * (MAX_STRENGTH - MIN_STRENGTH)
    return _clamp(strength, MIN_STRENGTH, MAX_STRENGTH)


def _apply_decay(conn, table: str, where_clause: str = "", params: Tuple = ()) -> None:
    rows = conn.execute(
        f"""
        SELECT id, weight, updated_at
        FROM {table}
        {where_clause}
        """,
        params
    ).fetchall()
    now = datetime.utcnow()
    for row in rows:
        updated_at = row["updated_at"]
        try:
            last = datetime.fromisoformat(updated_at) if updated_at else now
        except Exception:
            last = now
        weeks = max(0.0, (now - last).days / 7.0)
        factor = WEEKLY_DECAY ** weeks
        new_weight = _clamp(float(row["weight"] or 1.0) * factor, MIN_WEIGHT, MAX_WEIGHT)
        conn.execute(
            f"UPDATE {table} SET weight = ?, updated_at = ? WHERE id = ?",
            (new_weight, now.isoformat(), row["id"])
        )


def refresh_feedback_weights(conn, user_id: str) -> Dict[str, Dict[str, float]]:
    _apply_decay(conn, "autopost_pattern_feedback", "WHERE user_id = ?", (user_id,))
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
    strength = get_learning_strength(conn, user_id)

    def _weights_from_bucket(bucket: Dict[str, List[float]]) -> Dict[str, float]:
        weights: Dict[str, float] = {}
        for key, values in bucket.items():
            avg = sum(values) / max(1, len(values))
            ratio = avg / baseline if baseline > 0 else 1.0
            adjusted = 1.0 + (ratio - 1.0) * strength
            weights[key] = _clamp(adjusted, MIN_WEIGHT, MAX_WEIGHT)
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


def refresh_global_feedback_weights(conn) -> Dict[str, Dict[str, float]]:
    _apply_decay(conn, "autopost_pattern_feedback_global")
    rows = conn.execute(
        """
        SELECT v.hook_text, v.cta_text, v.hashtags,
               m.views, m.likes, m.comments, m.shares
        FROM autopost_metrics m
        JOIN autopost_videos v ON v.id = m.video_id
        ORDER BY m.created_at DESC
        LIMIT 500
        """
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
        hooks.setdefault(_extract_hook_pattern(row["hook_text"]), []).append(rate)
        ctas.setdefault(_extract_cta_pattern(row["cta_text"]), []).append(rate)
        hashtags.setdefault(_extract_hashtag_group(row["hashtags"]), []).append(rate)

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
                INSERT INTO autopost_pattern_feedback_global (pattern_type, pattern_key, weight, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(pattern_type, pattern_key)
                DO UPDATE SET weight = excluded.weight, updated_at = excluded.updated_at
                """,
                (pattern_type, key, float(weight), now)
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


def get_global_feedback_weights(conn) -> Dict[str, Dict[str, float]]:
    rows = conn.execute(
        """
        SELECT pattern_type, pattern_key, weight
        FROM autopost_pattern_feedback_global
        """
    ).fetchall()
    result: Dict[str, Dict[str, float]] = {}
    for row in rows:
        pattern_type = row["pattern_type"]
        result.setdefault(pattern_type, {})
        result[pattern_type][row["pattern_key"]] = float(row["weight"] or 1.0)
    return result


def merge_weights(global_weights: Dict[str, Dict[str, float]], user_weights: Dict[str, Dict[str, float]], strength: float) -> Dict[str, Dict[str, float]]:
    alpha = 0.4
    merged: Dict[str, Dict[str, float]] = {}
    for group in ("hook", "cta", "hashtag"):
        merged[group] = {}
        keys = set(global_weights.get(group, {}).keys()) | set(user_weights.get(group, {}).keys())
        for key in keys:
            g = global_weights.get(group, {}).get(key, 1.0)
            u = user_weights.get(group, {}).get(key, 1.0)
            merged[group][key] = _clamp((alpha * u) + ((1 - alpha) * g), MIN_WEIGHT, MAX_WEIGHT)
    return merged
