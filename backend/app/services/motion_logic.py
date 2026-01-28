"""
Motion Logic: Dynamic motion generation based on model type, character, and product category
Generates 3 different motion variations per image
"""

import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def detect_product_region(image_path: str) -> Dict[str, float]:
    """
    Detect main product region in image using simple saliency detection.
    Returns center point and approximate size of dominant object.
    
    Args:
        image_path: Path to image file
        
    Returns:
        Dict with 'center_x', 'center_y', 'width_ratio', 'height_ratio'
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return {"center_x": 0.5, "center_y": 0.5, "width_ratio": 0.6, "height_ratio": 0.6}
        
        h, w = img.shape[:2]
        
        # Convert to grayscale for saliency
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Simple edge detection to find object boundaries
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            # Fallback: assume center region
            return {"center_x": 0.5, "center_y": 0.5, "width_ratio": 0.6, "height_ratio": 0.6}
        
        # Find largest contour (likely main product)
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w_cont, h_cont = cv2.boundingRect(largest_contour)
        
        # Normalize to 0-1 range
        center_x = (x + w_cont / 2) / w
        center_y = (y + h_cont / 2) / h
        width_ratio = w_cont / w
        height_ratio = h_cont / h
        
        # Clamp values
        center_x = max(0.2, min(0.8, center_x))
        center_y = max(0.2, min(0.8, center_y))
        width_ratio = max(0.3, min(0.8, width_ratio))
        height_ratio = max(0.3, min(0.8, height_ratio))
        
        return {
            "center_x": center_x,
            "center_y": center_y,
            "width_ratio": width_ratio,
            "height_ratio": height_ratio
        }
    except Exception as e:
        logger.warning(f"Failed to detect product region: {e}, using defaults")
        return {"center_x": 0.5, "center_y": 0.5, "width_ratio": 0.6, "height_ratio": 0.6}


def detect_focus_y_from_edges(image_path: str) -> Optional[float]:
    """
    Lightweight focus detection using vertical edge-density scan.
    Returns normalized focus_y in [0, 1], or None on failure.
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return None

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(gray, 50, 150)
        weights = edges.astype(np.float32)

        total = float(weights.sum())
        if total < 1e-6:
            return None

        h = weights.shape[0]
        ys = np.linspace(0, 1, h, endpoint=False)
        wy = (weights.sum(axis=1) * ys).sum()

        focus_y = float(wy / total)
        if not (0.0 <= focus_y <= 1.0):
            return None
        return focus_y
    except Exception:
        return None


def compute_category_bias_y(
    category: Optional[str],
    model_type: Optional[str],
    model_character: Optional[str]
) -> float:
    """
    Soft category bias for focus_y in [0, 1]. Defaults to center (0.5).
    """
    combined = f"{category or ''} {model_type or ''} {model_character or ''}".strip().lower()
    if not combined:
        return 0.5

    if "shoe" in combined or "sepatu" in combined or "sandal" in combined or "footwear" in combined:
        return 0.65
    if "bag" in combined or "tas" in combined:
        return 0.58
    if "beauty" in combined or "skincare" in combined or "cosmetic" in combined:
        return 0.45
    if "hijab" in combined:
        return 0.45
    if "accessor" in combined or "small" in combined:
        return 0.52
    if "apparel" in combined or "model" in combined or "fashion" in combined:
        return 0.5
    return 0.5


