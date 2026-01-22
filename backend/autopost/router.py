from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile  # type: ignore
from typing import Any, Dict, Optional, Callable

from .service import AutopostService


def create_autopost_router(
    service: AutopostService,
    get_current_user: Callable[..., Dict[str, Any]]
) -> APIRouter:
    router = APIRouter()

    @router.post("/api/autopost/upload")
    async def autopost_upload_video(
        file: UploadFile = File(...),
        title: Optional[str] = Form(None),
        caption: Optional[str] = Form(None),
        hook_text: Optional[str] = Form(None),
        cta_text: Optional[str] = Form(None),
        hashtags: Optional[str] = Form(None),
        category: Optional[str] = Form(None),
        background_tasks: BackgroundTasks = None,
        current_user: Dict[str, Any] = Depends(get_current_user)
    ):
        user_id = current_user.get("id")
        return await service.upload_video(
            file=file,
            title=title,
            caption=caption,
            hook_text=hook_text,
            cta_text=cta_text,
            hashtags=hashtags,
            category=category,
            user_id=user_id,
            background_tasks=background_tasks
        )

    @router.get("/api/autopost/dashboard")
    async def autopost_dashboard(
        status: Optional[str] = None,
        current_user: Dict[str, Any] = Depends(get_current_user)
    ):
        user_id = current_user.get("id")
        return service.dashboard(user_id, status)

    return router
