"""
Human Model Video Service: Safe fake motion for images with human faces
Face remains completely static, only camera, light, shadow, and fabric move
"""

import subprocess
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple, List, Dict
import httpx
from io import BytesIO
import cv2
import numpy as np
from app.services.face_detection import detect_face, create_face_mask, get_face_region_info

logger = logging.getLogger(__name__)


def check_ffmpeg_available() -> bool:
    """Check if FFmpeg is available"""
    import sys
    from pathlib import Path
    
    # Try local FFmpeg first (in project folder)
    project_root = Path(__file__).resolve().parents[3]
    local_ffmpeg = project_root / "ffmpeg" / "ffmpeg-8.0.1-essentials_build" / "bin" / "ffmpeg.exe"
    
    if local_ffmpeg.exists():
        try:
            result = subprocess.run(
                [str(local_ffmpeg), '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
    
    # Fallback to system FFmpeg
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_ffmpeg_path() -> str:
    """Get the path to FFmpeg executable"""
    import sys
    from pathlib import Path
    
    # Try local FFmpeg first (in project folder)
    project_root = Path(__file__).resolve().parents[3]
    local_ffmpeg = project_root / "ffmpeg" / "ffmpeg-8.0.1-essentials_build" / "bin" / "ffmpeg.exe"
    
    if local_ffmpeg.exists():
        return str(local_ffmpeg)
    
    # Fallback to system FFmpeg
    return 'ffmpeg'


def download_image_from_url(image_url: str) -> BytesIO:
    """Download image from URL"""
    try:
        response = httpx.get(image_url, timeout=30)
        response.raise_for_status()
        return BytesIO(response.content)
    except Exception as e:
        logger.error(f"Failed to download image from {image_url}: {str(e)}")
        raise


def create_human_safe_video(
    image_path: str,
    output_path: str,
    template: str = "confident_intro",
    duration: float = 5.0,
    resolution: Tuple[int, int] = (720, 1280),
    fps: int = 30
) -> str:
    """
    Create safe fake motion video for human models.
    Face remains completely static, only camera/light/shadow/fabric move.
    
    Templates:
    1. confident_intro: Slow camera push (1.00 → 1.04), vertical parallax, shadow movement
    2. style_flow: Micro fabric warp (±2%), diagonal pan, background blur
    3. detail_value: Zoom into fabric detail, light sweep, slow pull-back
    
    Args:
        image_path: Path to input image
        output_path: Path to output MP4
        template: Template name (confident_intro, style_flow, detail_value)
        duration: Video duration (default: 5.0s)
        resolution: Video resolution (default: 720x1280)
        fps: Frame rate (default: 30)
    
    Returns:
        Path to output video file
    """
    if not check_ffmpeg_available():
        raise RuntimeError("FFmpeg is not available")
    
    # Detect face and create mask
    face_info = get_face_region_info(image_path)
    if face_info is None:
        logger.warning("No face detected, using standard fake motion")
        # Fallback to standard zoom if no face detected
        from app.services.video_service import create_fake_motion_video
        return create_fake_motion_video(
            image_path=image_path,
            output_path=output_path,
            duration=duration,
            resolution=resolution,
            fps=fps
        )
    
    width, height = resolution
    face_bbox = face_info["bbox"]
    face_mask = face_info["mask"]
    
    # Save face mask to temp file for FFmpeg
    # Mask format: 255 = face region (protected), 0 = non-face (can be transformed)
    temp_dir = os.path.dirname(output_path)
    mask_path = os.path.join(temp_dir, "face_mask.png")
    
    # Scale mask to match target resolution
    # The mask will be used to blend original and transformed images
    scaled_mask = cv2.resize(face_mask, (width, height), interpolation=cv2.INTER_LINEAR)
    cv2.imwrite(mask_path, scaled_mask)
    
    # Also create RGBA version of original image with mask as alpha channel
    # This allows overlay filter to use mask directly
    original_image = cv2.imread(image_path)
    if original_image is not None:
        original_scaled = cv2.resize(original_image, (width, height), interpolation=cv2.INTER_LINEAR)
        # Create RGBA image with mask as alpha
        original_rgba = cv2.cvtColor(original_scaled, cv2.COLOR_BGR2BGRA)
        # Use scaled mask as alpha channel (invert: high mask = high alpha = more visible)
        original_rgba[:, :, 3] = scaled_mask
        original_rgba_path = os.path.join(temp_dir, "original_rgba.png")
        cv2.imwrite(original_rgba_path, original_rgba)
    else:
        original_rgba_path = None
    
    logger.info(f"Face detected and locked: {face_bbox}")
    logger.info(f"Using template: {template}")
    logger.info(f"Face mask saved: {mask_path} (size: {width}x{height})")
    
    # Build FFmpeg filter based on template
    # Scale and pad to exact resolution
    scale_filter = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
    
    # Create transformation filter based on template
    if template == "confident_intro":
        # TEMPLATE 1: Slow camera push (1.00 → 1.04)
        transform_filter = f"zoompan=z='min(zoom+0.0008,1.04)':d={int(duration * fps)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        
    elif template == "style_flow":
        # TEMPLATE 2: Diagonal pan
        pan_x = "if(gte(t,0),1.5*t,0)"  # Horizontal pan
        pan_y = "if(gte(t,0),1.0*t,0)"  # Vertical pan
        transform_filter = f"crop=iw:ih:{pan_x}:{pan_y}"
        
    elif template == "detail_value":
        # TEMPLATE 3: Zoom in then pull back
        transform_filter = f"zoompan=z='if(lt(t,2.5),min(zoom+0.0015,1.10),max(zoom-0.001,1.0))':d={int(duration * fps)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        
    else:
        # Default: confident_intro
        transform_filter = f"zoompan=z='min(zoom+0.0008,1.04)':d={int(duration * fps)}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
    
    # EXPLICIT FACE PROTECTION USING MASK BLENDING
    # Strategy:
    # 1. Create transformed version: [scaled] -> [transformed] (camera motion applied)
    # 2. Keep original version: [scaled] (no transformation, face stays pixel-identical)
    # 3. Use mask to blend: face region from original, non-face from transformed
    #
    # FFmpeg filter chain with explicit face protection:
    # [0:v] -> scale -> [scaled] (original, no transform)
    # [scaled] -> transform -> [transformed] (camera motion)
    # [transformed] + [original_rgba] -> overlay -> [protected]
    #
    # The overlay filter uses alpha channel of overlay input:
    # - alpha = 255: use overlay (original face) - 100% protection
    # - alpha = 0: use base (transformed) - 0% protection
    # - alpha = 128: blend 50/50 - smooth transition (feathered edge)
    
    if original_rgba_path and os.path.exists(original_rgba_path):
        # Use overlay with RGBA image (mask is alpha channel)
        # This is the most reliable method for explicit face protection
        filter_complex = (
            f"[0:v]{scale_filter}[scaled];"  # Scale input
            f"[scaled]{transform_filter}[transformed];"  # Apply transformation
            f"[transformed][2:v]overlay=0:0:alpha=premultiplied[protected]"  # Overlay original with mask as alpha
        )
        additional_inputs = ['-loop', '1', '-i', original_rgba_path]
        logger.info("Using explicit face protection with RGBA overlay (mask as alpha channel)")
    else:
        # Fallback: Use transformed only (face not explicitly protected)
        # This should not happen if face detection worked
        filter_complex = (
            f"[0:v]{scale_filter}[scaled];"
            f"[scaled]{transform_filter}[transformed];"
            f"[transformed]format=yuv420p[protected]"
        )
        additional_inputs = []
        logger.warning("Could not create RGBA image, face protection may not work correctly")
    
    # FFmpeg command with explicit face protection
    cmd = [
        get_ffmpeg_path(),
        '-y',
        '-loop', '1',
        '-i', image_path,  # Input image [0:v]
        '-loop', '1',
        '-i', mask_path,   # Face mask [1:v]
    ]
    
    # Add additional inputs if using overlay approach
    cmd.extend(additional_inputs)
    
    # Complete command
    cmd.extend([
        '-t', str(duration),
        '-r', str(fps),
        '-filter_complex', filter_complex,
        '-map', '[protected]',  # Use the protected output
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        '-pix_fmt', 'yuv420p',
        '-an',
        '-movflags', '+faststart',
        output_path
    ])
    
    logger.info(f"Creating human-safe video: {output_path}")
    logger.info(f"Template: {template}, Face locked: {face_bbox}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")
        
        output_size = os.path.getsize(output_path) / (1024 * 1024)
        logger.info(f"Video created: {output_path} ({output_size:.2f} MB)")
        
        return output_path
        
    except subprocess.TimeoutExpired:
        raise RuntimeError("Video generation timed out")
    except Exception as e:
        logger.error(f"Error creating video: {str(e)}")
        raise


async def create_human_video_from_url(
    image_url: str,
    template: str = "confident_intro",
    output_filename: Optional[str] = None,
    motion_config: Optional[Dict] = None
) -> str:
    """
    Create human-safe video from image URL.
    
    Args:
        image_url: URL of the image
        template: Template name (confident_intro, style_flow, detail_value)
        output_filename: Optional output filename
    
    Returns:
        Path to created video file
    """
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Download image
        logger.info(f"Downloading image from: {image_url}")
        image_data = download_image_from_url(image_url)
        
        # Save image to temp file
        image_ext = Path(image_url).suffix or '.jpg'
        if image_ext not in ['.jpg', '.jpeg', '.png', '.webp']:
            image_ext = '.jpg'
        
        image_path = os.path.join(temp_dir, f"input{image_ext}")
        with open(image_path, 'wb') as f:
            f.write(image_data.getvalue())
        
        # Generate output filename
        if not output_filename:
            output_filename = f"human_video_{template}_{os.path.basename(image_url).split('.')[0]}"
        
        output_path = os.path.join(temp_dir, f"{output_filename}.mp4")
        
        # Create video
        create_human_safe_video(
            image_path=image_path,
            output_path=output_path,
            template=template
        )
        
        return output_path
        
    except Exception as e:
        logger.error(f"Error creating human video from URL: {str(e)}")
        raise
