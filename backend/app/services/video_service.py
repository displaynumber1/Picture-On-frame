"""
Video Service: Convert static images to TikTok-ready videos with fake motion
Uses FFmpeg for rendering (no GPU, no AI)
"""

import subprocess
import logging
import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple
import httpx
from io import BytesIO

logger = logging.getLogger(__name__)


def check_ffmpeg_available() -> bool:
    """Check if FFmpeg is available in the system"""
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
    """Download image from URL and return as BytesIO"""
    try:
        response = httpx.get(image_url, timeout=30)
        response.raise_for_status()
        return BytesIO(response.content)
    except Exception as e:
        logger.error(f"Failed to download image from {image_url}: {str(e)}")
        raise


def generateVideoFromImage(
    image_path: str,
    output_path: str,
    duration: float = 15.0,
    resolution: Tuple[int, int] = (1080, 1920),
    fps: int = 60,
    zoom_end: float = 1.36,
    rotate_degrees: float = 0.0,
    focus_x: Optional[float] = None,
    focus_y: Optional[float] = None,
    zoom_expr_override: Optional[str] = None,
    x_expr_override: Optional[str] = None,
    y_expr_override: Optional[str] = None
) -> str:
    """
    Generate a cinematic zoom-in video from a single image using FFmpeg.
    - 9:16 (1080x1920), 60 FPS
    - Supersampling (scale up first, then crop)
    - Easing zoom (sin/cos curve, no linear zoom)
    - No overlays, no alpha, no aspect distortion
    """
    if not check_ffmpeg_available():
        raise RuntimeError("FFmpeg is not available. Please install FFmpeg to use video generation.")

    width, height = resolution
    total_frames = int(duration * fps)
    ss_width, ss_height = width * 2, height * 2  # supersampling (2x)

    # Easing zoom: z='1+amp*(1-cos(on*PI/total_frames))/2'
    # Smooth zoom-in from 1.0 to zoom_end without jitter
    zoom_amp = max(zoom_end - 1.0, 0.001)
    pi = 3.14159265359
    zoom_expr = f"1+{zoom_amp}*(1-cos(on*{pi}/{total_frames}))/2"
    if zoom_expr_override:
        zoom_expr = zoom_expr_override

    # FFmpeg filter chain (single command string)
    # NOTE: Keep expressions quoted exactly to avoid parse errors.
    rotate_filter = ""
    if abs(rotate_degrees) > 0.0001:
        rotate_rad = rotate_degrees * pi / 180.0
        rotate_filter = (
            f",rotate=({rotate_rad})*sin(on*{pi}/{total_frames}):"
            "c=black:ow=iw:oh=ih"
        )

    base_x_expr = "iw/2-(iw/zoom/2)"
    base_y_expr = "ih/2-(ih/zoom/2)"
    if x_expr_override:
        base_x_expr = x_expr_override
    if y_expr_override:
        base_y_expr = y_expr_override
    if (x_expr_override is None and y_expr_override is None and
        focus_x is not None and focus_y is not None):
        fx = max(0.1, min(0.9, float(focus_x)))
        fy = max(0.1, min(0.9, float(focus_y)))
        offset_x = f"({fx - 0.5:.6f})*iw*0.25"
        offset_y = f"({fy - 0.5:.6f})*ih*0.25"
        base_x_expr = f"min(max({base_x_expr}+{offset_x},0),iw-iw/zoom)"
        base_y_expr = f"min(max({base_y_expr}+{offset_y},0),ih-ih/zoom)"

    filter_complex = (
        f"[0:v]format=rgba,colorchannelmixer=aa=1.0,"
        f"scale={ss_width}:{ss_height}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={ss_width}:{ss_height}:(iw-{ss_width})/2:(ih-{ss_height})/2"
        f"{rotate_filter}[img];"
        f"[1:v][img]overlay=0:0:format=auto,format=rgb24,"
        f"zoompan=z='{zoom_expr}':x='{base_x_expr}':y='{base_y_expr}':d={total_frames}:s={width}x{height},"
        f"setsar=1,fps={fps}[v]"
    )

    cmd = [
        get_ffmpeg_path(),
        "-y",
        "-loop", "1",
        "-framerate", str(fps),
        "-i", image_path,
        "-f", "lavfi",
        "-i", f"color=c=black:s={ss_width}x{ss_height}:r={fps}",
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-t", str(duration),
        "-shortest",
        "-c:v", "libx264",
        "-profile:v", "high",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_path
    ]

    logger.info(f"Creating cinematic video from image: {image_path}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Resolution: {width}x{height}, FPS: {fps}, Duration: {duration}s")
    logger.info(f"Zoom end: {zoom_end:.3f}, Supersample: {ss_width}x{ss_height}")
    logger.debug(f"Filter complex: {filter_complex}")
    logger.debug(f"FFmpeg command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        logger.error(f"FFmpeg error: {result.stderr}")
        raise RuntimeError(f"FFmpeg failed: {result.stderr}")

    return output_path


def create_fake_motion_video(
    image_path: str,
    output_path: str,
    hook_text: str = "Check This Out!",
    cta_text: str = "Shop Now",
    duration: float = 15.0,
    resolution: Tuple[int, int] = (1080, 1920),
    fps: int = 60,
    zoom_start: float = 1.0,
    zoom_end: float = 1.08,
    zoom_speed: float = 0.0015,
    hook_position: str = "top",  # top, center, bottom
    hook_timing: Tuple[float, float] = (0.0, 1.2),
    cta_position: str = "bottom",  # top, center, bottom
    cta_timing: Tuple[float, float] = (3.0, 5.0),
    pan_x: float = 0.0,  # Pan offset X (normalized -0.1 to 0.1)
    pan_y: float = 0.0,  # Pan offset Y (normalized -0.1 to 0.1)
    pan_speed: float = 0.0,  # Pan speed per frame
    rotate: float = 0.0,  # Rotation in degrees (0 = no rotation)
    focus_x: Optional[float] = None,
    focus_y: Optional[float] = None,
    zoom_expr_override: Optional[str] = None,
    x_expr_override: Optional[str] = None,
    y_expr_override: Optional[str] = None
) -> str:
    """
    Create a TikTok-ready video from a static image with fake motion effect.
    
    Args:
        image_path: Path to input image file
        output_path: Path to output MP4 file
        hook_text: Text that appears at the start (0s, duration 1.2s)
        cta_text: CTA text that appears later (3s, duration 2s)
        duration: Video duration in seconds (default: 5.0)
        resolution: Video resolution (width, height) - default: (1080, 1920) for 9:16
        fps: Frame rate (default: 60)
        zoom_start: Initial zoom scale (default: 1.0)
        zoom_end: Final zoom scale (default: 1.08)
    
    Returns:
        Path to output video file
    
    FFmpeg Command Breakdown:
    1. Input: Single image file
    2. Scale filter: Resize image to match video resolution (maintains aspect ratio, centers with padding)
    3. Zoom filter: Smooth zoom-in from 1.0 to 1.08 over duration (ease-in-out)
    4. Text overlays:
       - Hook text: Appears at 0s, fades in with scale, disappears at 1.2s
       - CTA text: Appears at 3s, fades in, disappears at 5s
    5. Output: MP4, 30fps, no audio, optimized for TikTok
    """
    if not check_ffmpeg_available():
        raise RuntimeError("FFmpeg is not available. Please install FFmpeg to use video generation.")

    # Use the new cinematic pipeline (no overlays, no pan, easing zoom)
    return generateVideoFromImage(
        image_path=image_path,
        output_path=output_path,
        duration=duration,
        resolution=resolution,
        fps=fps,
        zoom_end=zoom_end,
        rotate_degrees=rotate,
        focus_x=focus_x,
        focus_y=focus_y,
        zoom_expr_override=zoom_expr_override,
        x_expr_override=x_expr_override,
        y_expr_override=y_expr_override
    )
    
    width, height = resolution
    
    # FFmpeg filter chain explanation:
    # [0:v] - Input video stream (from image)
    # scale=w:h:force_original_aspect_ratio=decrease,pad=w:h:(ow-iw)/2:(oh-ih)/2
    #   - Scale image to fit resolution while maintaining aspect ratio
    #   - Pad with black bars if needed, centered
    # zoompan=z='min(zoom+0.0015,1.08)':d=150:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'
    #   - Smooth zoom from 1.0 to 1.08 over 150 frames (5s at 30fps)
    #   - Keeps subject centered during zoom
    #   - ease-in-out effect via gradual zoom increase
    
    # Text overlay filters:
    # drawtext for hook text:
    #   - fontsize: Large bold text
    #   - x/y: Centered position
    #   - enable: Only visible from 0s to 1.2s
    #   - alpha: Fade in/out with scale effect
    # drawtext for CTA text:
    #   - fontsize: Smaller than hook
    #   - x/y: Centered position
    #   - enable: Only visible from 3s to 5s
    #   - alpha: Fade in only
    
    # Calculate text positions (centered)
    hook_fontsize = int(height * 0.08)  # 8% of height for hook text
    cta_fontsize = int(height * 0.06)   # 6% of height for CTA text
    
    # Hook text timing: from hook_timing tuple
    hook_start_time, hook_end_time = hook_timing
    hook_start_frame = int(hook_start_time * fps)
    hook_end_frame = int(hook_end_time * fps)
    hook_total_frames = hook_end_frame - hook_start_frame
    
    # CTA text timing: from cta_timing tuple
    cta_start_time, cta_end_time = cta_timing
    cta_start_frame = int(cta_start_time * fps)
    cta_end_frame = int(cta_end_time * fps)
    cta_total_frames = cta_end_frame - cta_start_frame
    
    # Build FFmpeg filter complex
    # Scale and pad to exact resolution
    scale_filter = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2"
    
    # STABLE ZOOM FILTER (NO JITTER, NO CONDITIONAL) - EXACT STRUCTURE
    # Target format:
    # zoompan=z='1+0.0008*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=150:s=WIDTHxHEIGHT,fps=30
    total_frames = int(duration * fps)
    zoom_speed_per_frame = zoom_speed

    # Linear zoom only: z='1+speed*on' (no conditionals)
    # Keep camera centered (no pan) for stable zoom-in
    zoom_expr = "1" if zoom_speed_per_frame <= 0 else f"1+{zoom_speed_per_frame}*on"
    pan_x_expr = "iw/2-(iw/zoom/2)"
    pan_y_expr = "ih/2-(ih/zoom/2)"

    # Always wrap expressions in single quotes to match FFmpeg format
    zoom_filter = (
        f"zoompan=z='{zoom_expr}':"
        f"x='{pan_x_expr}':"
        f"y='{pan_y_expr}':"
        f"d={total_frames}:"
        f"s={width}x{height}"
    )
    fps_filter = f"fps={fps}"
    
    # Add rotation filter if specified (subtle rotation only, max 2 degrees for safety)
    rotate_filter = None
    if abs(rotate) > 0.01:
        # Clamp rotation to safe range (-2 to +2 degrees)
        rotate_clamped = max(-2.0, min(2.0, rotate))
        # Convert degrees to radians for FFmpeg rotate filter
        rotate_rad = rotate_clamped * 3.14159265359 / 180.0
        # Rotate filter: rotate=angle:fillcolor=black@0:ow=iw:oh=ih
        rotate_filter = f"rotate={rotate_rad}:fillcolor=black@0:ow=iw:oh=ih"
        logger.debug(f"Rotation applied: {rotate_clamped} degrees ({rotate_rad:.4f} radians)")
    
    # Hook text filter with fade and scale - escape commas in expressions
    # enable=between(t\\,start\\,end): Only show during hook_timing
    # alpha: Fade in (0→1) over first 0.3s, fade out (1→0) over last 0.3s
    # fontsize: Large bold text
    hook_fade_duration = 0.3
    # Don't escape here - escape_expression will handle it
    hook_alpha_in = f"if(lt(t,{hook_start_time+hook_fade_duration}),(t-{hook_start_time})/{hook_fade_duration},1)"  # Fade in
    hook_alpha_out = f"if(gt(t,{hook_end_time-hook_fade_duration}),({hook_end_time}-t)/{hook_fade_duration},1)"  # Fade out
    hook_alpha = f"{hook_alpha_in}*{hook_alpha_out}"
    
    # Calculate hook text Y position based on hook_position
    if hook_position == "top":
        hook_y = f"(h-text_h)/2-{int(height*0.20)}"  # Upper area
    elif hook_position == "center":
        hook_y = "(h-text_h)/2"  # Center
    else:  # bottom
        hook_y = f"(h-text_h)/2+{int(height*0.20)}"  # Lower area
    
    # Cross-platform font path detection
    import platform
    system = platform.system()
    
    def get_font_path():
        """Get system font path based on OS"""
        if system == "Windows":
            # Use forward slashes for FFmpeg compatibility
            return "C:/Windows/Fonts/arial.ttf"
        elif system == "Darwin":  # macOS
            return "/System/Library/Fonts/Helvetica.ttc"
        else:  # Linux
            return "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    
    font_path = get_font_path()
    
    # Escape text for FFmpeg drawtext
    # Escape spaces with backslash, escape commas in expressions
    def escape_text(text: str) -> str:
        """Escape special characters for FFmpeg drawtext text parameter"""
        return text.replace("\\", "\\\\").replace(" ", "\\ ").replace(":", "\\:")
    
    def escape_expression(expr: str) -> str:
        """Escape commas in FFmpeg expressions"""
        return expr.replace(",", "\\,")
    
    hook_text_escaped = escape_text(hook_text)
    cta_text_escaped = escape_text(cta_text)
    
    # Font path for Windows: C\\:/Windows/Fonts/arial.ttf (double backslash before colon, no quotes)
    if system == "Windows":
        # Format: C\\:/Windows/Fonts/arial.ttf
        font_path_normalized = font_path.replace('\\', '/')
        if len(font_path_normalized) >= 2 and font_path_normalized[1] == ':':
            font_path_escaped = font_path_normalized[0] + '\\\\:' + font_path_normalized[2:]
        else:
            font_path_escaped = font_path_normalized
    else:
        font_path_escaped = font_path
    
    # Build hook text filter - NO QUOTES, escape commas in expressions
    hook_enable_expr = escape_expression(f"between(t,{hook_start_time},{hook_end_time})")
    hook_alpha_expr = escape_expression(hook_alpha)
    hook_text_filter = (
        f"drawtext=text={hook_text_escaped}:"
        f"fontsize={hook_fontsize}:"
        f"fontcolor=white:"
        f"x=(w-text_w)/2:"
        f"y={hook_y}:"
        f"enable={hook_enable_expr}:"
        f"alpha={hook_alpha_expr}:"
        f"fontfile={font_path_escaped}"
    )
    
    # CTA text filter with fade in - escape commas in expressions
    # enable=between(t\\,start\\,end): Only show during cta_timing
    # alpha: Fade in (0→1) over first 0.5s
    cta_fade_duration = 0.5
    # Don't escape here - escape_expression will handle it
    cta_alpha = f"if(lt(t,{cta_start_time+cta_fade_duration}),(t-{cta_start_time})/{cta_fade_duration},1)"  # Fade in
    
    # Calculate CTA text Y position based on cta_position
    if cta_position == "top":
        cta_y = f"(h-text_h)/2-{int(height*0.20)}"  # Upper area
    elif cta_position == "center":
        cta_y = "(h-text_h)/2"  # Center
    else:  # bottom
        cta_y = f"(h-text_h)/2+{int(height*0.20)}"  # Lower area
    
    # Build CTA text filter - NO QUOTES, escape commas in expressions
    cta_enable_expr = escape_expression(f"between(t,{cta_start_time},{cta_end_time})")
    cta_alpha_expr = escape_expression(cta_alpha)
    cta_text_filter = (
        f"drawtext=text={cta_text_escaped}:"
        f"fontsize={cta_fontsize}:"
        f"fontcolor=white:"
        f"x=(w-text_w)/2:"
        f"y={cta_y}:"
        f"enable={cta_enable_expr}:"
        f"alpha={cta_alpha_expr}:"
        f"fontfile={font_path_escaped}"
    )
    
    # Build filter chain as array (not long string)
    filters = [
        scale_filter,
        zoom_filter,
        fps_filter
    ]
    
    # Add rotation if specified
    if rotate_filter:
        filters.append(rotate_filter)
    
    # Text overlays removed by request (no drawtext filters)
    
    filter_complex = ",".join(filters)
    
    # FFmpeg command
    # -loop 1: Loop the image to create video
    # -t {duration}: Set duration to exactly 5 seconds
    # -r {fps}: Set frame rate
    # -vf: Apply video filters
    # -c:v libx264: Use H.264 codec
    # -preset medium: Balance between speed and compression
    # -crf 23: Quality setting (lower = better quality, higher file size)
    # -pix_fmt yuv420p: Ensure compatibility
    # -an: No audio
    # -movflags +faststart: Optimize for web streaming
    
    # STABLE FFMPEG COMMAND (NO JITTER, CINEMATIC)
    # Format: -loop 1 -framerate 30 -i input -vf "zoompan=z='1+speed*on':..." -t 5
    # CRITICAL: Use linear zoom z='1+speed*on' (NO conditional, NO jitter)
    cmd = [
        get_ffmpeg_path(),
        '-y',  # Overwrite output file
        '-loop', '1',  # Loop input image (STABLE)
        '-framerate', str(fps),  # Set input framerate (prevents frame drop)
        '-i', image_path,  # Input image
        '-vf', filter_complex,  # Apply all filters
        '-t', str(duration),  # Duration: 5 seconds
        '-c:v', 'libx264',  # H.264 codec
        '-preset', 'medium',  # Encoding preset
        '-crf', '23',  # Quality (18-28 range, 23 is good balance)
        '-pix_fmt', 'yuv420p',  # Pixel format for compatibility
        '-an',  # No audio
        '-movflags', '+faststart',  # Optimize for web streaming
        output_path
    ]
    
    logger.info(f"Creating video from image: {image_path}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Resolution: {width}x{height}, FPS: {fps}, Duration: {duration}s")
    logger.info(f"Zoom: {zoom_start} → {zoom_end}")
    logger.info(f"Hook text: '{hook_text}' (0s-1.2s)")
    logger.info(f"CTA text: '{cta_text}' (3s-5s)")
    logger.info(f"Font path (original): {font_path}")
    logger.info(f"Font path (escaped): {font_path_escaped}")
    logger.debug(f"Filter complex: {filter_complex}")
    logger.debug(f"FFmpeg command: {' '.join(cmd)}")
    
    try:
        # Run FFmpeg
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60  # 60 second timeout
        )
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")
        
        # Check output file size
        output_size = os.path.getsize(output_path) / (1024 * 1024)  # Size in MB
        logger.info(f"Video created successfully: {output_path}")
        logger.info(f"File size: {output_size:.2f} MB")
        
        if output_size > 3.0:
            logger.warning(f"Video file size ({output_size:.2f} MB) exceeds 3MB target. Consider increasing CRF value.")
        
        return output_path
        
    except subprocess.TimeoutExpired:
        logger.error("FFmpeg command timed out")
        raise RuntimeError("Video generation timed out")
    except Exception as e:
        logger.error(f"Error creating video: {str(e)}")
        raise


