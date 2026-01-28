"""
Fal.ai service for image and video generation
"""
import os
import httpx
import logging
import asyncio
import json
from typing import List, Dict, Any, Optional, Tuple
from io import BytesIO

logger = logging.getLogger(__name__)

FAL_KEY = os.getenv('FAL_KEY')
FAL_API_BASE = "https://fal.run"

# LOCKED CONFIGURATION: Model dan parameter untuk image-to-image generation
# Model: fal-ai/flux-2/lora/edit - Image editing (FLUX.2 [dev] from Black Forest Labs)
# Untuk text-to-image: fal-ai/flux/schnell (fallback jika tidak ada image)
# Parameter DEFAULT untuk gambar pertama:
# - image_strength: 0.67 (FIXED - untuk balanced reference adherence)
# - num_inference_steps: 24 (FIXED - ini adalah INFERENCE, BUKAN training)
# - guidance_scale: 4.5 (FIXED - natural and realistic, prevents mannequin-like results)
# Parameter ENHANCED untuk gambar kedua (dinamis untuk hasil lebih realistis):
# - image_strength: 0.69 (+0.02 dari default, max 0.75)
# - num_inference_steps: 26 (+2 dari default, max 30)
# - guidance_scale: 4.95 (+10% dari default, max 6.0)
# ❗ Jangan gunakan nilai default dari fal.ai
# ❗ Fokus hanya pada image editing + prompt adherence
FAL_MODEL_ENDPOINT_TEXT_TO_IMAGE = "fal-ai/flux/schnell"  # Untuk text-to-image (tanpa init image)
FAL_MODEL_ENDPOINT_IMAGE_TO_IMAGE = "fal-ai/flux-2/lora/edit"  # Untuk image-to-image editing (FLUX.2 [dev])
FAL_NUM_INFERENCE_STEPS = 24  # Default: 24 inference steps (increased to prevent blank images)
FAL_GUIDANCE_SCALE = 4.5  # Default: 4.5 (natural and realistic, prevents mannequin-like results)
FAL_IMAGE_STRENGTH = 0.67  # Default: 0.67 (balanced for reference adherence)
# NOTE: Do NOT use fal.ai size presets. Always use explicit width/height for cost control.

def get_resolution_from_aspect_ratio(aspect_ratio: str) -> tuple[Optional[int], Optional[int]]:
    """
    Convert aspect ratio string to width and height resolution.
    COST-OPTIMIZED: All resolutions are below 1.0 MP to control generation costs.
    
    Resolution mapping (all below 1.0 MP):
    - 1:1   → 768 x 768   (0.59 MP)
    - 3:4   → 768 x 1024  (0.79 MP)
    - 4:3   → 1024 x 768  (0.79 MP)
    - 9:16  → 720 x 1280  (0.92 MP)
    - 16:9  → 1280 x 720  (0.92 MP)
    
    Args:
        aspect_ratio: Aspect ratio string (e.g., "9:16", "16:9", "1:1", "3:4", "4:3")
    
    Returns:
        Tuple of (width, height) or (None, None) if aspect ratio not recognized
    """
    aspect_ratio_map = {
        "1:1": (768, 768),      # 0.59 MP - Square format
        "3:4": (768, 1024),     # 0.79 MP - Vertical portrait
        "4:3": (1024, 768),    # 0.79 MP - Horizontal landscape
        "9:16": (720, 1280),   # 0.92 MP - Vertical/Story format
        "16:9": (1280, 720),   # 0.92 MP - Horizontal/Widescreen format
    }
    
    resolution = aspect_ratio_map.get(aspect_ratio, (None, None))
    
    # Verify megapixel count is below 1.0 MP
    if resolution[0] and resolution[1]:
        megapixels = (resolution[0] * resolution[1]) / 1_000_000
        if megapixels >= 1.0:
            logger.warning(f"⚠️ Resolution {resolution[0]}x{resolution[1]} = {megapixels:.2f} MP exceeds 1.0 MP limit!")
        else:
            logger.debug(f"✅ Resolution {resolution[0]}x{resolution[1]} = {megapixels:.2f} MP (below 1.0 MP limit)")
    
    return resolution


