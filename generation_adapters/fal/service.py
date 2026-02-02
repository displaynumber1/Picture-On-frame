"""Orchestration service for fal.ai identity-locked generation."""

from __future__ import annotations

from typing import Any, Dict, Optional, Union

from .fal_client import FalClient
from .faceid import generate_with_faceid
from .flux_edit import edit_with_flux_lora
from .schemas import StyleEditConfig


def _ensure_no_ai_generated(options: Optional[Dict[str, Any]]) -> None:
    if options and "ai_generated" in options:
        raise ValueError("ai_generated is not accepted from client input.")


def _extract_image_url(response: Dict[str, Any]) -> str:
    if "image_url" in response and isinstance(response["image_url"], str):
        return response["image_url"]
    if "image" in response and isinstance(response["image"], str):
        return response["image"]
    if "images" in response:
        images = response["images"]
        if isinstance(images, list) and images:
            first = images[0]
            if isinstance(first, str):
                return first
            if isinstance(first, dict) and "url" in first:
                return str(first["url"])
    raise ValueError("Unable to extract image URL from fal.ai response.")


async def generate_avatar(
    prompt: str,
    face_image_url_or_bytes: Union[str, bytes],
    options: Optional[Dict[str, Any]] = None,
    style_edit: Optional[StyleEditConfig] = None,
    client: Optional[FalClient] = None,
) -> str:
    """Generate an identity-locked avatar image.

    Step 1: Lock identity via FaceID.
    Step 2: Optionally apply style edit via Flux LoRA.

    Args:
        prompt: Text prompt for generation.
        face_image_url_or_bytes: Secure face image URL or bytes.
        options: Optional FaceID payload fields.
        style_edit: Optional style edit configuration.
        client: Optional FalClient instance.

    Returns:
        Final image URL.
    """

    _ensure_no_ai_generated(options)
    fal_client = client or FalClient()

    faceid_response = await generate_with_faceid(
        prompt=prompt,
        face_image_url_or_bytes=face_image_url_or_bytes,
        options=options,
        client=fal_client,
    )
    base_image_url = _extract_image_url(faceid_response)

    if not style_edit:
        return base_image_url

    _ensure_no_ai_generated(style_edit.options)
    flux_response = await edit_with_flux_lora(
        prompt=prompt,
        input_image_url=base_image_url,
        loras=style_edit.loras,
        strength=style_edit.strength,
        options=style_edit.options,
        client=fal_client,
    )
    return _extract_image_url(flux_response)
