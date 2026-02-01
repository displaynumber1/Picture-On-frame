import asyncio
import io
import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import HTTPException
from fastapi.testclient import TestClient

import main as app_module
from autopost import scheduler as scheduler_module
from autopost.service import AutopostDeps, AutopostService


def _noop(*_args, **_kwargs):
    return None


async def _noop_async(*_args, **_kwargs):
    return None


def _build_test_service(temp_dir: Path, active_tasks_state: dict) -> AutopostService:
    def active_tasks(_user_id: str) -> int:
        return int(active_tasks_state.get("count", 0))

    deps = AutopostDeps(
        temp_dir=temp_dir,
        default_threshold=7.0,
        scene_provider="none",
        get_db_connection=app_module.get_db_connection,
        enforce_rate_limit=_noop,
        get_user_profile=lambda _user_id: {
            "trial_upload_remaining": 3,
            "subscribed": False
        },
        update_user_trial_remaining=_noop,
        update_user_coins=_noop,
        get_trend_context=lambda *_args, **_kwargs: ([], None, None),
        get_scene_signals=lambda *_args, **_kwargs: None,
        score_video_metadata=lambda *_args, **_kwargs: {"score": 9.5, "feedback": {}, "trend_similarity": 0.0},
        adjust_threshold_with_feedback=lambda default, *_args, **_kwargs: default,
        schedule_next_check=app_module._schedule_next_check,
        now_iso=app_module._now_iso,
        log_score_details=_noop,
        broadcast_event=_noop_async,
        cleanup_old_temp_videos=_noop,
        async_scene_analysis=_noop_async,
        recheck_due_videos=lambda *_args, **_kwargs: 0,
        active_tasks=active_tasks
    )
    return AutopostService(deps)


class _StreamingUpload:
    def __init__(self, filename: str, content_type: str, total_bytes: int, chunk_size: int):
        self.filename = filename
        self.content_type = content_type
        self._remaining = total_bytes
        self._chunk_size = chunk_size

    async def read(self, _size: int = -1) -> bytes:
        if self._remaining <= 0:
            return b""
        to_send = min(self._chunk_size, self._remaining)
        self._remaining -= to_send
        return b"x" * to_send


def _insert_video(conn, user_id: str, file_name: str, file_path: str, status: str) -> int:
    now = app_module._now_iso()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO autopost_videos
        (user_id, file_name, file_path, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, file_name, file_path, status, now, now)
    )
    conn.commit()
    return int(cursor.lastrowid)