def detect_focal_point(image_path: str, category: Optional[str] = None) -> Optional[Dict[str, float]]:
    """
    Lightweight focal-point detection using edge density (no ML).
    Returns normalized focus_x/focus_y in [0, 1], or None on failure.
    Category is a soft bias for focus_y only.
    """
    try:
        img = cv2.imread(image_path)
        if img is None:
            return None

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Laplacian(gray, cv2.CV_32F, ksize=3)
        weights = np.abs(edges)

        total = float(weights.sum())
        if total < 1e-6:
            return None

        h, w = weights.shape
        xs = np.linspace(0, 1, w, endpoint=False)
        ys = np.linspace(0, 1, h, endpoint=False)
        wx = (weights.sum(axis=0) * xs).sum()
        wy = (weights.sum(axis=1) * ys).sum()

        focus_x = float(wx / total)
        focus_y = float(wy / total)

        # Soft category bias (focus_y only)
        if category:
            c = category.strip().lower()
            bias_map = {
                "sepatu": 0.08,
                "shoes": 0.08,
                "sandal": 0.08,
                "footwear": 0.08,
                "tas": 0.03,
                "bag": 0.03,
                "beauty": -0.05,
                "skincare": -0.05,
                "hijab": -0.04,
                "fashion": 0.0
            }
            for key, bias in bias_map.items():
                if key in c:
                    focus_y += bias
                    break

        focus_x = max(0.1, min(0.9, focus_x))
        focus_y = max(0.1, min(0.9, focus_y))

        return {"focus_x": focus_x, "focus_y": focus_y}
    except Exception:
        return None


def get_motion_variations(
    category: str,
    has_face: bool = False,
    model_character: Optional[str] = None,
    product_region: Optional[Dict[str, float]] = None
) -> List[Dict]:
    """
    Generate 3 motion variations based on category, face presence, and model character.
    
    Args:
        category: Product category (Fashion, Beauty, etc.)
        has_face: Whether image contains human face
        model_character: Character type if has_face (female, male, child, etc.)
        product_region: Detected product region info (for non-face images)
        
    Returns:
        List of 3 motion configurations
    """
    if has_face:
        return get_human_motion_variations(category, model_character)
    else:
        return get_product_motion_variations(category, product_region)


def get_human_motion_variations(category: str, model_character: Optional[str] = None) -> List[Dict]:
    """
    Generate 3 motion variations for human models with face protection.
    Motion is subtle and face-safe.
    """
    # Base motion configs (all face-safe)
    base_configs = [
        {
            "name": "Confident Intro",
            "motion_type": "slow_push",
            "zoom_start": 1.0,
            "zoom_end": 1.04,
            "zoom_speed": 0.0008,
            "pan_x": 0.0,
            "pan_y": 0.0,
            "pan_speed": 0.0,
            "rotate": 0.0,
            "description": "Slow camera push with vertical background parallax"
        },
        {
            "name": "Style Flow",
            "motion_type": "micro_pan",
            "zoom_start": 1.0,
            "zoom_end": 1.03,
            "zoom_speed": 0.0006,
            "pan_x": 0.02,  # Small diagonal pan
            "pan_y": -0.01,
            "pan_speed": 0.0004,
            "rotate": 0.0,
            "description": "Micro fabric warp with small diagonal camera pan"
        },
        {
            "name": "Detail & Value",
            "motion_type": "detail_zoom",
            "zoom_start": 1.0,
            "zoom_end": 1.05,
            "zoom_speed": 0.001,
            "pan_x": 0.0,
            "pan_y": 0.0,
            "pan_speed": 0.0,
            "rotate": 0.0,
            "description": "Zoom into fabric/outfit detail with light sweep"
        }
    ]
    
    # Adjust based on model character
    if model_character == "female":
        # More elegant, slower motion
        for config in base_configs:
            config["zoom_speed"] *= 0.9
            config["pan_speed"] *= 0.8
    elif model_character == "male":
        # Slightly more dynamic
        for config in base_configs:
            config["zoom_speed"] *= 1.1
    elif model_character in ["child", "anak laki-laki", "anak perempuan"]:
        # Playful, but still safe
        for config in base_configs:
            config["zoom_end"] = min(1.03, config["zoom_end"])
            config["zoom_speed"] *= 0.8
    
    # Adjust based on category
    if category == "Beauty":
        # More focus on face area (but still protected)
        base_configs[0]["zoom_end"] = 1.03
        base_configs[2]["zoom_end"] = 1.04
    elif category == "Fashion":
        # Show more of outfit
        base_configs[1]["pan_x"] = 0.03
        base_configs[2]["zoom_end"] = 1.06
    
    logger.info(f"get_human_motion_variations: category='{category}', returning {len(base_configs)} configs")
    if len(base_configs) != 3:
        logger.warning(f"⚠️ get_human_motion_variations returned {len(base_configs)} configs, expected 3!")
    return base_configs