async def compress_and_log_image(image_url: str, width: Optional[int] = None, height: Optional[int] = None) -> Tuple[str, Dict[str, Any]]:
    """
    Download image from URL, compress it, and return compressed image URL.
    Also logs resolution, megapixel count, and file size for cost control.
    
    Args:
        image_url: URL of image from fal.ai
        width: Expected width (for logging)
        height: Expected height (for logging)
    
    Returns:
        Tuple of (compressed_image_url, metadata_dict)
    """
    try:
        from PIL import Image
        
        # Download image
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(image_url)
            response.raise_for_status()
            image_bytes = response.content
        
        # Get image dimensions and size
        img = Image.open(BytesIO(image_bytes))
        actual_width, actual_height = img.size
        megapixels = (actual_width * actual_height) / 1_000_000
        original_size_bytes = len(image_bytes)
        original_size_mb = original_size_bytes / (1024 * 1024)
        
        # Log original image info
        logger.info(f"📊 Original image from fal.ai:")
        logger.info(f"   Resolution: {actual_width}x{actual_height} pixels")
        logger.info(f"   Megapixels: {megapixels:.3f} MP")
        logger.info(f"   File size: {original_size_bytes:,} bytes ({original_size_mb:.2f} MB)")
        if width and height:
            logger.info(f"   Expected: {width}x{height} (actual: {actual_width}x{actual_height})")
        
        # Compress image (target < 1MB)
        compressed_bytes, ext = compress_image_if_needed(image_bytes, max_size_mb=1.0, quality=82)
        compressed_size_bytes = len(compressed_bytes)
        compressed_size_mb = compressed_size_bytes / (1024 * 1024)
        
        # Log compressed image info
        logger.info(f"📦 Compressed image:")
        logger.info(f"   File size: {compressed_size_bytes:,} bytes ({compressed_size_mb:.2f} MB)")
        logger.info(f"   Compression ratio: {(1 - compressed_size_bytes / original_size_bytes) * 100:.1f}% reduction")
        
        # Upload compressed image to Supabase Storage
        # Note: This requires user_id and category, which we don't have here
        # For now, return the original URL and log compression stats
        # TODO: Integrate with Supabase upload if needed
        
        metadata = {
            "original_resolution": f"{actual_width}x{actual_height}",
            "original_megapixels": round(megapixels, 3),
            "original_size_bytes": original_size_bytes,
            "original_size_mb": round(original_size_mb, 2),
            "compressed_size_bytes": compressed_size_bytes,
            "compressed_size_mb": round(compressed_size_mb, 2),
            "compression_ratio": round((1 - compressed_size_bytes / original_size_bytes) * 100, 1),
            "below_1mp": megapixels < 1.0,
            "below_1mb": compressed_size_mb < 1.0
        }
        
        logger.info(f"✅ Image compression complete:")
        logger.info(f"   ✅ Megapixels: {megapixels:.3f} MP {'(below 1.0 MP)' if megapixels < 1.0 else '⚠️ EXCEEDS 1.0 MP!'}")
        logger.info(f"   ✅ Final size: {compressed_size_mb:.2f} MB {'(below 1MB)' if compressed_size_mb < 1.0 else '⚠️ EXCEEDS 1MB!'}")
        
        # For now, return original URL (compression logging is done)
        # In production, you might want to upload compressed version to Supabase
        return image_url, metadata
        
    except ImportError:
        logger.warning("PIL/Pillow not available, skipping compression. Returning original URL.")
        return image_url, {"compression_skipped": True, "reason": "PIL not available"}
    except Exception as e:
        logger.error(f"Error compressing image: {str(e)}", exc_info=True)
        logger.warning("Returning original URL due to compression error.")
        return image_url, {"compression_skipped": True, "reason": str(e)}


