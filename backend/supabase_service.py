"""
Supabase service for database operations
"""
import os
import logging
import httpx
from typing import Optional, Dict, Any, Tuple, List
from urllib.parse import quote_plus
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import Path
from io import BytesIO

logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent.parent / 'config.env'
if not env_path.exists():
    env_path = Path(__file__).parent / 'config.env'
load_dotenv(env_path)

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')  # Service role key for backend

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    logger.warning("Supabase credentials not found in environment variables")
    supabase: Optional[Client] = None
else:
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def get_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get user profile from Supabase
    
    Args:
        user_id: Supabase user ID (UUID)
    
    Returns:
        Profile dict or None if not found
    """
    if not supabase:
        raise ValueError("Supabase client not initialized")
    
    try:
        response = supabase.table("profiles").select("*").eq("user_id", user_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error getting user profile: {error_msg}", exc_info=True)
        
        # Check if it's a table not found error
        if "PGRST205" in error_msg or "could not find the table" in error_msg.lower():
            raise ValueError(
                "Tabel 'profiles' tidak ditemukan di Supabase. "
                "Silakan jalankan SQL setup di Supabase SQL Editor. "
                "Lihat file setup.sql untuk script SQL yang diperlukan."
            )
        
        # Check if it's a schema cache issue
        if "schema cache" in error_msg.lower():
            raise ValueError(
                "Schema cache Supabase perlu di-refresh. "
                "Silakan refresh schema cache di Supabase Dashboard > Database > Replication > Refresh Schema Cache, "
                "atau tunggu beberapa menit untuk cache refresh otomatis."
            )
        
        raise


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Get Supabase auth user by email (Admin API).
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise ValueError("Supabase client not initialized. Please configure SUPABASE_URL and SUPABASE_SERVICE_KEY in config.env")
    if not email:
        return None

    try:
        query_email = quote_plus(email.lower())
        url = f"{SUPABASE_URL}/auth/v1/admin/users?email={query_email}"
        headers = {
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "apikey": SUPABASE_SERVICE_KEY
        }
        response = httpx.get(url, headers=headers, timeout=10.0)
        if response.status_code != 200:
            logger.warning(f"Failed to fetch user by email: {response.status_code} - {response.text}")
            return None

        data = response.json()
        if isinstance(data, dict):
            users = data.get("users") or data.get("data") or []
        elif isinstance(data, list):
            users = data
        else:
            users = []

        return users[0] if users else None
    except Exception as e:
        logger.error(f"Error getting user by email: {str(e)}", exc_info=True)
        return None


def list_auth_users(page: int = 1, per_page: int = 20) -> Tuple[List[Dict[str, Any]], Optional[int]]:
    """
    List users via Supabase Admin API.
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise ValueError("Supabase credentials not initialized")
    try:
        url = f"{SUPABASE_URL}/auth/v1/admin/users"
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"
        }
        response = httpx.get(url, headers=headers, params={"page": page, "per_page": per_page}, timeout=15)
        if response.status_code != 200:
            logger.warning(f"Failed to list users: {response.status_code} - {response.text}")
            return [], None
        data = response.json()
        if isinstance(data, dict):
            users = data.get("users") or data.get("data") or []
            total = data.get("total")
        elif isinstance(data, list):
            users = data
            total = None
        else:
            users = []
            total = None
        return users, total if isinstance(total, int) else None
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}", exc_info=True)
        return [], None


def get_user_id_by_email(email: str) -> Optional[str]:
    """
    Resolve Supabase user_id from email using Admin API.
    """
    user = get_user_by_email(email)
    if not user:
        return None
    user_id = user.get("id")
    return user_id if isinstance(user_id, str) else None


def upsert_user_role(user_id: str, role_user: str) -> Optional[Dict[str, Any]]:
    """
    Upsert role_user in profiles table for a given user_id.
    """
    if not supabase:
        raise ValueError("Supabase client not initialized")
    if not user_id:
        return None

    try:
        payload = {"user_id": user_id, "role_user": role_user}
        response = supabase.table("profiles").upsert(payload, on_conflict="user_id").execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"Error upserting user role: {str(e)}", exc_info=True)
        raise


