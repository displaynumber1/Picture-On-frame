"""Flux LoRA image-to-image adapter for fal.ai."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .fal_client import FalClient


FLUX_LORA_ENDPOINT = "fal-ai/flux-lora/image-to-image"


def _ensure_no_ai_generated(options: Optional[Dict[str, Any]]) -> None:
    if options and "ai_generated" in options:
        raise ValueError("ai_generated is not accepted from client input.")


async def edit_with_flux_lora(
    prompt: str,
    input_image_url: str,
    loras: List[str],
    strength: float,
    options: Optional[Dict[str, Any]] = None,
    client: Optional[FalClient] = None,
) -> Dict[str, Any]:
    """Apply Flux LoRA style edit to an input image.

    Args:
        prompt: Text prompt.
        input_image_url: Input image URL.
        loras: List of LoRA identifiers.
        strength: LoRA strength value.
        options: Optional extra payload fields.
        client: Optional FalClient instance.

    Returns:
        fal.ai response JSON.
    """

    _ensure_no_ai_generated(options)
    payload: Dict[str, Any] = {
        "prompt": prompt,
        "image_url": input_image_url,
        "loras": loras,
        "strength": strength,
    }
    if options:
        payload.update(options)

    fal_client = client or FalClient()
    return await fal_client.call(FLUX_LORA_ENDPOINT, payload)