def compress_image_if_needed(image_bytes: bytes, max_size_mb: float = 1.0, quality: int = 82) -> Tuple[bytes, str]:
    """
    Compress image if size exceeds max_size_mb (default: 1MB).
    Uses JPEG quality 80-85 or WebP quality 75-80, strips metadata.
    
    Args:
        image_bytes: Original image bytes
        max_size_mb: Maximum file size in MB (default: 1.0)
        quality: JPEG quality (1-100, default: 82)
    
    Returns:
        Tuple of (compressed_image_bytes, file_extension)
    """
    try:
        from PIL import Image
        
        max_size_bytes = max_size_mb * 1024 * 1024
        original_size = len(image_bytes)
        
        # If image is already under limit, return as-is (but still strip metadata)
        if original_size <= max_size_bytes:
            logger.debug(f"   Image size {original_size} bytes ({original_size / (1024*1024):.2f} MB) is under limit")
            # Still strip metadata and convert to JPEG for consistency
            img = Image.open(BytesIO(image_bytes))
            
            # Convert to RGB if needed
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Save as JPEG with metadata stripped
            output = BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            return output.getvalue(), '.jpg'
        
        logger.info(f"   📦 Image size {original_size} bytes ({original_size / (1024*1024):.2f} MB) exceeds {max_size_mb}MB, compressing...")
        
        # Open image from bytes
        img = Image.open(BytesIO(image_bytes))
        
        # Convert RGBA to RGB if needed (for JPEG)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Try JPEG compression first (quality 80-85)
        current_quality = min(quality, 85)  # Cap at 85
        output = BytesIO()
        ext = '.jpg'
        
        # Try compressing with decreasing quality until under limit
        for attempt in range(5):
            output.seek(0)
            output.truncate(0)
            img.save(output, format='JPEG', quality=current_quality, optimize=True)
            compressed_size = len(output.getvalue())
            
            if compressed_size <= max_size_bytes:
                logger.info(f"   ✅ Compressed to {compressed_size} bytes ({compressed_size / (1024*1024):.2f} MB) with JPEG quality {current_quality}")
                return output.getvalue(), ext
            
            # Reduce quality for next attempt
            current_quality = max(75, current_quality - 5)  # Don't go below 75
        
        # If still too large, try WebP (better compression)
        if compressed_size > max_size_bytes:
            logger.info(f"   ⚠️ JPEG still too large, trying WebP compression...")
            webp_quality = 80
            for attempt in range(3):
                output.seek(0)
                output.truncate(0)
                img.save(output, format='WEBP', quality=webp_quality, method=6)
                compressed_size = len(output.getvalue())
                
                if compressed_size <= max_size_bytes:
                    logger.info(f"   ✅ Compressed to {compressed_size} bytes ({compressed_size / (1024*1024):.2f} MB) with WebP quality {webp_quality}")
                    return output.getvalue(), '.webp'
                
                webp_quality = max(70, webp_quality - 5)
        
        # If still too large after WebP, resize image
        if compressed_size > max_size_bytes:
            logger.info(f"   ⚠️ Still too large after compression, resizing image...")
            # Calculate resize factor (aim for ~80% of max size)
            resize_factor = (max_size_bytes * 0.8 / compressed_size) ** 0.5
            new_width = int(img.width * resize_factor)
            new_height = int(img.height * resize_factor)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Try saving again with JPEG
            output.seek(0)
            output.truncate(0)
            img.save(output, format='JPEG', quality=80, optimize=True)
            compressed_size = len(output.getvalue())
            logger.info(f"   ✅ Compressed and resized to {compressed_size} bytes ({compressed_size / (1024*1024):.2f} MB)")
        
        return output.getvalue(), ext
        
    except ImportError:
        logger.warning("PIL/Pillow not installed, cannot compress images. Install with: pip install Pillow")
        return image_bytes, '.jpg'
    except Exception as e:
        logger.error(f"Error compressing image: {str(e)}", exc_info=True)
        return image_bytes, '.jpg'


if not FAL_KEY:
    logger.warning("FAL_KEY not found in environment variables")


# Removed upload_image_to_fal_storage - images now uploaded to Supabase Storage instead


