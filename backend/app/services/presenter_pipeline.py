import io
import math
from typing import Dict, Optional, Tuple

import cv2
import httpx
import numpy as np

from app.services.landmark_service import detect_right_wrist
from app.services.person_segmentation_service import segment_person
from app.services.occlusion_service import apply_hand_occlusion


def _decode_image_bytes(image_bytes: bytes, with_alpha: bool = False):
    data = np.frombuffer(image_bytes, np.uint8)
    flag = cv2.IMREAD_UNCHANGED if with_alpha else cv2.IMREAD_COLOR
    img = cv2.imdecode(data, flag)
    if img is None:
        raise ValueError("Failed to decode image bytes")
    return img


async def _download_image_bgr(url: str, with_alpha: bool = False):
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return _decode_image_bytes(resp.content, with_alpha=with_alpha)


def _segment_product_bgr(product_bgra) -> Tuple[np.ndarray, np.ndarray]:
    if product_bgra is None:
        raise ValueError("product image is required")
    if product_bgra.shape[2] == 4:
        bgr = product_bgra[:, :, :3]
        alpha = product_bgra[:, :, 3]
        mask = alpha.astype(np.uint8)
        return bgr, mask
    mask = np.ones(product_bgra.shape[:2], dtype=np.uint8) * 255
    return product_bgra, mask


def _rotate_with_bounds(image, angle_rad: float):
    angle_deg = math.degrees(angle_rad)
    (h, w) = image.shape[:2]
    center = (w / 2, h / 2)
    mat = cv2.getRotationMatrix2D(center, angle_deg, 1.0)
    cos = abs(mat[0, 0])
    sin = abs(mat[0, 1])
    new_w = int((h * sin) + (w * cos))
    new_h = int((h * cos) + (w * sin))
    mat[0, 2] += (new_w / 2) - center[0]
    mat[1, 2] += (new_h / 2) - center[1]
    rotated = cv2.warpAffine(image, mat, (new_w, new_h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_TRANSPARENT)
    return rotated


def _place_rgba_on_canvas(canvas_shape, overlay_rgba, center_xy: Tuple[int, int]):
    canvas_h, canvas_w = canvas_shape[:2]
    overlay_h, overlay_w = overlay_rgba.shape[:2]
    cx, cy = center_xy
    x0 = int(cx - overlay_w / 2)
    y0 = int(cy - overlay_h / 2)
    x1 = x0 + overlay_w
    y1 = y0 + overlay_h

    canvas = np.zeros((canvas_h, canvas_w, 4), dtype=np.uint8)

    ox0 = max(0, -x0)
    oy0 = max(0, -y0)
    ox1 = overlay_w - max(0, x1 - canvas_w)
    oy1 = overlay_h - max(0, y1 - canvas_h)

    cx0 = max(0, x0)
    cy0 = max(0, y0)
    cx1 = cx0 + (ox1 - ox0)
    cy1 = cy0 + (oy1 - oy0)

    if cx1 > cx0 and cy1 > cy0:
        canvas[cy0:cy1, cx0:cx1] = overlay_rgba[oy0:oy1, ox0:ox1]

    return canvas


async def run_presenter_one_hand(
    product_main_url: str,
    render_plan: Dict[str, object],
    fal_service,
    supabase_service
) -> Dict[str, object]:
    if not product_main_url:
        raise ValueError("product_main_url is required")

    base_image_url = render_plan.get("base_image_url")
    user_id = render_plan.get("user_id")
    if not base_image_url:
        raise ValueError("base_image_url is required for presenter pipeline")

    prompt = (
        "female model standing, right hand extended forward as if holding an object, "
        "hand clearly visible, no accessories, clean studio lighting, natural pose, "
        "front facing, no object in hand"
    )

    last_error = None
    for _ in range(3):
        try:
            model_urls = await fal_service.generate_images(
                prompt=prompt,
                num_images=1,
                image_url=base_image_url,
                image_strength=render_plan.get("strength"),
                num_inference_steps=render_plan.get("num_inference_steps"),
                guidance_scale=render_plan.get("guidance_scale"),
                negative_prompt=render_plan.get("negative_prompt"),
                image_size=render_plan.get("image_size"),
                ip_adapters=[]
            )
            model_url = model_urls[0]
            model_image_bgr = await _download_image_bgr(model_url)
            wrist_info = detect_right_wrist(model_image_bgr)
            break
        except Exception as e:
            last_error = e
            wrist_info = None
            model_image_bgr = None
    if not wrist_info or model_image_bgr is None:
        raise ValueError(f"Failed to detect right wrist after retries: {last_error}")

    seg = segment_person(model_image_bgr, wrist=wrist_info["wrist"])
    hand_mask = seg["hand_mask"]
    hand_region = seg["hand_region"]

    product_bgra = await _download_image_bgr(product_main_url, with_alpha=True)
    bag_bgr, bag_mask = _segment_product_bgr(product_bgra)

    model_h, model_w = model_image_bgr.shape[:2]
    target_height = int(model_h * 0.30)
    scale = target_height / max(1, bag_bgr.shape[0])
    bag_resized = cv2.resize(bag_bgr, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    mask_resized = cv2.resize(bag_mask, (bag_resized.shape[1], bag_resized.shape[0]), interpolation=cv2.INTER_NEAREST)
    bag_rgba = np.dstack([bag_resized, mask_resized])

    bag_rotated = _rotate_with_bounds(bag_rgba, wrist_info["angle"])
    bag_layer = _place_rgba_on_canvas(model_image_bgr.shape, bag_rotated, wrist_info["wrist"])

    composed = apply_hand_occlusion(model_image_bgr, bag_layer, hand_mask, hand_region)

    _, buffer = cv2.imencode(".jpg", composed, [int(cv2.IMWRITE_JPEG_QUALITY), 92])
    output_bytes = buffer.tobytes()

    file_name = "presenter_one_hand.jpg"
    output_url = supabase_service.upload_image_to_supabase_storage(
        file_content=output_bytes,
        file_name=file_name,
        bucket_name="IMAGES_UPLOAD",
        user_id=user_id,
        category="presenter"
    )

    return {"output_url": output_url, "interaction": "one_hand_hold"}
