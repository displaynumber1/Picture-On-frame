from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Optional
import json
import logging
import os

from fastapi import BackgroundTasks, HTTPException, UploadFile  # type: ignore

from .generator import generate_metadata, generate_variants
from .scoring import build_score_reasons
from .scheduler import get_best_posting_window, resolve_schedule_time
from .feedback import get_feedback_weights, refresh_feedback_weights


BroadcastFn = Callable[[str, str, Dict[str, Any]], Awaitable[None]]
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AutopostDeps:
    temp_dir: Path
    default_threshold: float
    scene_provider: str
    get_db_connection: Callable[[], Any]
    enforce_rate_limit: Callable[[str], None]
    get_user_profile: Callable[[str], Dict[str, Any]]
    update_user_coins: Callable[[str, int], Dict[str, Any]]
    get_trend_context: Callable[..., Any]
    get_scene_signals: Callable[[str], Optional[Dict[str, Any]]]
    score_video_metadata: Callable[..., Dict[str, Any]]
    adjust_threshold_with_feedback: Callable[[float, Dict[str, Any], float], float]
    schedule_next_check: Callable[[], str]
    now_iso: Callable[[], str]
    log_score_details: Callable[[str, Dict[str, Any]], None]
    broadcast_event: BroadcastFn
    cleanup_old_temp_videos: Callable[[], None]
    async_scene_analysis: Callable[[int, str, str], None]
    recheck_due_videos: Callable[[Any, str], int]