async def generate_images(
    prompt: str, 
    num_images: int = 1,
    init_image_url: Optional[str] = None,  # Public URL image untuk image-to-image (dari Supabase Storage) - LEGACY, gunakan init_image_urls
    init_image_urls: Optional[List[str]] = None,  # Public URL images untuk image-to-image (dari Supabase Storage) - array untuk multiple images
    image_strength: Optional[float] = None,  # Image strength (optional, will use default if not provided)
    num_inference_steps: Optional[int] = None,  # Number of inference steps (optional, will use default if not provided)
    guidance_scale: Optional[float] = None,  # Guidance scale (CFG) (optional, will use default if not provided)
    negative_prompt: Optional[str] = None,  # Negative prompt untuk menghindari hasil yang tidak diinginkan
    aspect_ratio: Optional[str] = None  # Aspect ratio (e.g., "9:16", "16:9", "1:1") - untuk menentukan width/height
) -> List[str]:
    """
    Generate images using Fal.ai flux-2/lora/edit model
    - Image-to-image: jika init_image_url tersedia (model: flux-2/lora/edit - FLUX.2 [dev])
    - Text-to-image: jika init_image_url tidak tersedia (model: flux/schnell)
    
    DEFAULT PARAMETERS (Gambar pertama):
    - num_inference_steps: 24 (default - ini adalah INFERENCE, BUKAN training)
    - guidance_scale: 4.5 (default - natural and realistic, prevents mannequin-like results)
    - image_strength: 0.67 (default - untuk balanced reference adherence)
    
    ENHANCED PARAMETERS (Gambar kedua - dinamis untuk hasil lebih realistis):
    - num_inference_steps: 26 (+2 dari default, max 30)
    - guidance_scale: 4.95 (+10% dari default, max 6.0)
    - image_strength: 0.69 (+0.02 dari default, max 0.75)
    
    Args:
        prompt: Text prompt for image generation (tetap digunakan, dikombinasikan dengan init image)
        num_images: Number of images to generate (default: 2)
        init_image_url: Public URL image untuk image-to-image (dari Supabase Storage, optional)
        init_image_urls: Public URL images untuk image-to-image (dari Supabase Storage, optional)
    
    Returns:
        List of image URLs
    """
    if not FAL_KEY:
        raise ValueError("FAL_KEY is not configured")
    
    # Use provided parameters or fallback to defaults
    final_image_strength = image_strength if image_strength is not None else FAL_IMAGE_STRENGTH
    final_num_inference_steps = num_inference_steps if num_inference_steps is not None else FAL_NUM_INFERENCE_STEPS
    final_guidance_scale = guidance_scale if guidance_scale is not None else FAL_GUIDANCE_SCALE
    
    # Determine image URLs - prioritize init_image_urls (array), fallback to init_image_url (single) for backward compatibility
    image_urls_list = []
    if init_image_urls and len(init_image_urls) > 0:
        image_urls_list = init_image_urls
    elif init_image_url:
        image_urls_list = [init_image_url]  # Convert single URL to array for backward compatibility
    
    # Determine model endpoint based on image URLs availability
    use_image_to_image = len(image_urls_list) > 0
    # flux-2/lora/edit untuk image-to-image editing dengan LoRA support (FLUX.2 [dev]), flux/schnell untuk text-to-image
    model_endpoint = FAL_MODEL_ENDPOINT_IMAGE_TO_IMAGE if use_image_to_image else FAL_MODEL_ENDPOINT_TEXT_TO_IMAGE
    
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            images = []
            error_summaries: List[str] = []
            
            # Generate multiple images (one request per image)
            for i in range(num_images):
                try:
                    # Dynamic configuration for second image (i == 1) to make it more realistic
                    # First image (i == 0) uses default configuration
                    # Second image (i == 1) uses enhanced configuration for better realism
                    is_second_image = (i == 1)
                    
                    # Adjust parameters for second image to enhance realism
                    if is_second_image:
                        # Enhanced configuration for second image:
                        # - Slightly higher guidance_scale for better prompt adherence
                        # - Slightly higher num_inference_steps for more detail
                        # - Slightly adjusted image_strength for better balance
                        dynamic_guidance_scale = final_guidance_scale * 1.1  # 10% increase (e.g., 4.5 -> 4.95)
                        dynamic_num_inference_steps = final_num_inference_steps + 2  # +2 steps (e.g., 24 -> 26)
                        dynamic_image_strength = final_image_strength + 0.02  # Slight increase (e.g., 0.67 -> 0.69)
                        
                        # Clamp values to safe ranges
                        dynamic_guidance_scale = min(dynamic_guidance_scale, 6.0)  # Max CFG 6.0
                        dynamic_num_inference_steps = min(dynamic_num_inference_steps, 30)  # Max steps 30
                        dynamic_image_strength = min(dynamic_image_strength, 0.75)  # Max image strength 0.75
                        
                        current_image_strength = dynamic_image_strength
                        current_num_inference_steps = dynamic_num_inference_steps
                        current_guidance_scale = dynamic_guidance_scale
                        
                        logger.info(f"🎯 Using ENHANCED configuration for image {i+1} (second image) for better realism")
                        logger.info(f"   Image Strength: {current_image_strength:.2f} (enhanced from {final_image_strength:.2f})")
                        logger.info(f"   Steps: {current_num_inference_steps} (enhanced from {final_num_inference_steps})")
                        logger.info(f"   CFG: {current_guidance_scale:.2f} (enhanced from {final_guidance_scale:.2f})")
                    else:
                        # Default configuration for first image
                        current_image_strength = final_image_strength
                        current_num_inference_steps = final_num_inference_steps
                        current_guidance_scale = final_guidance_scale
                        
                        logger.info(f"📸 Using DEFAULT configuration for image {i+1} (first image)")
                    
                    # LOG: Request details (untuk debugging)
                    generation_type = "image-to-image" if use_image_to_image else "text-to-image"
                    logger.info(f"📤 Sending {generation_type} request to Fal.ai for image {i+1}/{num_images}")
                    logger.info(f"   Model: {model_endpoint}")
                    logger.info(f"   Prompt length: {len(prompt)} chars")
                    logger.info(f"   Prompt preview: {prompt[:200]}...")
                    if use_image_to_image and len(image_urls_list) > 0:
                        logger.info(f"   Init image URLs: {len(image_urls_list)} image(s)")
                        for idx, url in enumerate(image_urls_list[:3]):
                            logger.info(f"      [{idx+1}] {url[:80]}...")
                            logger.info(f"   Image Strength: {current_image_strength:.2f}")
                    logger.debug(f"   Full prompt: {prompt}")
                    
                    # Build request payload based on generation type
                    if use_image_to_image and len(image_urls_list) > 0:
                        # Image-to-image payload untuk fal-ai/flux-2/lora/edit
                        # Model ini menggunakan image_urls (plural - array)
                        # Support multiple images: face + products + background (max 3 images sesuai dokumentasi Fal.ai)
                        # Fal.ai flux-2/lora/edit dapat menerima hingga 3 images dalam array
                        request_payload = {
                            "prompt": prompt,  # Prompt tetap digunakan, dikombinasikan dengan init images
                            "image_urls": image_urls_list[:3],  # Public URLs dari Supabase Storage (array untuk flux-2/lora/edit, max 3 images)
                            "image_strength": current_image_strength,  # Dynamic: default for first image, enhanced for second
                            "num_inference_steps": current_num_inference_steps,  # Dynamic: default for first image, enhanced for second
                            "guidance_scale": current_guidance_scale  # Dynamic: default for first image, enhanced for second
                        }
                        
                        # Add width and height based on aspect ratio
                        if aspect_ratio:
                            width, height = get_resolution_from_aspect_ratio(aspect_ratio)
                            if width and height:
                                request_payload["width"] = width
                                request_payload["height"] = height
                                logger.info(f"   ✅ Resolution: {width}x{height} (aspect ratio: {aspect_ratio})")
                        
                        # Add negative prompt if provided
                        if negative_prompt:
                            request_payload["negative_prompt"] = negative_prompt
                            logger.info(f"   ✅ Negative prompt included: {negative_prompt[:100]}...")
                        
                        logger.info(f"   ✅ Image-to-image: Using {len(image_urls_list[:3])} image(s) from Supabase Storage")
                        logger.info(f"   📤 Image URLs yang dikirim ({len(image_urls_list[:3])} images):")
                        for idx, url in enumerate(image_urls_list[:3]):
                            logger.info(f"      [{idx+1}] {url[:100]}...")
                        if len(image_urls_list) > 3:
                            logger.warning(f"   ⚠️ More than 3 images provided. Only first 3 images will be used by Fal.ai.")
                        logger.info(f"   Model: fal-ai/flux-2/lora/edit (FLUX.2 [dev])")
                        logger.info(f"   Image Strength: {current_image_strength:.2f} ({'enhanced' if is_second_image else 'default'}: {FAL_IMAGE_STRENGTH})")
                        logger.info(f"   Inference Steps: {current_num_inference_steps} ({'enhanced' if is_second_image else 'default'}: {FAL_NUM_INFERENCE_STEPS})")
                        logger.info(f"   Guidance Scale: {current_guidance_scale:.2f} ({'enhanced' if is_second_image else 'default'}: {FAL_GUIDANCE_SCALE})")
                    else:
                        # This should NOT happen in image-to-image pipeline
                        # But kept as fallback for backward compatibility
                        raise ValueError(
                            "This is an image-to-image pipeline. init_image_urls or init_image_url is required. "
                            "Please provide at least one image (face_image, product_images, or background_image)."
                        )
                    
                    # Log FULL request payload untuk debugging (termasuk image_urls lengkap)
                    payload_for_log = {**request_payload}
                    if 'image_urls' in payload_for_log:
                        # Keep full URLs for logging (truncate each URL if too long)
                        image_urls_full = payload_for_log['image_urls']
                        payload_for_log['image_urls_full'] = image_urls_full  # Keep full URLs for logging
                        payload_for_log['image_urls'] = [
                            url[:100] + '...' if len(url) > 100 else url 
                            for url in image_urls_full
                        ]
                    elif 'image_url' in payload_for_log:  # Legacy support
                        payload_for_log['image_url_full'] = payload_for_log['image_url']
                        payload_for_log['image_url'] = payload_for_log['image_url'][:100] + '...' if len(payload_for_log['image_url']) > 100 else payload_for_log['image_url']
                    logger.info(f"   📤 FULL REQUEST PAYLOAD ke Fal.ai:")
                    logger.info(f"   {json.dumps(payload_for_log, indent=2)}")
                    logger.debug(f"   Full request payload (detailed): {json.dumps(request_payload, indent=2)}")
                    
                    response = await client.post(
                        f"{FAL_API_BASE}/{model_endpoint}",
                        headers={
                            "Authorization": f"Key {FAL_KEY}",
                            "Content-Type": "application/json"
                        },
                        json=request_payload
                    )
                    # Check response status before processing
                    if response.status_code == 403:
                        error_detail = response.text if hasattr(response, 'text') else response.content.decode('utf-8', errors='ignore')
                        logger.error(f"❌ Fal.ai API 403 Forbidden for image {i+1}. Response: {error_detail[:500]}")
                        logger.error(f"   Check FAL_KEY format and permissions. Current FAL_KEY starts with: {FAL_KEY[:20]}..." if FAL_KEY else "   FAL_KEY is not set")
                        raise ValueError(f"Fal.ai API access denied (403 Forbidden). Please check your FAL_KEY and API permissions. Response: {error_detail[:300]}")
                    
                    if response.status_code == 401:
                        error_detail = response.text if hasattr(response, 'text') else response.content.decode('utf-8', errors='ignore')
                        logger.error(f"❌ Fal.ai API 401 Unauthorized for image {i+1}. Response: {error_detail[:500]}")
                        logger.error(f"   Check FAL_KEY format. Current FAL_KEY starts with: {FAL_KEY[:20]}..." if FAL_KEY else "   FAL_KEY is not set")
                        raise ValueError(f"Fal.ai API authentication failed (401). Please check your FAL_KEY. Response: {error_detail[:300]}")
                    
                    # Raise for other HTTP errors
                    response.raise_for_status()
                    
                    # Parse JSON response
                    try:
                        result = response.json()
                        logger.debug(f"Fal.ai API response for image {i+1}: {json.dumps(result, indent=2)[:500]}")
                    except Exception as json_error:
                        error_text = response.text if hasattr(response, 'text') else response.content.decode('utf-8', errors='ignore')
                        logger.error(f"❌ Failed to parse JSON response for image {i+1}. Status: {response.status_code}, Text: {error_text[:500]}")
                        raise ValueError(f"Fal.ai API returned invalid JSON. Status: {response.status_code}, Error: {str(json_error)}")
                    
                    # Extract image URL(s) from response
                    # Fal.ai may return single image or array of images
                    extracted_urls = []
                    
                    # Try different response formats
                    if "images" in result:
                        if isinstance(result["images"], list) and len(result["images"]) > 0:
                            # Extract ALL images from array (not just first one)
                            for img_item in result["images"]:
                                img_url = img_item.get("url") if isinstance(img_item, dict) else img_item
                                if img_url:
                                    extracted_urls.append(img_url)
                        elif isinstance(result["images"], dict):
                            img_url = result["images"].get("url")
                            if img_url:
                                extracted_urls.append(img_url)
                    elif "image" in result:
                        img_data = result["image"]
                        img_url = img_data.get("url") if isinstance(img_data, dict) else img_data
                        if img_url:
                            extracted_urls.append(img_url)
                    elif "url" in result:
                        extracted_urls.append(result["url"])
                    elif "file" in result:
                        file_data = result["file"]
                        img_url = file_data.get("url") if isinstance(file_data, dict) else file_data
                        if img_url:
                            extracted_urls.append(img_url)
                    
                    # Process all extracted URLs
                    if extracted_urls:
                        logger.info(f"✅ Extracted {len(extracted_urls)} image URL(s) from Fal.ai response")
                        for idx, image_url in enumerate(extracted_urls):
                            # Compress and log image before adding to results
                            try:
                                compressed_url, metadata = await compress_and_log_image(
                                    image_url,
                                    width=request_payload.get("width") if "width" in request_payload else None,
                                    height=request_payload.get("height") if "height" in request_payload else None
                                )
                                images.append(compressed_url)
                                logger.info(f"✅ Generated and compressed image {len(images)}/{num_images} from Fal.ai: {compressed_url[:100]}...")
                            except Exception as comp_error:
                                logger.warning(f"⚠️ Compression failed for image {len(images)+1}, using original URL: {str(comp_error)}")
                                images.append(image_url)
                                logger.info(f"✅ Generated image {len(images)}/{num_images} from Fal.ai (uncompressed): {image_url[:100]}...")
                            
                            # If we have enough images, break from inner loop
                            if len(images) >= num_images:
                                break
                        
                        # If we have enough images, break from outer loop
                        if len(images) >= num_images:
                            break
                    
                    # If still no URLs extracted, check for async job
                    if not extracted_urls and ("request_id" in result or "job_id" in result):
                        # Handle async job (polling)
                        request_id = result.get("request_id") or result.get("job_id")
                        max_polls = 30
                        
                        for poll_count in range(max_polls):
                            await asyncio.sleep(2)
                            poll_response = await client.get(
                                f"{FAL_API_BASE}/{model_endpoint}/requests/{request_id}",
                                headers={"Authorization": f"Key {FAL_KEY}"}
                            )
                            poll_result = poll_response.json()
                            
                            if poll_result.get("status") == "COMPLETED":
                                # Extract all images from async result
                                poll_urls = []
                                if "images" in poll_result:
                                    if isinstance(poll_result["images"], list):
                                        for img_item in poll_result["images"]:
                                            img_url = img_item.get("url") if isinstance(img_item, dict) else img_item
                                            if img_url:
                                                poll_urls.append(img_url)
                                    elif isinstance(poll_result["images"], dict):
                                        img_url = poll_result["images"].get("url")
                                        if img_url:
                                            poll_urls.append(img_url)
                                elif "image" in poll_result:
                                    img_url = poll_result["image"].get("url") if isinstance(poll_result["image"], dict) else poll_result["image"]
                                    if img_url:
                                        poll_urls.append(img_url)
                                elif "url" in poll_result:
                                    poll_urls.append(poll_result["url"])
                                
                                if poll_urls:
                                    extracted_urls = poll_urls
                                    logger.info(f"✅ Extracted {len(extracted_urls)} image URL(s) from async job result")
                                    # Process extracted URLs from async job
                                    for idx, image_url in enumerate(extracted_urls):
                                        try:
                                            compressed_url, metadata = await compress_and_log_image(
                                                image_url,
                                                width=request_payload.get("width") if "width" in request_payload else None,
                                                height=request_payload.get("height") if "height" in request_payload else None
                                            )
                                            images.append(compressed_url)
                                            logger.info(f"✅ Generated and compressed image {len(images)}/{num_images} from async job: {compressed_url[:100]}...")
                                        except Exception as comp_error:
                                            logger.warning(f"⚠️ Compression failed, using original URL: {str(comp_error)}")
                                            images.append(image_url)
                                            logger.info(f"✅ Generated image {len(images)}/{num_images} from async job (uncompressed): {image_url[:100]}...")
                                        
                                        if len(images) >= num_images:
                                            break
                                    
                                    if len(images) >= num_images:
                                        break
                                break
                            elif poll_result.get("status") == "FAILED":
                                logger.warning(f"Fal.ai job {request_id} failed")
                                break
                    
                        # Fallback: try to find URL in response text if still no URLs
                    if not extracted_urls:
                        logger.warning(f"⚠️ Could not extract image URL from Fal.ai response. Full response: {json.dumps(result, indent=2)[:1000]}")
                        # Try to find any URL-like field in the response
                        response_str = json.dumps(result)
                        import re
                        urls = re.findall(r'https?://[^\s"\'<>]+', response_str)
                        if urls:
                            logger.info(f"Found potential URLs in response: {urls[:3]}")
                            # Use all found URLs (up to num_images needed)
                            for url_idx, url in enumerate(urls):
                                if len(images) >= num_images:
                                    break
                                images.append(url)
                                logger.info(f"✅ Using URL found in response ({len(images)}/{num_images}): {url}")
                            else:
                                logger.error(f"❌ No image URL found in Fal.ai response for image {i+1}")
                                error_summaries.append(f"image {i+1}: no image URL in Fal.ai response")
                        
                except ValueError as e:
                    # Re-raise ValueError (it's already a meaningful error message from 401/403)
                    raise
                except httpx.HTTPStatusError as e:
                    error_detail = e.response.text if hasattr(e.response, 'text') else str(e)
                    logger.error(f"HTTP Error generating image {i+1}: {e.response.status_code} - {error_detail[:500]}")
                    error_summaries.append(f"image {i+1}: HTTP {e.response.status_code} - {error_detail[:200]}")
                    # If it's 401/403, don't continue - it's an auth issue
                    if e.response.status_code in (401, 403):
                        raise ValueError(f"Fal.ai API authentication/authorization failed ({e.response.status_code}): {error_detail[:300]}")
                    # Continue with next image for other HTTP errors (but log warning)
                    logger.warning(f"Skipping image {i+1} due to HTTP error {e.response.status_code}")
                except Exception as e:
                    logger.error(f"Error generating image {i+1}: {str(e)}", exc_info=True)
                    error_summaries.append(f"image {i+1}: {type(e).__name__} - {str(e)[:200]}")
                    # Continue with next image even if one fails (but log error)
            
            if not images:
                error_hint = " | ".join(error_summaries[-3:]) if error_summaries else "Unknown error (no details from Fal.ai)"
                raise ValueError(f"No images generated from Fal.ai. Last errors: {error_hint}")
            
            logger.info(f"Successfully generated {len(images)}/{num_images} images from Fal.ai")
            return images
            
    except httpx.HTTPStatusError as e:
        error_text = e.response.text if hasattr(e.response, 'text') else str(e)
        logger.error(f"Fal.ai API error: {e.response.status_code} - {error_text}")
        raise ValueError(f"Fal.ai API error: {e.response.status_code} - {error_text}")
    except Exception as e:
        logger.error(f"Error generating images with Fal.ai: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to generate images: {str(e)}")