def run_sanity_tests():
    with tempfile.TemporaryDirectory() as tmp:
        base_dir = Path(tmp).resolve()
        db_path = base_dir / "test_autopost.db"

        app_module.DB_PATH = db_path
        app_module.init_database()
        app_module.SAFE_VIDEO_BASE = base_dir
        app_module.SAFE_TEMP_BASE = base_dir

        active_tasks_state = {"count": 0}
        service = _build_test_service(base_dir, active_tasks_state)
        app_module.autopost_service.deps = service.deps

        def override_current_user():
            return {"id": "test-user", "role": "user"}

        app_module.app.dependency_overrides[app_module.get_current_user] = override_current_user
        client = TestClient(app_module.app)

        # download path guard
        safe_video = base_dir / "video.mp4"
        safe_video.write_bytes(b"video")
        conn = app_module.get_db_connection()
        video_id = _insert_video(conn, "test-user", "video.mp4", str(safe_video), "QUEUED")
        conn.close()
        resp = client.get(f"/api/autopost/video/{video_id}")
        assert resp.status_code == 200

        unsafe_video = (base_dir / ".." / "evil.mp4").resolve()
        unsafe_video.write_bytes(b"evil")
        conn = app_module.get_db_connection()
        unsafe_id = _insert_video(conn, "test-user", "evil.mp4", str(unsafe_video), "QUEUED")
        conn.close()
        resp = client.get(f"/api/autopost/video/{unsafe_id}")
        assert resp.status_code == 403

        # retry state guard
        conn = app_module.get_db_connection()
        failed_id = _insert_video(conn, "test-user", "failed.mp4", str(safe_video), "FAILED")
        queued_id = _insert_video(conn, "test-user", "queued.mp4", str(safe_video), "QUEUED")
        conn.close()
        resp = client.post(f"/api/autopost/tasks/{failed_id}/retry")
        assert resp.status_code == 200
        resp = client.post(f"/api/autopost/tasks/{queued_id}/retry")
        assert resp.status_code == 400

        # complete state guard
        conn = app_module.get_db_connection()
        in_progress_id = _insert_video(conn, "test-user", "prog.mp4", str(safe_video), "IN_PROGRESS")
        invalid_id = _insert_video(conn, "test-user", "invalid.mp4", str(safe_video), "QUEUED")
        conn.close()
        resp = client.post(
            f"/api/autopost/tasks/{in_progress_id}/complete",
            json={"status": "POSTED", "error": None}
        )
        assert resp.status_code == 200
        resp = client.post(
            f"/api/autopost/tasks/{in_progress_id}/complete",
            json={"status": "POSTED", "error": None}
        )
        assert resp.status_code == 409
        resp = client.post(
            f"/api/autopost/tasks/{invalid_id}/complete",
            json={"status": "POSTED", "error": None}
        )
        assert resp.status_code == 400

        # retry-variant guard
        conn = app_module.get_db_connection()
        failed_variant_id = _insert_video(conn, "test-user", "failedv.mp4", str(safe_video), "FAILED")
        queued_variant_id = _insert_video(conn, "test-user", "queuedv.mp4", str(safe_video), "QUEUED")
        conn.close()
        resp = client.post(f"/api/autopost/tasks/{failed_variant_id}/retry-variant")
        assert resp.status_code == 200
        resp = client.post(f"/api/autopost/tasks/{queued_variant_id}/retry-variant")
        assert resp.status_code == 409

        # upload guards: concurrency and extension allowlist
        active_tasks_state["count"] = 4
        resp = client.post(
            "/api/autopost/upload",
            files={"file": ("video.mp4", io.BytesIO(b"video"), "video/mp4")}
        )
        assert resp.status_code == 429
        active_tasks_state["count"] = 0
        resp = client.post(
            "/api/autopost/upload",
            files={"file": ("video.txt", io.BytesIO(b"text"), "text/plain")}
        )
        assert resp.status_code == 400

        # generate-image validation: missing prompt + invalid base64
        original_get_user_profile = app_module.get_user_profile
        original_update_user_coins = app_module.update_user_coins
        app_module.get_user_profile = lambda _user_id: {"coins_balance": 1000}
        app_module.update_user_coins = _noop
        try:
            resp = client.post("/api/generate-image", json={})
            assert resp.status_code == 422
            resp = client.post("/api/generate-image", json={
                "prompt": "test",
                "product_images": ["not_base64"]
            })
            assert resp.status_code == 422
            resp = client.post("/api/generate-image", json={
                "prompt": "test"
            })
            assert resp.status_code == 422
            resp = client.post(
                "/api/generate-image",
                files={"image": ("image.png", io.BytesIO(b"fake"), "image/png")}
            )
            assert resp.status_code == 422
            resp = client.post(
                "/api/generate-image",
                files={"prompt": (None, "test")}
            )
            assert resp.status_code == 422
            resp = client.post(
                "/api/generate-image",
                json={
                    "prompt": "test",
                    "product_images": ["data:image/;base64,AAAA"]
                }
            )
            assert resp.status_code == 422
            resp = client.post(
                "/api/generate-image",
                files={
                    "prompt": (None, "test"),
                    "image": ("empty.png", io.BytesIO(b""), "image/png")
                }
            )
            assert resp.status_code == 422
            resp = client.post(
                "/api/generate-image",
                files={
                    "prompt": (None, "test"),
                    "image": ("note.txt", io.BytesIO(b"hello"), "text/plain")
                }
            )
            assert resp.status_code == 422
        finally:
            app_module.get_user_profile = original_get_user_profile
            app_module.update_user_coins = original_update_user_coins

        # scheduler: resolve_schedule_time
        now_in_window = datetime(2024, 1, 1, 11, 30, 0)
        assert scheduler_module.resolve_schedule_time(now_in_window) is None
        now_before_window = datetime(2024, 1, 1, 10, 0, 0)
        next_start = scheduler_module.resolve_schedule_time(now_before_window)
        assert next_start is not None
        assert next_start.hour == 11
        assert next_start.date() == now_before_window.date()
        now_after_window = datetime(2024, 1, 1, 23, 0, 0)
        next_start = scheduler_module.resolve_schedule_time(now_after_window)
        assert next_start is not None
        assert next_start.hour == 11
        assert next_start.date() == (now_after_window + timedelta(days=1)).date()

        preferred = (8, 10)
        assert scheduler_module.resolve_schedule_time(datetime(2024, 1, 1, 9, 0, 0), preferred) is None
        preferred_start = scheduler_module.resolve_schedule_time(datetime(2024, 1, 1, 10, 0, 0), preferred)
        assert preferred_start is not None
        assert preferred_start.hour == 8

        # scheduler: get_best_posting_window
        conn = app_module.get_db_connection()
        conn.execute("DELETE FROM autopost_metrics WHERE user_id = ?", ("test-user",))
        samples = [
            ("2024-01-01T09:00:00", 100, 5, 2, 1),   # 0.08
            ("2024-01-02T09:30:00", 100, 6, 2, 1),   # 0.09
            ("2024-01-03T09:45:00", 100, 5, 1, 1),   # 0.07
            ("2024-01-04T15:00:00", 100, 30, 10, 10),  # 0.50
            ("2024-01-05T15:15:00", 100, 25, 10, 5),   # 0.40
        ]
        for posted_at, views, likes, comments, shares in samples:
            conn.execute(
                """
                INSERT INTO autopost_metrics
                (user_id, video_id, views, likes, comments, shares, posted_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                ("test-user", 1, views, likes, comments, shares, posted_at, app_module._now_iso())
            )
        conn.commit()
        window = scheduler_module.get_best_posting_window(conn, "test-user")
        conn.close()
        assert window is not None
        assert window[0] == 15
        assert window[1] == 17

        # upload size limit (streaming)
        oversized = _StreamingUpload(
            filename="big.mp4",
            content_type="video/mp4",
            total_bytes=(151 * 1024 * 1024),
            chunk_size=(1024 * 1024)
        )
        try:
            asyncio.run(
                service.upload_video(
                    file=oversized,
                    title=None,
                    caption=None,
                    hook_text=None,
                    cta_text=None,
                    hashtags=None,
                    category=None,
                    user_id="test-user",
                    background_tasks=None
                )
            )
            assert False, "Expected 413 for oversized upload"
        except HTTPException as exc:
            assert exc.status_code == 413

        # service MIME whitelist (bypass guard)
        bad_mime = _StreamingUpload(
            filename="video.mp4",
            content_type="video/avi",
            total_bytes=1024,
            chunk_size=512
        )
        try:
            asyncio.run(
                service.upload_video(
                    file=bad_mime,
                    title=None,
                    caption=None,
                    hook_text=None,
                    cta_text=None,
                    hashtags=None,
                    category=None,
                    user_id="test-user",
                    background_tasks=None
                )
            )
            assert False, "Expected 400 for invalid MIME type"
        except HTTPException as exc:
            assert exc.status_code == 400

        print("Autopost sanity tests passed.")


if __name__ == "__main__":
    run_sanity_tests()