def ensure_admin_roles_by_email(emails: List[str]) -> int:
    """
    Legacy: Ensure role_user=admin for a list of emails. Returns count of updated profiles.
    Prefer using ensure_admin_users_by_email to avoid changing auth-facing roles.
    """
    updated = 0
    for email in emails:
        user_id = get_user_id_by_email(email)
        if not user_id:
            logger.warning(f"Bootstrap admin skipped: user not found for email {email}")
            continue
        try:
            upsert_user_role(user_id, "admin")
            updated += 1
        except Exception as e:
            logger.error(f"Bootstrap admin failed for {email}: {str(e)}", exc_info=True)
    return updated


def ensure_admin_users_by_email(emails: List[str]) -> int:
    """
    Ensure user_id exists in admin_users table for a list of emails.
    Returns count of upserted rows.
    """
    if not supabase:
        raise ValueError("Supabase client not initialized")
    updated = 0
    for email in emails:
        user_id = get_user_id_by_email(email)
        if not user_id:
            logger.warning(f"Bootstrap admin skipped: user not found for email {email}")
            continue
        try:
            response = supabase.table("admin_users").upsert({"user_id": user_id}, on_conflict="user_id").execute()
            if response.data:
                updated += 1
            supabase.table("profiles").update({"is_admin": True}).eq("user_id", user_id).execute()
        except Exception as e:
            logger.error(f"Bootstrap admin_users failed for {email}: {str(e)}", exc_info=True)
    return updated


def is_admin_user(user_id: str) -> bool:
    """
    Check if user_id is listed in admin_users table.
    """
    if not supabase:
        raise ValueError("Supabase client not initialized")
    if not user_id:
        return False
    try:
        response = supabase.table("admin_users").select("user_id").eq("user_id", user_id).limit(1).execute()
        return bool(response.data)
    except Exception as e:
        logger.error(f"Error checking admin_users: {str(e)}", exc_info=True)
        return False


