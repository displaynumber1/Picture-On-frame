from typing import Optional, Tuple

import cv2
import numpy as np


def _alpha_blend(base_bgr, overlay_rgba):
    overlay_rgb = overlay_rgba[:, :, :3].astype(np.float32)
    alpha = (overlay_rgba[:, :, 3:4].astype(np.float32)) / 255.0
    base = base_bgr.astype(np.float32)
    blended = (alpha * overlay_rgb) + ((1 - alpha) * base)
    return blended.astype(np.uint8)


def apply_hand_occlusion(
    base_image,
    bag_layer_rgba,
    hand_mask,
    hand_region: Optional[Tuple[int, int, int, int]] = None
):
    if base_image is None or bag_layer_rgba is None:
        raise ValueError("base_image and bag_layer_rgba are required")

    composite = _alpha_blend(base_image, bag_layer_rgba)

    if hand_mask is None:
        return composite

    mask = hand_mask.astype(bool)
    composite[mask] = base_image[mask]
    return composite
