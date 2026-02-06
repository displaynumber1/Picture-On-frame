"""
Strict Image Preprocessing Pipeline for fal / Flux
Processes all user-uploaded images before sending to fal
"""
import logging
from typing import Tuple, Optional, Dict, Any
from io import BytesIO
from PIL import Image

logger = logging.getLogger(__name__)

# Supported image formats
SUPPORTED_FORMATS = {'JPEG', 'JPG', 'PNG', 'WEBP', 'HEIC'}
MIN_DIMENSION = 256  # Minimum width or height in pixels
MAX_LONGEST_SIDE = 1024  # Maximum longest side after normalization

# Target resolutions for final resize (all < 1.0 MP)
TARGET_RESOLUTIONS = {
    "1:1": (768, 768),      # 0.59 MP
    "3:4": (768, 1024),     # 0.79 MP
    "4:3": (1024, 768),    # 0.79 MP
    "9:16": (720, 1280),   # 0.92 MP
    "16:9": (1280, 720),   # 0.92 MP
}

# Safety margins for center crop (percentage of image dimension)
SAFETY_MARGINS = {
    "face_dominant": 0.175,  # 15-20% average
    "half_body": 0.125,      # 10-15% average
    "full_body": 0.075,      # 5-10% average
}


def validate_image_input(image_bytes: bytes, filename: Optional[str] = None) -> Tuple[Image.Image, str]:
    """
    STEP 1: INPUT VALIDATION
    - Accept only image files (jpg, png, webp, heic)
    - Reject images with width or height < 256 px
    
    Args:
        image_bytes: Raw image bytes
        filename: Optional filename for format detection
    
    Returns:
        Tuple of (PIL Image, format string)
    
    Raises:
        ValueError: If image is invalid or too small
    """
    try:
        img = Image.open(BytesIO(image_bytes))
        
        # Check format
        img_format = img.format.upper() if img.format else None
        if img_format not in SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported image format: {img_format}. "
                f"Supported formats: {', '.join(SUPPORTED_FORMATS)}"
            )
        
        # Check minimum dimensions
        width, height = img.size
        if width < MIN_DIMENSION or height < MIN_DIMENSION:
            raise ValueError(
                f"Image too small: {width}x{height}px. "
                f"Minimum dimension: {MIN_DIMENSION}px"
            )
        
        logger.info(f"✅ Input validation passed: {width}x{height}px, format: {img_format}")
        return img, img_format
        
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Invalid image file: {str(e)}")


def normalize_resolution(img: Image.Image) -> Image.Image:
    """
    STEP 2: NORMALIZE RESOLUTION (FIRST RESIZE)
    - Resize proportionally so the longest side = MAX 1024 px
    - NEVER upscale images
    - Preserve aspect ratio
    
    Args:
        img: PIL Image
    
    Returns:
        Resized PIL Image
    """
    width, height = img.size
    longest_side = max(width, height)
    
    # If already within limit, return as-is
    if longest_side <= MAX_LONGEST_SIDE:
        logger.info(f"✅ Image already normalized: {width}x{height}px (longest side: {longest_side}px)")
        return img
    
    # Calculate new dimensions (proportional resize)
    if width > height:
        new_width = MAX_LONGEST_SIDE
        new_height = int(height * (MAX_LONGEST_SIDE / width))
    else:
        new_height = MAX_LONGEST_SIDE
        new_width = int(width * (MAX_LONGEST_SIDE / height))
    
    # Resize using high-quality resampling
    resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    logger.info(f"✅ Normalized resolution: {width}x{height}px → {new_width}x{new_height}px")
    
    return resized


def parse_aspect_ratio(aspect_ratio_str: str) -> Tuple[int, int]:
    """
    Parse aspect ratio string to (width, height) tuple
    
    Args:
        aspect_ratio_str: Aspect ratio string (e.g., "9:16", "1:1")
    
    Returns:
        Tuple of (width_ratio, height_ratio)
    
    Raises:
        ValueError: If aspect ratio format is invalid
    """
    try:
        parts = aspect_ratio_str.split(':')
        if len(parts) != 2:
            raise ValueError(f"Invalid aspect ratio format: {aspect_ratio_str}")
        
        width_ratio = int(parts[0])
        height_ratio = int(parts[1])
        
        if width_ratio <= 0 or height_ratio <= 0:
            raise ValueError(f"Invalid aspect ratio values: {aspect_ratio_str}")
        
        return width_ratio, height_ratio
        
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid aspect ratio format: {aspect_ratio_str}. Error: {str(e)}")


