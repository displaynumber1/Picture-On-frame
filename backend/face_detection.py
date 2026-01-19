"""
Face Detection and Face Lock System for Video Generation
Uses MediaPipe for face detection and creates face mask for protection
"""

import cv2
import numpy as np
import logging
from typing import Tuple, Optional, List
import mediapipe as mp

logger = logging.getLogger(__name__)

# Initialize MediaPipe Face Detection
mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils


def detect_face(image_path: str) -> Optional[Tuple[int, int, int, int]]:
    """
    Detect human face in image using MediaPipe.
    
    IMPORTANT: Face detection runs on ORIGINAL image BEFORE any resize/crop.
    This ensures maximum detection accuracy.
    
    Args:
        image_path: Path to input image file
    
    Returns:
        Tuple of (x, y, width, height) bounding box, or None if no face detected
        Bounding box is expanded by 15-20% for safety margin
    """
    try:
        # Load image with IMREAD_UNCHANGED to preserve all channels (including alpha)
        image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if image is None:
            logger.error(f"Failed to read image: {image_path}")
            return None
        
        # Debug: Log image shape and channels
        height, width = image.shape[:2]
        channels = image.shape[2] if len(image.shape) == 3 else 1
        logger.debug(f"Image loaded: shape=({height}, {width}), channels={channels}, dtype={image.dtype}")
        
        # Handle different image formats
        if channels == 4:
            # RGBA image: Convert to RGB explicitly
            logger.debug("RGBA image detected, converting to RGB")
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
        elif channels == 3:
            # BGR image: Convert to RGB (MediaPipe requires RGB)
            logger.debug("BGR image detected, converting to RGB")
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        elif channels == 1:
            # Grayscale: Convert to RGB
            logger.debug("Grayscale image detected, converting to RGB")
            image_rgb = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        else:
            logger.warning(f"Unexpected image format: {channels} channels, defaulting to BGR2RGB")
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Verify RGB conversion
        height, width = image_rgb.shape[:2]
        logger.debug(f"RGB image ready: shape=({height}, {width}), channels={image_rgb.shape[2]}")
        
        # CRITICAL: Run face detection on ORIGINAL image size (no resize before detection)
        # MediaPipe works best on original resolution
        
        # Initialize MediaPipe Face Detection with LOWER confidence threshold
        # Lower threshold (0.3) catches more faces, especially in AI-generated images
        with mp_face_detection.FaceDetection(
            model_selection=1,  # 0 for short-range, 1 for full-range (better for full body)
            min_detection_confidence=0.3  # Lowered from 0.5 to 0.3 for better detection
        ) as face_detection:
            # Process image (on original size, no resize)
            results = face_detection.process(image_rgb)
            
            if results.detections:
                # Get first face detection (assuming single face)
                detection = results.detections[0]
                confidence = detection.score[0]
                logger.info(f"Face detected with confidence: {confidence:.3f}")
                
                # Get bounding box
                bbox = detection.location_data.relative_bounding_box
                
                # Convert relative coordinates to absolute
                x = int(bbox.xmin * width)
                y = int(bbox.ymin * height)
                w = int(bbox.width * width)
                h = int(bbox.height * height)
                
                # Expand bounding box by 15-20% for safety margin (include hairline)
                expand_factor = 0.18  # 18% expansion
                x_expand = int(w * expand_factor)
                y_expand = int(h * expand_factor)
                
                x = max(0, x - x_expand)
                y = max(0, y - y_expand)
                w = min(width - x, w + 2 * x_expand)
                h = min(height - y, h + 2 * y_expand)
                
                logger.info(f"Face detected: x={x}, y={y}, w={w}, h={h} (expanded by {expand_factor*100}%)")
                logger.info(f"Face region: {w}x{h} pixels in {width}x{height} image")
                return (x, y, w, h)
            else:
                logger.info("No face detected in image (MediaPipe returned no detections)")
                return None
                
    except Exception as e:
        logger.error(f"Error detecting face: {str(e)}", exc_info=True)
        return None


def create_face_mask(
    image_shape: Tuple[int, int],
    face_bbox: Tuple[int, int, int, int],
    feather_size: int = 30
) -> np.ndarray:
    """
    Create soft-edge face mask with feathering.
    
    Args:
        image_shape: (height, width) of image
        face_bbox: (x, y, width, height) bounding box of face
        feather_size: Size of feathering edge in pixels
    
    Returns:
        Binary mask (0 = face region, 255 = non-face region) with soft edges
    """
    height, width = image_shape[:2]
    x, y, w, h = face_bbox
    
    # Create binary mask
    # Format: 255 = face region (PROTECTED, use original), 0 = non-face (can be transformed)
    mask = np.zeros((height, width), dtype=np.uint8)
    
    # Create face region (255 = protected area)
    mask[y:y+h, x:x+w] = 255
    
    # Apply Gaussian blur for soft edges (feathering)
    # This creates smooth transition between protected and transformable regions
    mask = cv2.GaussianBlur(mask, (feather_size * 2 + 1, feather_size * 2 + 1), feather_size / 3)
    
    # Mask format: 255 = face (protected), 0-254 = transition zone, 0 = non-face (transformable)
    # Higher values = more protection, lower values = more transformation allowed
    
    return mask


def has_human_face(image_path: str) -> bool:
    """
    Check if image contains a human face.
    
    Args:
        image_path: Path to input image file
    
    Returns:
        True if face detected, False otherwise
    """
    face_bbox = detect_face(image_path)
    return face_bbox is not None


def get_face_region_info(image_path: str) -> Optional[dict]:
    """
    Get detailed face region information.
    
    Args:
        image_path: Path to input image file
    
    Returns:
        Dictionary with face bounding box and mask info, or None if no face
    """
    face_bbox = detect_face(image_path)
    if face_bbox is None:
        return None
    
    # Read image to get dimensions (use same method as detect_face)
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if image is None:
        return None
    
    # Handle different channel formats
    if len(image.shape) == 3:
        height, width = image.shape[:2]
    else:
        height, width = image.shape[:2]
    
    # Create face mask
    face_mask = create_face_mask((height, width), face_bbox)
    
    return {
        "bbox": face_bbox,  # (x, y, w, h)
        "mask": face_mask,
        "image_shape": (height, width),
        "center": (face_bbox[0] + face_bbox[2] // 2, face_bbox[1] + face_bbox[3] // 2)
    }
