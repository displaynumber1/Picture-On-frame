"""
Debug helper: Save prompt yang dikirim ke Fal.ai ke file
Untuk memudahkan analisa prompt tanpa harus scroll terminal logs
"""
import json
from datetime import datetime
from pathlib import Path

PROMPT_LOG_FILE = Path(__file__).parent / "prompt_log.json"

def save_prompt_log(request_data: dict, enhanced_prompt: str, fal_request: dict):
    """
    Save prompt yang dikirim ke Fal.ai ke file JSON untuk debugging
    
    Args:
        request_data: Data dari request (termasuk images info, image_url, dll)
        enhanced_prompt: Final prompt yang dikirim ke Fal.ai
        fal_request: Request payload yang dikirim ke Fal.ai (steps, CFG, image_url, dll)
    """
    try:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "request": {
                "has_product_images": len([img for img in (request_data.get("product_images") or []) if img]) > 0 if request_data.get("product_images") else False,
                "num_product_images": len([img for img in (request_data.get("product_images") or []) if img]) if request_data.get("product_images") else 0,
                "has_face_image": bool(request_data.get("face_image")),
                "has_background_image": bool(request_data.get("background_image")),
                "has_image_url": bool(request_data.get("image_url")),
                "image_url": request_data.get("image_url"),  # Full image_url untuk debugging
                "request_format": request_data.get("request_format", "unknown"),
                "original_prompt": request_data.get("prompt", enhanced_prompt)[:200] + "..." if len(request_data.get("prompt", enhanced_prompt)) > 200 else request_data.get("prompt", enhanced_prompt)
            },
            "enhanced_prompt": enhanced_prompt,
            "fal_request": fal_request,  # Ini sudah include image_url jika ada
            "prompt_length": len(enhanced_prompt),
            "generation_mode": "image-to-image" if fal_request.get("image_url") or fal_request.get("image_strength") else "text-to-image"
        }
        
        # Load existing logs
        if PROMPT_LOG_FILE.exists():
            with open(PROMPT_LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        else:
            logs = []
        
        # Add new log entry (keep last 10 entries)
        logs.append(log_entry)
        if len(logs) > 10:
            logs = logs[-10:]
        
        # Save logs
        with open(PROMPT_LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
        
        return log_entry
    except Exception as e:
        print(f"⚠️  Failed to save prompt log: {e}")
        return None


def get_latest_prompt_log():
    """Get latest prompt log entry"""
    try:
        if PROMPT_LOG_FILE.exists():
            with open(PROMPT_LOG_FILE, 'r', encoding='utf-8') as f:
                logs = json.load(f)
                if logs:
                    return logs[-1]
        return None
    except Exception as e:
        print(f"⚠️  Failed to load prompt log: {e}")
        return None


def clear_prompt_log():
    """Clear all prompt logs"""
    try:
        if PROMPT_LOG_FILE.exists():
            PROMPT_LOG_FILE.unlink()
            return True
        return False
    except Exception as e:
        print(f"⚠️  Failed to clear prompt log: {e}")
        return False