def get_product_motion_variations(
    category: str,
    product_region: Optional[Dict[str, float]] = None
) -> List[Dict]:
    """
    Generate 3 motion variations for product images (no face).
    Motion focuses on product region.
    """
    if product_region is None:
        product_region = {"center_x": 0.5, "center_y": 0.5, "width_ratio": 0.6, "height_ratio": 0.6}
    
    center_x = product_region["center_x"]
    center_y = product_region["center_y"]
    
    # Calculate pan offsets to focus on product
    pan_offset_x = (center_x - 0.5) * 0.1  # Max 10% pan
    pan_offset_y = (center_y - 0.5) * 0.1
    
    # STABLE MOTION CONFIGS (NO JITTER, LINEAR ZOOM ONLY)
    # CRITICAL: All configs use linear zoom formula z='1+speed*on'
    # - NO conditional logic (no if, no max with conditions)
    # - NO zoom up then down
    # - Linear zoom only for stability
    #
    # Formula: zoom_end determines speed
    # For 5s @ 60fps = 300 frames:
    # - zoom_end 1.18 → speed = 0.18/300 = 0.0006 per frame
    # - zoom_end 1.21 → speed = 0.21/300 = 0.0007 per frame
    
    total_frames = 300  # 5 seconds @ 60fps
    
    # Base configs per category (STABLE LINEAR ZOOM ONLY - EXACT FORMAT)
    # CRITICAL: All configs use linear zoom z='1+speed*on' (NO conditional)
    # 3 Variasi sesuai spesifikasi:
    # 1. Elegant Zoom: z='1+0.0008*on' → zoom_end = 1 + 0.0008*300 = 1.24
    # 2. Luxury Zoom: z='1+0.0007*on' → zoom_end = 1 + 0.0007*300 = 1.21
    # 3. Subtle Zoom: z='1+0.0006*on' → zoom_end = 1 + 0.0006*300 = 1.18
    category_configs = {
        "Fashion": [
            {
                "name": "Elegant Zoom",
                "motion_type": "center_zoom",
                "zoom_start": 1.0,
                "zoom_end": 1.24,  # z='1+0.0008*on' → 1 + 0.0008*300 = 1.24
                "zoom_speed": 0.0008,  # Per frame speed @ 60fps
                "pan_x": 0.0,  # NO PAN for stability
                "pan_y": 0.0,
                "pan_speed": 0.0,
                "rotate": 0.0,
                "description": "Smooth elegant zoom (z='1+0.0008*on', stable)"
            },
            {
                "name": "Luxury Zoom",
                "motion_type": "slow_zoom",
                "zoom_start": 1.0,
                "zoom_end": 1.21,  # z='1+0.0007*on' → 1 + 0.0007*300 = 1.21
                "zoom_speed": 0.0007,  # Per frame speed @ 60fps
                "pan_x": 0.0,  # NO PAN for stability
                "pan_y": 0.0,
                "pan_speed": 0.0,
                "rotate": 0.0,
                "description": "Luxury zoom (z='1+0.0007*on', stable)"
            },
            {
                "name": "Subtle Zoom",
                "motion_type": "slow_zoom",
                "zoom_start": 1.0,
                "zoom_end": 1.18,  # z='1+0.0006*on'
                "zoom_speed": 0.0006,
                "pan_x": 0.0,
                "pan_y": 0.0,
                "pan_speed": 0.0,
                "rotate": 0.0,
                "description": "Subtle zoom (z='1+0.0006*on', stable)"
            }
        ],
        "Beauty": [
            {
                "name": "Elegant Zoom",
                "motion_type": "center_zoom",
                "zoom_start": 1.0,
                "zoom_end": 1.24,  # z='1+0.0008*on'
                "zoom_speed": 0.0008,
                "pan_x": 0.0,
                "pan_y": 0.0,
                "pan_speed": 0.0,
                "rotate": 0.0,
                "description": "Smooth elegant zoom (z='1+0.0008*on', stable)"
            },
            {
                "name": "Luxury Zoom",
                "motion_type": "slow_zoom",
                "zoom_start": 1.0,
                "zoom_end": 1.21,  # z='1+0.0007*on'
                "zoom_speed": 0.0007,
                "pan_x": 0.0,
                "pan_y": 0.0,
                "pan_speed": 0.0,
                "rotate": 0.0,
                "description": "Luxury zoom (z='1+0.0007*on', stable)"
            },
            {
                "name": "Subtle Zoom",
                "motion_type": "slow_zoom",
                "zoom_start": 1.0,
                "zoom_end": 1.18,  # z='1+0.0006*on'
                "zoom_speed": 0.0006,
                "pan_x": 0.0,
                "pan_y": 0.0,
                "pan_speed": 0.0,
                "rotate": 0.0,
                "description": "Subtle zoom (z='1+0.0006*on', stable)"
            }
        ],
        "Tas": [
            {
                "name": "Elegant Zoom",
                "motion_type": "center_zoom",
                "zoom_start": 1.0,
                "zoom_end": 1.24,  # z='1+0.0008*on'
                "zoom_speed": 0.0008,
                "pan_x": 0.0,
                "pan_y": 0.0,
                "pan_speed": 0.0,
                "rotate": 0.0,
                "description": "Smooth elegant zoom (z='1+0.0008*on', stable)"
            },
            {
                "name": "Luxury Zoom",
                "motion_type": "slow_zoom",
                "zoom_start": 1.0,
                "zoom_end": 1.21,  # z='1+0.0007*on'
                "zoom_speed": 0.0007,
                "pan_x": 0.0,
                "pan_y": 0.0,
                "pan_speed": 0.0,
                "rotate": 0.0,
                "description": "Luxury zoom (z='1+0.0007*on', stable)"
            },
            {
                "name": "Subtle Zoom",
                "motion_type": "slow_zoom",
                "zoom_start": 1.0,
                "zoom_end": 1.18,  # z='1+0.0006*on'
                "zoom_speed": 0.0006,
                "pan_x": 0.0,
                "pan_y": 0.0,
                "pan_speed": 0.0,
                "rotate": 0.0,
                "description": "Subtle zoom (z='1+0.0006*on', stable)"
            }
        ],
        "Sandal/Sepatu": [
            {
                "name": "Elegant Zoom",
                "motion_type": "center_zoom",
                "zoom_start": 1.0,
                "zoom_end": 1.105,  # z='1+0.00035*on'
                "zoom_speed": 0.00035,
                "pan_x": 0.0,
                "pan_y": 0.0,
                "pan_speed": 0.0,
                "rotate": 0.0,
                "description": "Smooth elegant zoom (z='1+0.00035*on', stable)"
            },
            {
                "name": "Luxury Zoom",
                "motion_type": "slow_zoom",
                "zoom_start": 1.0,
                "zoom_end": 1.075,  # z='1+0.00025*on'
                "zoom_speed": 0.00025,
                "pan_x": 0.0,
                "pan_y": 0.0,
                "pan_speed": 0.0,
                "rotate": 0.0,
                "description": "Slight zoom luxury (z='1+0.00025*on', minimal)"
            },
            {
                "name": "Smooth Pan",
                "motion_type": "smooth_pan",
                "zoom_start": 1.0,
                "zoom_end": 1.0,  # NO ZOOM, z=1
                "zoom_speed": 0.0,
                "pan_x": 0.02,  # Pan halus: x='40*sin(on/60)'
                "pan_y": 0.0,
                "pan_speed": 0.0,
                "rotate": 0.0,
                "description": "Pan halus (z=1, x='40*sin(on/60)', no zoom)"
            }
        ]
    }

    # Variation 2 rotation disabled to keep camera motion purely linear
    
    # Default to Fashion if category not found
    configs = category_configs.get(category, category_configs["Fashion"])
    logger.info(f"get_product_motion_variations: category='{category}', returning {len(configs)} configs")
    if len(configs) != 3:
        logger.warning(f"⚠️ get_product_motion_variations returned {len(configs)} configs, expected 3!")
    return configs