async def create_video_from_url(
    image_url: str,
    hook_text: str = "Check This Out!",
    cta_text: str = "Shop Now",
    output_filename: Optional[str] = None,
    duration: float = 15.0,
    zoom_start: float = 1.0,
    zoom_end: float = 1.08,
    zoom_speed: float = 0.0015,
    hook_position: str = "top",
    hook_timing: Tuple[float, float] = (0.0, 1.2),
    cta_position: str = "bottom",
    cta_timing: Tuple[float, float] = (3.0, 5.0),
    pan_x: float = 0.0,
    pan_y: float = 0.0,
    pan_speed: float = 0.0,
    rotate: float = 0.0,
    focus_x: Optional[float] = None,
    focus_y: Optional[float] = None,
    zoom_expr_override: Optional[str] = None,
    x_expr_override: Optional[str] = None,
    y_expr_override: Optional[str] = None,
    apply_zoom_boost: bool = True
) -> str:
    """
    Create video from image URL.
    Downloads image, creates video, returns path to video file.
    
    Args:
        image_url: URL of the image to convert
        hook_text: Hook text for video
        cta_text: CTA text for video
        output_filename: Optional output filename (without extension)
    
    Returns:
        Path to created video file
    """
    # Create temporary directory for processing
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
            output_filename = f"video_{os.path.basename(image_url).split('.')[0]}"
        
        output_path = os.path.join(temp_dir, f"{output_filename}.mp4")
        
        # Increase zoom speed by 3x (relative to start)
        zoom_end_fast = 1.0 + (zoom_end - 1.0) * 3.0 if apply_zoom_boost else zoom_end

        # Create video with custom parameters
        create_fake_motion_video(
            image_path=image_path,
            output_path=output_path,
            hook_text=hook_text,
            cta_text=cta_text,
            duration=duration,
            zoom_start=zoom_start,
            zoom_end=zoom_end_fast,
            zoom_speed=zoom_speed,
            hook_position=hook_position,
            hook_timing=hook_timing,
            cta_position=cta_position,
            cta_timing=cta_timing,
            pan_x=pan_x,
            pan_y=pan_y,
            pan_speed=pan_speed,
            rotate=rotate,
            focus_x=focus_x,
            focus_y=focus_y,
            zoom_expr_override=zoom_expr_override,
            x_expr_override=x_expr_override,
            y_expr_override=y_expr_override
        )
        
        return output_path
        
    except Exception as e:
        logger.error(f"Error creating video from URL: {str(e)}")
        raise


# Example usage
if __name__ == "__main__":
    # Example: Create video from local image
    # create_fake_motion_video(
    #     image_path="input.jpg",
    #     output_path="output.mp4",
    #     hook_text="Amazing Product!",
    #     cta_text="Buy Now"
    # )
    
    # Example: Create video from URL (async)
    # import asyncio
    # video_path = asyncio.run(create_video_from_url(
    #     image_url="https://example.com/image.jpg",
    #     hook_text="Check This Out!",
    #     cta_text="Shop Now"
    # ))
    # print(f"Video created: {video_path}")
    pass