async def generate_video(prompt: str, image_url: Optional[str] = None) -> str:
    """
    Generate video using Fal.ai kling-v2/video-generation model
    
    Args:
        prompt: Text prompt for video generation
        image_url: Optional image URL to animate
    
    Returns:
        Video URL
    """
    if not FAL_KEY:
        raise ValueError("FAL_KEY is not configured")
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:  # Longer timeout for video
            payload = {
                "prompt": prompt,
                "duration": 5,  # 5 seconds video
                "aspect_ratio": "16:9"
            }
            
            if image_url:
                payload["image_url"] = image_url
            
            # Submit job
            submit_response = await client.post(
                f"{FAL_API_BASE}/fal-ai/kling-v2/video-generation",
                headers={
                    "Authorization": f"Key {FAL_KEY}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            submit_response.raise_for_status()
            submit_result = submit_response.json()
            
            # Check if async job or direct result
            if "request_id" in submit_result or "job_id" in submit_result:
                # Async job - poll for result
                request_id = submit_result.get("request_id") or submit_result.get("job_id")
                max_polls = 60  # Video takes longer
                poll_count = 0
                
                while poll_count < max_polls:
                    await asyncio.sleep(3)  # Wait 3 seconds between polls
                    poll_response = await client.get(
                        f"{FAL_API_BASE}/fal-ai/kling-v2/video-generation/requests/{request_id}",
                        headers={"Authorization": f"Key {FAL_KEY}"}
                    )
                    poll_result = poll_response.json()
                    
                    if poll_result.get("status") == "COMPLETED":
                        video_url = None
                        if "video" in poll_result:
                            video_data = poll_result["video"]
                            video_url = video_data.get("url") if isinstance(video_data, dict) else video_data
                        elif "url" in poll_result:
                            video_url = poll_result["url"]
                        elif "video_url" in poll_result:
                            video_url = poll_result["video_url"]
                        
                        if video_url:
                            logger.info(f"Generated video from Fal.ai: {video_url}")
                            return video_url
                    elif poll_result.get("status") == "FAILED":
                        logger.error(f"Fal.ai video job failed: {poll_result}")
                        raise ValueError("Video generation failed")
                    
                    poll_count += 1
                
                raise ValueError("Video generation timeout")
            else:
                # Direct result
                video_url = None
                if "video" in submit_result:
                    video_data = submit_result["video"]
                    video_url = video_data.get("url") if isinstance(video_data, dict) else video_data
                elif "url" in submit_result:
                    video_url = submit_result["url"]
                elif "video_url" in submit_result:
                    video_url = submit_result["video_url"]
                
                if not video_url:
                    logger.error(f"No video URL found in Fal.ai response: {submit_result}")
                    raise ValueError("No video generated from Fal.ai")
                
                logger.info(f"Generated video from Fal.ai: {video_url}")
                return video_url
            
    except httpx.HTTPStatusError as e:
        logger.error(f"Fal.ai API error: {e.response.status_code} - {e.response.text}")
        raise ValueError(f"Fal.ai API error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        logger.error(f"Error generating video with Fal.ai: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to generate video: {str(e)}")


async def generate_kling_image_to_video(prompt: str, image_url: str, negative_prompt: Optional[str] = None) -> str:
    """
    Generate video using fal-ai/kling-video/v2.1/standard/image-to-video
    """
    if not FAL_KEY:
        raise ValueError("FAL_KEY is not configured")
    if not image_url:
        raise ValueError("image_url is required")

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            payload = {
                "prompt": prompt,
                "image_url": image_url,
                "duration": 5,
                "aspect_ratio": "9:16"
            }
            if negative_prompt:
                payload["negative_prompt"] = negative_prompt

            submit_response = await client.post(
                f"{FAL_API_BASE}/fal-ai/kling-video/v2.1/standard/image-to-video",
                headers={
                    "Authorization": f"Key {FAL_KEY}",
                    "Content-Type": "application/json"
                },
                json=payload
            )
            submit_response.raise_for_status()
            submit_result = submit_response.json()

            request_id = submit_result.get("request_id") or submit_result.get("job_id")
            if request_id:
                max_polls = 60
                poll_count = 0
                while poll_count < max_polls:
                    await asyncio.sleep(3)
                    poll_response = await client.get(
                        f"{FAL_API_BASE}/fal-ai/kling-video/v2.1/standard/image-to-video/requests/{request_id}",
                        headers={"Authorization": f"Key {FAL_KEY}"}
                    )
                    poll_result = poll_response.json()
                    if poll_result.get("status") == "COMPLETED":
                        video_url = None
                        if "video" in poll_result:
                            video_data = poll_result["video"]
                            video_url = video_data.get("url") if isinstance(video_data, dict) else video_data
                        elif "url" in poll_result:
                            video_url = poll_result["url"]
                        elif "video_url" in poll_result:
                            video_url = poll_result["video_url"]
                        if video_url:
                            logger.info(f"Generated Kling video: {video_url}")
                            return video_url
                    elif poll_result.get("status") == "FAILED":
                        raise ValueError(f"Kling video generation failed: {poll_result}")
                    poll_count += 1
                raise ValueError("Kling video generation timed out")

            if "video" in submit_result:
                video_data = submit_result["video"]
                video_url = video_data.get("url") if isinstance(video_data, dict) else video_data
                if video_url:
                    return video_url
            if "video_url" in submit_result:
                return submit_result["video_url"]

            raise ValueError(f"Unexpected response from Kling video: {submit_result}")
    except httpx.HTTPStatusError as e:
        error_text = e.response.text if hasattr(e.response, 'text') else str(e)
        logger.error(f"Fal.ai Kling API error: {e.response.status_code} - {error_text}")
        raise ValueError(f"Fal.ai Kling API error: {e.response.status_code} - {error_text}")
    except Exception as e:
        logger.error(f"Error generating Kling video: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to generate Kling video: {str(e)}")

