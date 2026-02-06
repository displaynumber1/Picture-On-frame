import math
from typing import Dict, Tuple

import cv2
import mediapipe as mp


def detect_right_wrist(image_bgr) -> Dict[str, object]:
    if image_bgr is None:
        raise ValueError("image_bgr is required")

    height, width = image_bgr.shape[:2]
    image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    pose = mp.solutions.pose.Pose(
        static_image_mode=True,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.5,
    )
    results = pose.process(image_rgb)
    pose.close()

    if not results.pose_landmarks:
        raise ValueError("Pose landmarks not detected")

    landmarks = results.pose_landmarks.landmark
    right_wrist = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_WRIST.value]
    right_elbow = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_ELBOW.value]

    if right_wrist.visibility < 0.5:
        raise ValueError("Right wrist confidence too low")

    wrist_x = int(right_wrist.x * width)
    wrist_y = int(right_wrist.y * height)
    elbow_x = int(right_elbow.x * width)
    elbow_y = int(right_elbow.y * height)

    angle = math.atan2(wrist_y - elbow_y, wrist_x - elbow_x)

    return {
        "wrist": (wrist_x, wrist_y),
        "angle": angle,
        "confidence": right_wrist.visibility,
    }