def update_user_quota(user_id: str, quota_change: int) -> Dict[str, Any]:
    """
    Update user's free_image_quota
    
    Args:
        user_id: Supabase user ID
        quota_change: Change in quota (negative to decrease)
    
    Returns:
        Updated profile
    """
    if not supabase:
        raise ValueError("Supabase client not initialized")
    
    try:
        # Get current profile
        profile = get_user_profile(user_id)
        if not profile:
            raise ValueError("User profile not found")
        
        new_quota = max(0, profile.get("free_image_quota", 0) + quota_change)
        
        # Update quota
        response = supabase.table("profiles").update({
            "free_image_quota": new_quota
        }).eq("user_id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        raise ValueError("Failed to update quota")
    except Exception as e:
        logger.error(f"Error updating user quota: {str(e)}", exc_info=True)
        raise


def update_user_coins(user_id: str, coins_change: int) -> Dict[str, Any]:
    """
    Update user's coins_balance
    
    Args:
        user_id: Supabase user ID
        coins_change: Change in coins (can be positive or negative)
    
    Returns:
        Updated profile
    """
    if not supabase:
        raise ValueError("Supabase client not initialized")
    
    try:
        # Get current profile
        profile = get_user_profile(user_id)
        if not profile:
            raise ValueError("User profile not found")
        
        new_balance = max(0, profile.get("coins_balance", 0) + coins_change)
        
        # Update coins
        response = supabase.table("profiles").update({
            "coins_balance": new_balance
        }).eq("user_id", user_id).execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        raise ValueError("Failed to update coins")
    except Exception as e:
        logger.error(f"Error updating user coins: {str(e)}", exc_info=True)
        raise


def update_user_trial_remaining(user_id: str, trial_remaining: int) -> Dict[str, Any]:
    """
    Update user's trial_upload_remaining.
    """
    if not supabase:
        raise ValueError("Supabase client not initialized")
    try:
        response = supabase.table("profiles").update({
            "trial_upload_remaining": max(0, int(trial_remaining))
        }).eq("user_id", user_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        raise ValueError("Failed to update trial remaining")
    except Exception as e:
        logger.error(f"Error updating trial remaining: {str(e)}", exc_info=True)
        raise


def update_user_subscription(user_id: str, subscribed: bool) -> Dict[str, Any]:
    """
    Update user's subscribed flag.
    """
    if not supabase:
        raise ValueError("Supabase client not initialized")
    try:
        response = supabase.table("profiles").update({
            "subscribed": bool(subscribed)
        }).eq("user_id", user_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        raise ValueError("Failed to update subscription")
    except Exception as e:
        logger.error(f"Error updating subscription: {str(e)}", exc_info=True)
        raise


def update_user_admin_flag(user_id: str, is_admin: bool) -> Dict[str, Any]:
    """
    Update user's is_admin flag and keep admin_users table in sync.
    """
    if not supabase:
        raise ValueError("Supabase client not initialized")
    try:
        response = supabase.table("profiles").update({
            "is_admin": bool(is_admin)
        }).eq("user_id", user_id).execute()
        if bool(is_admin):
            supabase.table("admin_users").upsert({"user_id": user_id}, on_conflict="user_id").execute()
        else:
            supabase.table("admin_users").delete().eq("user_id", user_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        raise ValueError("Failed to update admin flag")
    except Exception as e:
        logger.error(f"Error updating admin flag: {str(e)}", exc_info=True)
        raise


def update_user_subscription_expires(user_id: str, expires_at: Optional[str]) -> Dict[str, Any]:
    """
    Update user's subscription_expires_at and subscribed_until.
    """
    if not supabase:
        raise ValueError("Supabase client not initialized")
    try:
        response = supabase.table("profiles").update({
            "subscription_expires_at": expires_at,
            "subscribed_until": expires_at
        }).eq("user_id", user_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        raise ValueError("Failed to update subscription_expires_at")
    except Exception as e:
        logger.error(f"Error updating subscription expiry: {str(e)}", exc_info=True)
        raise


def upsert_subscription_record(user_id: str, active: bool, expires_at: Optional[str]) -> None:
    """
    Upsert subscriptions table record.
    """
    if not supabase:
        raise ValueError("Supabase client not initialized")
    try:
        supabase.table("subscriptions").upsert({
            "user_id": user_id,
            "active": bool(active),
            "expires_at": expires_at
        }, on_conflict="user_id").execute()
    except Exception as e:
        logger.error(f"Error upserting subscriptions: {str(e)}", exc_info=True)


def get_profile_by_user_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Get profile by user_id using service role (admin use).
    """
    if not supabase:
        raise ValueError("Supabase client not initialized")
    try:
        response = supabase.table("profiles").select("*").eq("user_id", user_id).limit(1).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"Error getting profile by user_id: {str(e)}", exc_info=True)
        return None


def insert_midtrans_transaction_log(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Insert Midtrans transaction log into Supabase table `midtrans_transactions`.

    Returns inserted row or None if insert fails.
    """
    if not supabase:
        raise ValueError("Supabase client not initialized")

    try:
        response = supabase.table("midtrans_transactions").insert(payload).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        logger.error(f"Error inserting midtrans transaction log: {str(e)}", exc_info=True)
        raise


def verify_user_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify Supabase JWT token and get user info
    
    Args:
        token: Supabase JWT token (access_token from Supabase session)
    
    Returns:
        User info dict or None if invalid
    """
    if not supabase or not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.error("Supabase not configured. Please add SUPABASE_URL and SUPABASE_SERVICE_KEY to config.env")
        raise ValueError("Supabase client not initialized. Please configure SUPABASE_URL and SUPABASE_SERVICE_KEY in config.env")
    
    try:
        # Verify token using Supabase REST API
        # Use the user's access token to get their user info
        verify_url = f"{SUPABASE_URL}/auth/v1/user"
        headers = {
            "Authorization": f"Bearer {token}",
            "apikey": SUPABASE_SERVICE_KEY  # Use service role key for API access
        }
        
        response = httpx.get(verify_url, headers=headers, timeout=10.0)
        
        if response.status_code == 200:
            user_data = response.json()
            return {
                "id": user_data.get("id"),
                "email": user_data.get("email"),
                "user_metadata": user_data.get("user_metadata", {})
            }
        else:
            logger.warning(f"Token verification failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error verifying user token: {str(e)}", exc_info=True)
        return None


def upload_image_to_supabase_storage(
    file_content: bytes,
    file_name: str,
    bucket_name: str = "IMAGES_UPLOAD",
    user_id: Optional[str] = None,
    category: Optional[str] = None
) -> str:
    """
    Upload image file to Supabase Storage and return public URL
    
    Args:
        file_content: Image file content as bytes
        file_name: Original file name (used only to extract extension)
        bucket_name: Storage bucket name (default: "public")
        user_id: User ID for path organization (required for structured path)
        category: Image category (e.g., "face", "product", "background") - used in path structure
    
    Returns:
        Public URL of the uploaded image
    """
    if not supabase:
        raise ValueError("Supabase client not initialized")
    
    try:
        # Generate unique filename with UUID
        import uuid
        import os
        from io import BytesIO
        
        # Extract file extension from original filename
        file_ext = os.path.splitext(file_name)[1] or ".jpg"
        # Normalize extension (lowercase, remove leading dot for mapping)
        ext_lower = file_ext.lower().lstrip('.')
        
        # Generate unique filename with UUID
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        
        # Build path structure: {user_id}/{category}/{uuid}.{ext}
        # Path MUST always be unique (UUID ensures uniqueness)
        if not user_id:
            raise ValueError("user_id is required for upload path structure")
        if not category:
            raise ValueError("category is required for upload path structure")
        
        file_path = f"{user_id}/{category}/{unique_filename}"
        
        # MIME type mapping (explicit mapping for content-type)
        # .jpg and .jpeg MUST be image/jpeg
        mime_type_map = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "webp": "image/webp",
            "gif": "image/gif",
            "mp4": "video/mp4",  # Support for video files
            "mov": "video/quicktime",
            "webm": "video/webm"
        }
        # Default based on category: videos -> video/mp4, images -> image/jpeg
        if category == "videos":
            default_content_type = "video/mp4"
        else:
            default_content_type = "image/jpeg"
        content_type = mime_type_map.get(ext_lower, default_content_type)
        
        # Ensure file_content is bytes (not BytesIO)
        # If file_content is already bytes, use it directly
        # If it's BytesIO, convert to bytes using .getvalue()
        input_type = type(file_content).__name__
        if isinstance(file_content, BytesIO):
            # Convert BytesIO to bytes
            file_content_bytes = file_content.getvalue()
            logger.debug(f"   Converted BytesIO to bytes: {len(file_content_bytes)} bytes")
        elif isinstance(file_content, bytes):
            # Already bytes, use directly
            file_content_bytes = file_content
        else:
            # Try to convert to bytes
            try:
                file_content_bytes = bytes(file_content)
            except Exception as e:
                raise ValueError(f"file_content must be bytes or BytesIO, got {input_type}: {str(e)}")
        
        # Log file details before upload
        file_size_bytes = len(file_content_bytes)
        file_size_mb = file_size_bytes / (1024 * 1024)
        logger.info(f"📤 Uploading image to Supabase Storage:")
        logger.info(f"   Bucket: {bucket_name}")
        logger.info(f"   Path: {file_path}")
        logger.info(f"   File size: {file_size_bytes} bytes ({file_size_mb:.2f} MB)")
        logger.info(f"   File extension: {file_ext}")
        logger.info(f"   Content-Type: {content_type}")
        logger.info(f"   UUID: {unique_filename}")
        logger.info(f"   Input type: {input_type} → bytes")
        
        # Upload file to Supabase Storage (upsert=False as BOOLEAN to prevent overwriting)
        # Supabase Storage requires bytes, not BytesIO
        try:
            response = supabase.storage.from_(bucket_name).upload(
                path=file_path,
                file=file_content_bytes,  # Use bytes, not BytesIO
                file_options={
                    "content-type": content_type,
                    "upsert": False  # BOOLEAN, not string - do not overwrite if exists (UUID ensures uniqueness)
                }
            )
            
            # Log Supabase response
            logger.info(f"   Supabase upload response: {response}")
            logger.debug(f"   Response type: {type(response)}")
            logger.debug(f"   Response content: {str(response)[:500]}")
            
        except Exception as upload_error:
            error_msg = str(upload_error)
            logger.error(f"❌ Supabase upload failed:")
            logger.error(f"   Bucket: {bucket_name}")
            logger.error(f"   Path: {file_path}")
            logger.error(f"   File size: {file_size_bytes} bytes")
            logger.error(f"   Content-Type: {content_type}")
            logger.error(f"   Error: {error_msg}")
            logger.error(f"   Error type: {type(upload_error).__name__}")
            logger.error(f"   File content type: {type(file_content_bytes).__name__}")
            logger.error(f"   Input type: {input_type}")
            # Re-raise to be caught by outer exception handler
            raise
        
        # Get public URL - Supabase storage.get_public_url returns string directly
        try:
            public_url = supabase.storage.from_(bucket_name).get_public_url(file_path)
        except Exception as url_error:
            logger.error(f"❌ Failed to get public URL: {str(url_error)}")
            raise ValueError(f"Failed to get public URL after upload: {str(url_error)}")
        
        logger.info(f"✅ Image uploaded successfully to Supabase Storage")
        logger.info(f"   Public URL: {public_url}")
        logger.info(f"   File path: {file_path}")
        logger.info(f"   File size: {file_size_bytes} bytes ({file_size_mb:.2f} MB)")
        logger.info(f"   Content-Type: {content_type}")
        
        return public_url
        
    except ValueError:
        # Re-raise ValueError as-is (already formatted error message)
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ Error uploading image to Supabase Storage:")
        logger.error(f"   Error: {error_msg}")
        logger.error(f"   Error type: {type(e).__name__}")
        logger.error(f"   Bucket: {bucket_name}")
        logger.error(f"   File size: {len(file_content)} bytes")
        logger.error(f"   Full traceback:", exc_info=True)
        
        # Raise exception to stop process
        raise ValueError(f"Failed to upload image to Supabase Storage: {error_msg}")


def compress_image_if_needed(image_bytes: bytes, max_size_mb: float = 1.0, quality: int = 85) -> Tuple[bytes, str]:
    """
    Compress image if size exceeds max_size_mb (default: 1MB)
    
    Args:
        image_bytes: Original image bytes
        max_size_mb: Maximum file size in MB (default: 1.0)
        quality: JPEG quality (1-100, default: 85)
    
    Returns:
        Tuple of (compressed_image_bytes, file_extension)
    """
    try:
        from PIL import Image
        
        max_size_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes
        original_size = len(image_bytes)
        
        # If image is already under limit, return as-is
        if original_size <= max_size_bytes:
            logger.debug(f"   Image size {original_size} bytes ({original_size / (1024*1024):.2f} MB) is under limit, no compression needed")
            # Determine extension from image format
            try:
                img = Image.open(BytesIO(image_bytes))
                format_lower = img.format.lower() if img.format else 'jpeg'
                ext_map = {'jpeg': '.jpg', 'jpg': '.jpg', 'png': '.png', 'webp': '.webp', 'gif': '.gif'}
                ext = ext_map.get(format_lower, '.jpg')
                return image_bytes, ext
            except:
                return image_bytes, '.jpg'
        
        logger.info(f"   📦 Image size {original_size} bytes ({original_size / (1024*1024):.2f} MB) exceeds {max_size_mb}MB, compressing...")
        
        # Open image from bytes
        img = Image.open(BytesIO(image_bytes))
        
        # Convert RGBA to RGB if needed (for JPEG)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Create white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Calculate target quality to get under max_size
        # Start with specified quality and reduce if needed
        current_quality = quality
        output = BytesIO()
        ext = '.jpg'  # Always use JPEG for compression
        
        # Try compressing with decreasing quality until under limit
        for attempt in range(5):  # Max 5 attempts
            output.seek(0)
            output.truncate(0)
            img.save(output, format='JPEG', quality=current_quality, optimize=True)
            compressed_size = len(output.getvalue())
            
            if compressed_size <= max_size_bytes:
                logger.info(f"   ✅ Compressed to {compressed_size} bytes ({compressed_size / (1024*1024):.2f} MB) with quality {current_quality}")
                return output.getvalue(), ext
            
            # Reduce quality for next attempt
            current_quality = max(50, current_quality - 10)  # Don't go below 50
        
        # If still too large, resize image
        if compressed_size > max_size_bytes:
            logger.info(f"   ⚠️ Still too large after quality reduction, resizing image...")
            # Calculate resize factor (aim for ~80% of max size)
            resize_factor = (max_size_bytes * 0.8 / compressed_size) ** 0.5
            new_width = int(img.width * resize_factor)
            new_height = int(img.height * resize_factor)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Try saving again with reduced quality
            output.seek(0)
            output.truncate(0)
            img.save(output, format='JPEG', quality=current_quality, optimize=True)
            compressed_size = len(output.getvalue())
            logger.info(f"   ✅ Compressed and resized to {compressed_size} bytes ({compressed_size / (1024*1024):.2f} MB)")
        
        return output.getvalue(), ext
        
    except ImportError:
        logger.warning("PIL/Pillow not installed, cannot compress images. Install with: pip install Pillow")
        # Return original if PIL not available
        return image_bytes, '.jpg'
    except Exception as e:
        logger.error(f"Error compressing image: {str(e)}", exc_info=True)
        # Return original on error
        return image_bytes, '.jpg'


def convert_base64_to_image_bytes(base64_str: str, compress_if_over_1mb: bool = True):
    # Returns (bytes, str) - tuple of image bytes and file extension
    """
    Convert base64 string (with or without data URL prefix) to image bytes
    Optionally compress if over 1MB
    
    Args:
        base64_str: Base64 string or data URL (e.g., "data:image/jpeg;base64,/9j/4AAQ...")
        compress_if_over_1mb: Whether to compress image if over 1MB (default: True)
    
    Returns:
        Tuple of (image_bytes, file_extension)
    """
    import base64 as b64
    
    try:
        # Extract pure base64 from data URL if needed
        if ',' in base64_str:
            # Data URL format: "data:image/jpeg;base64,/9j/4AAQ..."
            header, base64_data = base64_str.split(',', 1)
            # Extract mime type to determine extension
            if 'image/jpeg' in header or 'image/jpg' in header:
                ext = '.jpg'
            elif 'image/png' in header:
                ext = '.png'
            elif 'image/webp' in header:
                ext = '.webp'
            else:
                ext = '.jpg'  # Default
        else:
            base64_data = base64_str
            ext = '.jpg'  # Default
        
        # Decode base64 to bytes
        image_bytes = b64.b64decode(base64_data)
        
        # Compress if needed
        if compress_if_over_1mb:
            image_bytes, ext = compress_image_if_needed(image_bytes, max_size_mb=1.0)
        
        return image_bytes, ext
        
    except Exception as e:
        logger.error(f"Error converting base64 to image bytes: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to convert base64 to image bytes: {str(e)}")

