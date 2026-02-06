from typing import Dict, Optional, Tuple

import cv2
import mediapipe as mp
import numpy as np


def segment_person(
    image_bgr,
    wrist: Optional[Tuple[int, int]] = None,
    hand_radius: Optional[int] = None
) -> Dict[str, object]:
    if image_bgr is None:
        raise ValueError("image_bgr is required")

    height, width = image_bgr.shape[:2]
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    segmenter = mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=1)
    result = segmenter.process(image_rgb)
    segmenter.close()

    if result.segmentation_mask is None:
        raise ValueError("Segmentation mask not available")

    mask = (result.segmentation_mask > 0.1).astype(np.uint8) * 255
    body_mask = mask

    hand_mask = np.zeros_like(body_mask)
    hand_region = None
    if wrist:
        radius = hand_radius or int(min(height, width) * 0.08)
        cx, cy = wrist
        circle = np.zeros_like(body_mask)
        cv2.circle(circle, (int(cx), int(cy)), int(radius), 255, -1)
        hand_mask = cv2.bitwise_and(body_mask, circle)
        x0 = max(int(cx - radius), 0)
        y0 = max(int(cy - radius), 0)
        x1 = min(int(cx + radius), width - 1)
        y1 = min(int(cy + radius), height - 1)
        hand_region = (x0, y0, x1, y1)

    return {
        "body_mask": body_mask,
        "hand_mask": hand_mask,
        "hand_region": hand_region,
    }