def safe_center_crop(img: Image.Image, target_aspect_ratio: str, image_type: str = "full_body") -> Image.Image:
    """
    STEP 4: SAFE CENTER CROP (NO FACE DETECTION)
    - Crop to target aspect ratio using center-based crop
    - NEVER tightly crop to the face
    - Apply safety margin based on image type
    - Preserve head-to-body proportion
    
    Args:
        img: PIL Image (already normalized)
        target_aspect_ratio: Target aspect ratio string (e.g., "9:16", "1:1")
        image_type: Type of image ("face_dominant", "half_body", "full_body")
    
    Returns:
        Cropped PIL Image
    """
    width, height = img.size
    current_aspect = width / height
    
    # Parse target aspect ratio
    target_width_ratio, target_height_ratio = parse_aspect_ratio(target_aspect_ratio)
    target_aspect = target_width_ratio / target_height_ratio
    
    # If aspect ratios match (within 1% tolerance), no crop needed
    if abs(current_aspect - target_aspect) < 0.01:
        logger.info(f"✅ Aspect ratio already matches: {current_aspect:.3f} ≈ {target_aspect:.3f}")
        return img
    
    # Get safety margin based on image type
    safety_margin = SAFETY_MARGINS.get(image_type, SAFETY_MARGINS["full_body"])
    
    # Calculate crop dimensions
    if current_aspect > target_aspect:
        # Image is wider than target → crop width
        new_width = int(height * target_aspect)
        # Apply safety margin (reduce crop width)
        crop_width = int(new_width * (1 - safety_margin))
        left = (width - crop_width) // 2
        right = left + crop_width
        top = 0
        bottom = height
    else:
        # Image is taller than target → crop height
        new_height = int(width / target_aspect)
        # Apply safety margin (reduce crop height)
        crop_height = int(new_height * (1 - safety_margin))
        top = (height - crop_height) // 2
        bottom = top + crop_height
        left = 0
        right = width
    
    # Perform center crop
    cropped = img.crop((left, top, right, bottom))
    logger.info(
        f"✅ Safe center crop: {width}x{height}px → {cropped.width}x{cropped.height}px "
        f"(margin: {safety_margin*100:.1f}%, type: {image_type})"
    )
    
    return cropped


def final_resize(img: Image.Image, target_aspect_ratio: str) -> Image.Image:
    """
    STEP 5: FINAL RESIZE (AI INPUT SIZE)
    - Resize cropped image to target resolution
    - Ensure total megapixels < 1.0 MP
    
    Args:
        img: PIL Image (already cropped)
        target_aspect_ratio: Target aspect ratio string
    
    Returns:
        Resized PIL Image
    
    Raises:
        ValueError: If target resolution exceeds 1.0 MP
    """
    if target_aspect_ratio not in TARGET_RESOLUTIONS:
        raise ValueError(
            f"Unsupported aspect ratio: {target_aspect_ratio}. "
            f"Supported: {', '.join(TARGET_RESOLUTIONS.keys())}"
        )
    
    target_width, target_height = TARGET_RESOLUTIONS[target_aspect_ratio]
    megapixels = (target_width * target_height) / 1_000_000
    
    # Safety check: ensure < 1.0 MP
    if megapixels >= 1.0:
        raise ValueError(
            f"Target resolution {target_width}x{target_height} = {megapixels:.3f} MP "
            f"exceeds 1.0 MP limit!"
        )
    
    # Resize to target resolution
    resized = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
    
    logger.info(
        f"✅ Final resize: {img.width}x{img.height}px → {target_width}x{target_height}px "
        f"({megapixels:.3f} MP)"
    )
    
    return resized


def cleanup_and_compress(img: Image.Image, target_size_mb: float = 1.0) -> Tuple[bytes, str]:
    """
    STEP 6: IMAGE CLEANUP & COMPRESSION
    - Convert image to JPEG or WebP
    - JPEG quality: 80-85
    - WebP quality: 75-80
    - Strip all EXIF / metadata
    - Target file size < 1MB
    
    Args:
        img: PIL Image
        target_size_mb: Target file size in MB (default: 1.0)
    
    Returns:
        Tuple of (compressed_bytes, file_extension)
    """
    # Convert to RGB if needed (for JPEG)
    if img.mode in ('RGBA', 'LA', 'P'):
        # Create white background
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Strip metadata by creating new image
    img_clean = Image.new('RGB', img.size)
    img_clean.paste(img)
    
    target_size_bytes = int(target_size_mb * 1024 * 1024)
    
    # Try JPEG first (quality 80-85)
    output = BytesIO()
    quality = 85
    
    for attempt in range(5):
        output.seek(0)
        output.truncate(0)
        img_clean.save(output, format='JPEG', quality=quality, optimize=True)
        size = len(output.getvalue())
        
        if size <= target_size_bytes:
            logger.info(f"✅ Compressed to {size:,} bytes ({size/(1024*1024):.2f} MB) with JPEG quality {quality}")
            return output.getvalue(), '.jpg'
        
        # Reduce quality
        quality = max(80, quality - 2)
    
    # If JPEG still too large, try WebP (better compression)
    logger.info(f"⚠️ JPEG still too large, trying WebP...")
    webp_quality = 80
    
    for attempt in range(3):
        output.seek(0)
        output.truncate(0)
        img_clean.save(output, format='WEBP', quality=webp_quality, method=6)
        size = len(output.getvalue())
        
        if size <= target_size_bytes:
            logger.info(f"✅ Compressed to {size:,} bytes ({size/(1024*1024):.2f} MB) with WebP quality {webp_quality}")
            return output.getvalue(), '.webp'
        
        webp_quality = max(75, webp_quality - 2)
    
    # If still too large, return JPEG anyway (but log warning)
    logger.warning(f"⚠️ Final size {size:,} bytes ({size/(1024*1024):.2f} MB) exceeds target {target_size_mb}MB")
    return output.getvalue(), '.jpg'