class AutopostService:
    def __init__(self, deps: AutopostDeps):
        self.deps = deps

    async def upload_video(
        self,
        file: UploadFile,
        title: Optional[str],
        caption: Optional[str],
        hook_text: Optional[str],
        cta_text: Optional[str],
        hashtags: Optional[str],
        category: Optional[str],
        user_id: str,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> Dict[str, Any]:
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in token")

        self.deps.enforce_rate_limit(user_id)
        profile = self.deps.get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        coins = profile.get("coins_balance", 0)
        autopost_upload_cost = 90
        if coins < autopost_upload_cost:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "INSUFFICIENT_COINS",
                    "required_coins": autopost_upload_cost,
                    "action": "topup",
                    "message": "Coins kamu tidak cukup."
                }
            )

        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")

        file_ext = Path(file.filename).suffix or ".mp4"
        safe_name = f"{user_id}_{int(datetime.now().timestamp())}_{os.urandom(4).hex()}{file_ext}"
        file_path = self.deps.temp_dir / safe_name

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        trend_list, _, _ = self.deps.get_trend_context(title, caption, hook_text, cta_text, hashtags, category)
        trend_tag = trend_list[0] if trend_list else None

        conn = self.deps.get_db_connection()
        refresh_feedback_weights(conn, user_id)
        weights = get_feedback_weights(conn, user_id)

        if title or hook_text or cta_text or hashtags:
            generated = generate_metadata(title, hook_text, cta_text, hashtags, category, trend_tag=trend_tag)
            title = generated.title
            hook_text = generated.hook_text
            cta_text = generated.cta_text
            hashtags = generated.hashtags
            sources = generated.sources
        else:
            variants = generate_variants(category, trend_tag, weights, count=5)
            scored_variants: List[Dict[str, Any]] = []
            for variant in variants:
                details = self.deps.score_video_metadata(
                    variant.title,
                    caption,
                    variant.hook_text,
                    variant.cta_text,
                    variant.hashtags,
                    category,
                    user_id,
                    None
                )
                scored_variants.append({
                    "variant": variant,
                    "score": float(details.get("score", 0.0))
                })
            scored_variants.sort(key=lambda v: v["score"], reverse=True)
            best = scored_variants[0]["variant"]
            logger.info(f"[AI VARIANTS] video={file.filename} scores={[round(v['score'], 2) for v in scored_variants]}")
            logger.info(f"[AI VARIANTS] selected hook_pattern={best.hook_pattern} cta_pattern={best.cta_pattern} hashtag_pattern={best.hashtag_pattern}")
            title = best.title
            hook_text = best.hook_text
            cta_text = best.cta_text
            hashtags = best.hashtags
            sources = {
                "title_source": "ai_generated",
                "hook_source": "ai_generated",
                "cta_source": "ai_generated",
                "hashtags_source": "ai_generated"
            }

        scene_signals = self.deps.get_scene_signals(str(file_path))
        details = self.deps.score_video_metadata(
            title,
            caption,
            hook_text,
            cta_text,
            hashtags,
            category,
            user_id,
            scene_signals
        )
        score = float(details.get("score", 0.0))
        threshold = self.deps.adjust_threshold_with_feedback(
            self.deps.default_threshold,
            details.get("feedback") or {},
            float(details.get("trend_similarity") or 0.0)
        )
        details["threshold"] = threshold
        score_reasons = build_score_reasons(details, title, hook_text, cta_text, hashtags, category)
        self.deps.log_score_details(f"user={user_id} video={file.filename}", details)

        compliance_blocked = bool(details.get("compliance_blocked"))
        if compliance_blocked:
            status = "WAITING_RECHECK"
            next_check_at = self.deps.schedule_next_check()
        else:
            status = "QUEUED" if score >= threshold else "WAITING_RECHECK"
            next_check_at = None if status == "QUEUED" else self.deps.schedule_next_check()

        cursor = conn.cursor()
        scheduled_at = None
        status_note = None
        if status == "QUEUED":
            preferred_window = get_best_posting_window(conn, user_id)
            scheduled_at_dt = resolve_schedule_time(datetime.now(), preferred_window)
            if scheduled_at_dt:
                scheduled_at = scheduled_at_dt.isoformat()
                status_note = "scheduled"

        cursor.execute(
            """
            INSERT INTO autopost_videos
            (user_id, file_name, file_path, title, caption, hook_text, cta_text, hashtags, category,
             title_source, hook_source, cta_source, hashtags_source,
             status, score, score_details, score_reasons, threshold, next_check_at, scheduled_at, status_note,
             created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                file.filename,
                str(file_path),
                title,
                caption,
                hook_text,
                cta_text,
                hashtags,
                category,
                sources.get("title_source"),
                sources.get("hook_source"),
                sources.get("cta_source"),
                sources.get("hashtags_source"),
                status,
                score,
                json.dumps(details),
                json.dumps(score_reasons),
                threshold,
                next_check_at,
                scheduled_at,
                status_note,
                self.deps.now_iso(),
                self.deps.now_iso()
            )
        )
        record_id = cursor.lastrowid
        conn.commit()
        updated_profile = self.deps.update_user_coins(user_id, -autopost_upload_cost)
        remaining_coins = updated_profile.get("coins_balance", 0) if updated_profile else coins - autopost_upload_cost

        if self.deps.scene_provider != "none" and background_tasks is not None:
            background_tasks.add_task(self.deps.async_scene_analysis, record_id, str(file_path), user_id)
        conn.close()

        response_payload = {
            "id": record_id,
            "status": status,
            "score": score,
            "threshold": threshold,
            "next_check_at": next_check_at,
            "scheduled_at": scheduled_at,
            "status_note": status_note,
            "score_reasons": score_reasons,
            "remaining_coins": remaining_coins
        }
        self.deps.cleanup_old_temp_videos()
        await self.deps.broadcast_event(
            user_id,
            "autopost.updated",
            {"id": record_id, "status": status, "score": score, "next_check_at": next_check_at, "video_name": file.filename}
        )
        return response_payload

    def dashboard(self, user_id: str, status: Optional[str]) -> Dict[str, Any]:
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in token")

        conn = self.deps.get_db_connection()
        self.deps.recheck_due_videos(conn, user_id)
        self.deps.cleanup_old_temp_videos()
        if status:
            rows = conn.execute(
                "SELECT * FROM autopost_videos WHERE user_id = ? AND status = ? ORDER BY created_at DESC",
                (user_id, status)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM autopost_videos WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,)
            ).fetchall()
        conn.close()

        items = []
        for row in rows:
            item = dict(row)
            try:
                item["score_details"] = json.loads(item.get("score_details") or "{}")
            except Exception:
                item["score_details"] = {}
            try:
                item["score_reasons"] = json.loads(item.get("score_reasons") or "[]")
            except Exception:
                item["score_reasons"] = []
            item["video_name"] = item.get("file_name")
            item["credit_used"] = item.get("credit_used") if "credit_used" in item else 0
            items.append(item)
        return {"items": items}

    def regenerate_metadata(self, user_id: str, video_id: int) -> Dict[str, Any]:
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in token")

        conn = self.deps.get_db_connection()
        row = conn.execute(
            "SELECT * FROM autopost_videos WHERE id = ? AND user_id = ?",
            (video_id, user_id)
        ).fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Video not found")

        category = row["category"]
        caption = row["caption"]
        file_path = row["file_path"]
        current_status = row["status"]

        trend_list, _, _ = self.deps.get_trend_context(None, caption, None, None, None, category)
        trend_tag = trend_list[0] if trend_list else None
        refresh_feedback_weights(conn, user_id)
        weights = get_feedback_weights(conn, user_id)

        variants = generate_variants(category, trend_tag, weights, count=5)
        scored_variants: List[Dict[str, Any]] = []
        for variant in variants:
            details = self.deps.score_video_metadata(
                variant.title,
                caption,
                variant.hook_text,
                variant.cta_text,
                variant.hashtags,
                category,
                user_id,
                None
            )
            scored_variants.append({
                "variant": variant,
                "score": float(details.get("score", 0.0))
            })
        scored_variants.sort(key=lambda v: v["score"], reverse=True)
        best = scored_variants[0]["variant"]
        logger.info(f"[AI VARIANTS] video_id={video_id} scores={[round(v['score'], 2) for v in scored_variants]}")
        logger.info(f"[AI VARIANTS] selected hook_pattern={best.hook_pattern} cta_pattern={best.cta_pattern} hashtag_pattern={best.hashtag_pattern}")

        title = best.title
        hook_text = best.hook_text
        cta_text = best.cta_text
        hashtags = best.hashtags

        logger.info(f"[AI GENERATE] video_id={video_id}")
        logger.info(f"Generated hook: {hook_text}")

        scene_signals = self.deps.get_scene_signals(str(file_path)) if file_path else None
        details = self.deps.score_video_metadata(
            title,
            caption,
            hook_text,
            cta_text,
            hashtags,
            category,
            user_id,
            scene_signals
        )
        score = float(details.get("score", 0.0))
        threshold = self.deps.adjust_threshold_with_feedback(
            self.deps.default_threshold,
            details.get("feedback") or {},
            float(details.get("trend_similarity") or 0.0)
        )
        details["threshold"] = threshold
        score_reasons = build_score_reasons(details, title, hook_text, cta_text, hashtags, category)
        logger.info(f"Score after regenerate: {score}")

        compliance_blocked = bool(details.get("compliance_blocked"))
        next_check_at = None
        scheduled_at = None
        status_note = None
        new_status = current_status

        if current_status in ("QUEUED", "WAITING_RECHECK"):
            if compliance_blocked:
                new_status = "WAITING_RECHECK"
                next_check_at = self.deps.schedule_next_check()
            else:
                new_status = "QUEUED" if score >= threshold else "WAITING_RECHECK"
                next_check_at = None if new_status == "QUEUED" else self.deps.schedule_next_check()

            if new_status == "QUEUED":
                preferred_window = get_best_posting_window(conn, user_id)
                scheduled_at_dt = resolve_schedule_time(datetime.now(), preferred_window)
                if scheduled_at_dt:
                    scheduled_at = scheduled_at_dt.isoformat()
                    status_note = "scheduled"

        conn.execute(
            """
            UPDATE autopost_videos
            SET title = ?, hook_text = ?, cta_text = ?, hashtags = ?,
                title_source = ?, hook_source = ?, cta_source = ?, hashtags_source = ?,
                score = ?, score_details = ?, score_reasons = ?, threshold = ?,
                status = ?, next_check_at = ?, scheduled_at = ?, status_note = ?,
                updated_at = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                title,
                hook_text,
                cta_text,
                hashtags,
                "ai_generated",
                "ai_generated",
                "ai_generated",
                "ai_generated",
                score,
                json.dumps(details),
                json.dumps(score_reasons),
                threshold,
                new_status,
                next_check_at,
                scheduled_at,
                status_note,
                self.deps.now_iso(),
                video_id,
                user_id
            )
        )
        conn.commit()
        conn.close()

        hashtag_list = [tag for tag in (hashtags or "").split() if tag]
        return {
            "title": title,
            "hook": hook_text,
            "cta": cta_text,
            "hashtags": hashtag_list,
            "score": score,
            "score_reasons": score_reasons
        }
