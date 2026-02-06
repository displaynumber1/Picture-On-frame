"""FaceID generation adapter for fal."""

from __future__ import annotations

import base64
from typing import Any, Dict, Optional, Union

from .fal_client import FalClient


FACE_ID_ENDPOINT = "fal-ai/ip-adapter-face-id"


def _ensure_no_ai_generated(options: Optional[Dict[str, Any]]) -> None:
    if options and "ai_generated" in options:
        raise ValueError("ai_generated is not accepted from client input.")


def _to_data_url(image_bytes: bytes) -> str:
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


async def generate_with_faceid(
    prompt: str,
    face_image_url_or_bytes: Union[str, bytes],
    options: Optional[Dict[str, Any]] = None,
    client: Optional[FalClient] = None,
) -> Dict[str, Any]:
    """Generate an image using FaceID identity lock.

    Args:
        prompt: Text prompt.
        face_image_url_or_bytes: URL or raw image bytes.
        options: Optional extra payload fields.
        client: Optional FalClient instance.

    Returns:
        fal response JSON.
    """

    _ensure_no_ai_generated(options)
    face_input = (
        _to_data_url(face_image_url_or_bytes)
        if isinstance(face_image_url_or_bytes, (bytes, bytearray))
        else face_image_url_or_bytes
    )
    payload: Dict[str, Any] = {"prompt": prompt, "face_image_url": face_input}
    if options:
        payload.update(options)

    fal_client = client or FalClient()
    return await fal_client.call(FACE_ID_ENDPOINT, payload)