def preprocess_image(
    image_bytes: bytes,
    target_aspect_ratio: str,
    image_type: str = "full_body",
    filename: Optional[str] = None
) -> Tuple[bytes, str, Dict[str, Any]]:
    """
    Complete image preprocessing pipeline
    
    Pipeline steps:
    1. Input validation
    2. Normalize resolution (max 1024px longest side)
    3. Determine target aspect ratio
    4. Safe center crop
    5. Final resize to target resolution
    6. Cleanup & compression
    
    Args:
        image_bytes: Raw image bytes
        target_aspect_ratio: Target aspect ratio (e.g., "9:16", "1:1")
        image_type: Type of image ("face_dominant", "half_body", "full_body")
        filename: Optional filename for format detection
    
    Returns:
        Tuple of (processed_bytes, file_extension, metadata_dict)
    
    Raises:
        ValueError: If preprocessing fails at any step
    """
    metadata = {
        "original_size_bytes": len(image_bytes),
        "original_size_mb": round(len(image_bytes) / (1024 * 1024), 2),
    }
    
    try:
        # STEP 1: Input validation
        img, img_format = validate_image_input(image_bytes, filename)
        original_width, original_height = img.size
        metadata["original_resolution"] = f"{original_width}x{original_height}"
        metadata["original_format"] = img_format
        
        # STEP 2: Normalize resolution
        img = normalize_resolution(img)
        normalized_width, normalized_height = img.size
        metadata["normalized_resolution"] = f"{normalized_width}x{normalized_height}"
        
        # STEP 3: Target aspect ratio is provided as parameter
        if target_aspect_ratio not in TARGET_RESOLUTIONS:
            raise ValueError(
                f"Unsupported target aspect ratio: {target_aspect_ratio}. "
                f"Supported: {', '.join(TARGET_RESOLUTIONS.keys())}"
            )
        
        # STEP 4: Safe center crop
        img = safe_center_crop(img, target_aspect_ratio, image_type)
        cropped_width, cropped_height = img.size
        metadata["cropped_resolution"] = f"{cropped_width}x{cropped_height}"
        
        # STEP 5: Final resize
        img = final_resize(img, target_aspect_ratio)
        final_width, final_height = img.size
        megapixels = (final_width * final_height) / 1_000_000
        metadata["final_resolution"] = f"{final_width}x{final_height}"
        metadata["final_megapixels"] = round(megapixels, 3)
        metadata["below_1mp"] = megapixels < 1.0
        
        # Safety check: block if > 1.0 MP
        if megapixels >= 1.0:
            raise ValueError(
                f"Final resolution {final_width}x{final_height} = {megapixels:.3f} MP "
                f"exceeds 1.0 MP limit! Request blocked."
            )
        
        # STEP 6: Cleanup & compression
        processed_bytes, ext = cleanup_and_compress(img, target_size_mb=1.0)
        final_size_bytes = len(processed_bytes)
        final_size_mb = final_size_bytes / (1024 * 1024)
        metadata["final_size_bytes"] = final_size_bytes
        metadata["final_size_mb"] = round(final_size_mb, 2)
        metadata["below_1mb"] = final_size_mb < 1.0
        metadata["file_extension"] = ext
        
        # Log summary
        logger.info(f"📊 Image preprocessing complete:")
        logger.info(f"   Original: {original_width}x{original_height}px, {metadata['original_size_mb']} MB")
        logger.info(f"   Final: {final_width}x{final_height}px ({megapixels:.3f} MP), {final_size_mb:.2f} MB")
        logger.info(f"   ✅ Below 1.0 MP: {megapixels < 1.0}, Below 1MB: {final_size_mb < 1.0}")
        
        return processed_bytes, ext, metadata
        
    except Exception as e:
        logger.error(f"❌ Image preprocessing failed: {str(e)}", exc_info=True)
        raise ValueError(f"Image preprocessing failed: {str(e)}")
