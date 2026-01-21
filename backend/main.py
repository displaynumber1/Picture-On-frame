from __future__ import annotations

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Header, Response, Form, Request, WebSocket, WebSocketDisconnect, BackgroundTasks  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from fastapi.responses import JSONResponse, FileResponse  # type: ignore
from pydantic import BaseModel  # type: ignore
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import random
import time
import re
import csv
import hashlib
import math
import base64
import os
import sqlite3
import json
from pathlib import Path
import tempfile
import subprocess
from dotenv import load_dotenv  # type: ignore
from google import genai  # type: ignore
from gemini_service import generate_product_photo, generate_product_video
import logging
import httpx  # type: ignore
from fal_service import generate_images as fal_generate_images, generate_video as fal_generate_video, generate_kling_image_to_video as fal_generate_kling_video
from video_service import create_video_from_url, check_ffmpeg_available, get_ffmpeg_path
from video_config import get_video_presets, get_video_preset
from human_video_service import check_ffmpeg_available as check_ffmpeg_available_human
from face_detection import has_human_face
from motion_logic import (
    get_motion_variations,
    detect_product_region,
    detect_focus_y_from_edges,
    compute_category_bias_y
)
from supabase_service import (
    get_user_profile, 
    get_user_id_by_email,
    ensure_admin_roles_by_email,
    update_user_quota, 
    update_user_coins, 
    verify_user_token,
    upload_image_to_supabase_storage,
    convert_base64_to_image_bytes,
    insert_midtrans_transaction_log
)
from image_preprocessor import preprocess_image

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables

# Try to load from parent directory first, then current directory
env_path = Path(__file__).parent.parent / 'config.env'
if not env_path.exists():
    env_path = Path(__file__).parent / 'config.env'
load_dotenv(env_path)

# Bootstrap admin configuration (safe, environment-driven)
def _parse_bootstrap_admin_emails() -> List[str]:
    raw = os.getenv("BOOTSTRAP_ADMIN_EMAILS", "")
    if not raw:
        return []
    normalized = raw.replace(";", ",")
    emails = [email.strip().lower() for email in normalized.split(",") if email.strip()]
    return list(dict.fromkeys(emails))


BOOTSTRAP_ADMIN_ENABLED = os.getenv("BOOTSTRAP_ADMIN_ENABLED", "false").lower() in {"1", "true", "yes", "on"}
BOOTSTRAP_ADMIN_EMAILS = _parse_bootstrap_admin_emails()

# Authentication dependency
async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Verify Supabase JWT token and return user info"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    try:
        # Extract token from "Bearer <token>" format
        token = authorization.replace("Bearer ", "").strip()
        user = verify_user_token(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        user_id = user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found in token")
        # Enforce profile existence (whitelist via profiles table)
        profile = get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=403, detail="Email kamu belum terdaftar di sistem kami")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}", exc_info=True)
        raise HTTPException(status_code=401, detail="Token verification failed")


async def get_current_user_raw(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Verify Supabase JWT token without profile enforcement (debug only)"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    try:
        token = authorization.replace("Bearer ", "").strip()
        user = verify_user_token(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}", exc_info=True)
        raise HTTPException(status_code=401, detail="Token verification failed")


async def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=403, detail="Admin access required")
    role = get_user_role_from_profile(user_id) or "user"
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Initialize Gemini API Client (optional)
# Note: Fal.ai is now the primary image generation service for images/video
api_key = os.getenv('GEMINI_API_KEY')
client = None
if api_key:
    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        logger.warning(f"Failed to initialize Gemini client: {e}. Some endpoints may not work without GEMINI_API_KEY.")
else:
    logger.info("GEMINI_API_KEY not found. LLM scoring will fallback to heuristic mode.")

# Database path
DB_PATH = Path(__file__).parent / 'premium_studio.db'
AUTPOST_TEMP_DIR = Path(__file__).parent / 'temp_videos'
AUTPOST_TEMP_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_AUTPOST_THRESHOLD = float(os.getenv("AUTPOST_SCORE_THRESHOLD", "8.0"))
AUTPOST_LLM_MODEL = os.getenv("AUTPOST_LLM_MODEL", "gemini-1.5-flash")
AUTPOST_LLM_PROVIDER = os.getenv("AUTPOST_LLM_PROVIDER", "gemini")  # gemini | ollama | openai_compat
AUTPOST_LLM_BASE_URL = os.getenv("AUTPOST_LLM_BASE_URL", "http://127.0.0.1:11434")
AUTPOST_SCORE_CACHE_TTL = int(os.getenv("AUTPOST_SCORE_CACHE_TTL", "900"))  # seconds
AUTPOST_RATE_LIMIT_PER_MIN = int(os.getenv("AUTPOST_RATE_LIMIT_PER_MIN", "10"))
AUTPOST_MAX_TEMP_AGE_HOURS = int(os.getenv("AUTPOST_MAX_TEMP_AGE_HOURS", "24"))
AUTPOST_SCENE_PROVIDER = os.getenv("AUTPOST_SCENE_PROVIDER", "none").lower()  # none | openscenesense | http
AUTPOST_SCENE_ENDPOINT = os.getenv("AUTPOST_SCENE_ENDPOINT", "").strip()
AUTPOST_SCENE_TIMEOUT = float(os.getenv("AUTPOST_SCENE_TIMEOUT", "8"))
AUTPOST_SCENE_LIGHT_MODE = os.getenv("AUTPOST_SCENE_LIGHT_MODE", "1").lower() in {"1", "true", "yes", "on"}
AUTPOST_SCENE_MAX_MB = float(os.getenv("AUTPOST_SCENE_MAX_MB", "20"))
AUTPOST_SCENE_SAMPLE_SECONDS = float(os.getenv("AUTPOST_SCENE_SAMPLE_SECONDS", "4"))
AUTPOST_SCENE_SAMPLE_FPS = int(os.getenv("AUTPOST_SCENE_SAMPLE_FPS", "6"))
AUTPOST_SCENE_SAMPLE_SCALE = int(os.getenv("AUTPOST_SCENE_SAMPLE_SCALE", "480"))
AUTPOST_VOICE_SAMPLE_SECONDS = float(os.getenv("AUTPOST_VOICE_SAMPLE_SECONDS", "6"))
AUTPOST_VOICE_VAD_MODE = int(os.getenv("AUTPOST_VOICE_VAD_MODE", "2"))  # 0-3, higher is more aggressive
AUTPOST_TRENDS_CSV = Path(__file__).parent / "trends.csv"
AUTPOST_EMBEDDING_PROVIDER = os.getenv("AUTPOST_EMBEDDING_PROVIDER", "ollama")  # ollama | openai_compat
AUTPOST_EMBEDDING_MODEL = os.getenv("AUTPOST_EMBEDDING_MODEL", "nomic-embed-text")
AUTPOST_QDRANT_URL = os.getenv("AUTPOST_QDRANT_URL", "")
AUTPOST_QDRANT_API_KEY = os.getenv("AUTPOST_QDRANT_API_KEY", "")
AUTPOST_QDRANT_COLLECTION = os.getenv("AUTPOST_QDRANT_COLLECTION", "autopost_trends")
AUTPOST_HASHTAG_REGEX = os.getenv("AUTPOST_HASHTAG_REGEX", r"^#[a-z0-9_]{2,40}$")
AUTPOST_CATEGORY_WHITELIST = os.getenv(
    "AUTPOST_CATEGORY_WHITELIST",
    "fashion,apparel,shoes,bag,beauty,accessories,general,all"
)

# Helper function to extract base64 and mime_type from data URL
def extract_base64_and_mime_type(data_url_or_base64: str, default_mime: str = "image/png") -> tuple[str, str]:
    """
    Extract pure base64 string and mime_type from data URL or base64 string.
    
    Args:
        data_url_or_base64: Can be:
            - Data URL format: "data:image/jpeg;base64,/9j/4AAQ..."
            - Pure base64: "/9j/4AAQ..."
        default_mime: Default mime type if not found in data URL
    
    Returns:
        tuple: (pure_base64_string, mime_type)
    """
    if not data_url_or_base64:
        return "", default_mime
    
    # Check if it's a data URL
    if ',' in data_url_or_base64:
        # Format: "data:image/jpeg;base64,/9j/4AAQ..."
        parts = data_url_or_base64.split(',', 1)
        header = parts[0]  # "data:image/jpeg;base64"
        base64_data = parts[1]  # Pure base64 string
        
        # Extract mime_type from header
        if 'data:' in header:
            mime_part = header.split('data:')[1]
            if ';' in mime_part:
                mime_type = mime_part.split(';')[0].strip()
            else:
                mime_type = mime_part.strip()
            
            # Validate mime_type
            if mime_type and mime_type.startswith('image/'):
                return base64_data, mime_type
        
        # If mime_type extraction failed, use default
        return base64_data, default_mime
    else:
        # Pure base64 string, use default mime_type
        return data_url_or_base64, default_mime

# Database initialization function
def init_database():
    """Initialize database and create tables if they don't exist"""
    from datetime import datetime
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create authorized_users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS authorized_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                role TEXT DEFAULT 'user' NOT NULL,
                created_at TEXT NOT NULL
            )
        ''')

        # Create autopost_videos table for dashboard queue
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS autopost_videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                title TEXT,
                caption TEXT,
                hook_text TEXT,
                cta_text TEXT,
                hashtags TEXT,
                category TEXT,
                status TEXT NOT NULL,
                score REAL,
                score_details TEXT,
                threshold REAL,
                next_check_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                error TEXT
            )
        ''')

        # Create autopost_metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS autopost_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                video_id INTEGER NOT NULL,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                shares INTEGER DEFAULT 0,
                avg_watch_time REAL,
                retention_curve TEXT,
                posted_at TEXT,
                created_at TEXT NOT NULL
            )
        ''')

        # Create autopost_competitors table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS autopost_competitors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT,
                notes TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        # Bootstrap authorized admins from environment (optional)
        if BOOTSTRAP_ADMIN_ENABLED and BOOTSTRAP_ADMIN_EMAILS:
            for admin_email in BOOTSTRAP_ADMIN_EMAILS:
                cursor.execute('SELECT id FROM authorized_users WHERE email = ?', (admin_email,))
                if cursor.fetchone() is None:
                    cursor.execute('''
                        INSERT INTO authorized_users (email, role, created_at)
                        VALUES (?, ?, ?)
                    ''', (admin_email, 'admin', datetime.now().isoformat()))
                    logger.info(f"Bootstrap admin '{admin_email}' added to authorized_users")
                else:
                    logger.info(f"Bootstrap admin '{admin_email}' already exists in authorized_users")
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at: {DB_PATH}")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}", exc_info=True)
        raise

def bootstrap_admin_profiles() -> None:
    """Ensure admin roles in Supabase profiles for bootstrap emails"""
    if not BOOTSTRAP_ADMIN_ENABLED or not BOOTSTRAP_ADMIN_EMAILS:
        return
    try:
        updated = ensure_admin_roles_by_email(BOOTSTRAP_ADMIN_EMAILS)
        logger.info(f"Bootstrap admin profiles updated: {updated}")
    except Exception as e:
        logger.warning(f"Bootstrap admin profiles skipped: {str(e)}")


# Initialize database on startup
init_database()
bootstrap_admin_profiles()

# Database helper functions
def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def is_email_authorized(email: str) -> bool:
    """Check if email is in authorized_users table"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM authorized_users WHERE email = ?', (email,))
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except sqlite3.OperationalError as e:
        if "no such table" in str(e).lower():
            logger.error("Database table not found. Reinitializing database...")
            init_database()
            # Retry after initialization
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM authorized_users WHERE email = ?', (email,))
            result = cursor.fetchone()
            conn.close()
            return result is not None
        raise

def get_user_role(email: str) -> Optional[str]:
    """Get user role from database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT role FROM authorized_users WHERE email = ?', (email,))
        result = cursor.fetchone()
        conn.close()
        return result['role'] if result else None
    except sqlite3.OperationalError as e:
        if "no such table" in str(e).lower():
            logger.error("Database table not found. Reinitializing database...")
            init_database()
            # Retry after initialization
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT role FROM authorized_users WHERE email = ?', (email,))
            result = cursor.fetchone()
            conn.close()
            return result['role'] if result else None
        raise


def get_user_role_from_profile(user_id: str) -> Optional[str]:
    """Get user role from Supabase profile"""
    try:
        profile = get_user_profile(user_id)
        if not profile:
            return None
        role = profile.get("role_user") or profile.get("role")
        return role if isinstance(role, str) else None
    except Exception as e:
        logger.error(f"Error getting profile role: {str(e)}", exc_info=True)
        return None


def get_user_role_from_email(email: str) -> Optional[str]:
    """Resolve role_user from Supabase profile using email"""
    try:
        user_id = get_user_id_by_email(email)
        if not user_id:
            return None
        return get_user_role_from_profile(user_id)
    except Exception as e:
        logger.error(f"Error getting role from email: {str(e)}", exc_info=True)
        return None



def add_authorized_user(email: str, role: str = 'user') -> bool:
    """Add new user to authorized_users table"""
    from datetime import datetime
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO authorized_users (email, role, created_at)
            VALUES (?, ?, ?)
        ''', (email, role, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False


def _now_iso() -> str:
    return datetime.now().isoformat()


def _schedule_next_check(minutes_min: int = 15, minutes_max: int = 30) -> str:
    minutes = random.randint(minutes_min, minutes_max)
    return (datetime.now() + timedelta(minutes=minutes)).isoformat()


def _enforce_rate_limit(user_id: str) -> None:
    now = datetime.now().timestamp()
    window_start = now - 60
    history = AUTPOST_RATE_LIMIT.get(user_id, [])
    history = [ts for ts in history if ts >= window_start]
    if len(history) >= AUTPOST_RATE_LIMIT_PER_MIN:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
    history.append(now)
    AUTPOST_RATE_LIMIT[user_id] = history


def _cleanup_old_temp_videos() -> int:
    cutoff = datetime.now() - timedelta(hours=AUTPOST_MAX_TEMP_AGE_HOURS)
    if not AUTPOST_TEMP_DIR.exists():
        return 0
    removed = 0
    for file_path in AUTPOST_TEMP_DIR.glob("*"):
        try:
            if file_path.is_file() and datetime.fromtimestamp(file_path.stat().st_mtime) < cutoff:
                file_path.unlink()
                removed += 1
        except Exception:
            continue
    return removed


def _get_category_whitelist() -> List[str]:
    return [c.strip().lower() for c in AUTPOST_CATEGORY_WHITELIST.split(",") if c.strip()]


def _category_label_map() -> Dict[str, str]:
    return {
        "fashion": "Fashion",
        "apparel": "Apparel",
        "shoes": "Sandal",
        "footwear": "Sandal",
        "sandal": "Sandal",
        "sepatu": "Sandal",
        "bag": "Bag",
        "beauty": "Beauty",
        "accessories": "Accessories",
        "general": "General",
        "all": "All"
    }


def _get_engagement_templates(category: Optional[str]) -> Dict[str, List[str]]:
    category_key = (category or "general").strip().lower()
    label = _category_label_map().get(category_key, category_key.title())
    trend_list, _, _ = _get_trend_context("", "", "", "", "", category_key)
    trend_tags = " ".join(trend_list[:3]) if trend_list else "#fyp #viral"

    hooks = [
        f"{label} wajib punya! Banyak yang salah pilih.",
        f"{label} terbaik minggu ini — lihat bedanya!",
        f"Stop scroll! {label} ini lagi rame banget.",
        f"Cuma 5 detik, kamu bakal paham {label} ini.",
        f"Tips {label} biar kelihatan lebih mahal."
    ]
    ctas = [
        "Komen 'MAU' biar aku kirim detailnya.",
        "Tag temanmu yang butuh ini.",
        "Save dulu biar nggak lupa.",
        "Follow untuk update stok & promo.",
        "Share ke bestie kamu."
    ]
    captions = [
        f"{label} yang bener bikin look naik level. {trend_tags}",
        f"Lagi diskon? Cek sampe habis. {trend_tags}",
        f"Pilihan aman buat harian. {trend_tags}",
        f"Detailnya halus banget, worth it. {trend_tags}",
        f"Kalau kamu suka simple tapi elegan, ini wajib. {trend_tags}"
    ]
    return {"hooks": hooks, "ctas": ctas, "captions": captions, "hashtags": trend_list}


def _validate_trend_row(row: Dict[str, Any], row_num: int) -> Optional[str]:
    hashtag = (row.get("hashtag") or "").strip()
    category = (row.get("category") or "").strip().lower()
    weight = row.get("weight")

    if not hashtag:
        return f"Row {row_num}: hashtag is required"
    if not re.match(AUTPOST_HASHTAG_REGEX, hashtag.lower()):
        return f"Row {row_num}: invalid hashtag format"

    whitelist = _get_category_whitelist()
    if category and category not in whitelist:
        return f"Row {row_num}: category not allowed"

    if weight is not None and str(weight).strip() != "":
        try:
            float(weight)
        except Exception:
            return f"Row {row_num}: weight must be a number"
    return None


def _refresh_trends_index() -> int:
    rows = _load_trends_csv()
    prepared_rows: List[Dict[str, Any]] = []
    texts: List[str] = []
    for row in rows:
        prepared = dict(row)
        text = f"{row.get('hashtag', '')} {row.get('category', '')}".strip()
        prepared_rows.append(prepared)
        texts.append(text)
    try:
        vectors = _embed_texts(texts) if texts else []
    except Exception as e:
        logger.warning(f"Failed to embed trends texts (LLM server unreachable?): {e}")
        vectors = []
    AUTPOST_TRENDS_INDEX["rows"] = prepared_rows
    AUTPOST_TRENDS_INDEX["vectors"] = vectors
    if vectors and AUTPOST_QDRANT_URL:
        _upsert_qdrant_trends(prepared_rows, vectors)
    return len(prepared_rows)




def _cosine_vec(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def _embed_texts(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    if AUTPOST_EMBEDDING_PROVIDER == "ollama":
        vectors: List[List[float]] = []
        for text in texts:
            r = httpx.post(
                f"{AUTPOST_LLM_BASE_URL}/api/embeddings",
                json={"model": AUTPOST_EMBEDDING_MODEL, "prompt": text},
                timeout=30.0
            )
            r.raise_for_status()
            vectors.append(r.json().get("embedding", []))
        return vectors
    if AUTPOST_EMBEDDING_PROVIDER == "openai_compat":
        response = httpx.post(
            f"{AUTPOST_LLM_BASE_URL}/v1/embeddings",
            json={"model": AUTPOST_EMBEDDING_MODEL, "input": texts},
            timeout=30.0
        )
        response.raise_for_status()
        data = response.json()
        return [d.get("embedding", []) for d in data.get("data", [])]
    return []


def _search_trends(query_text: str, category: Optional[str], limit: int = 8) -> List[Dict[str, Any]]:
    rows = AUTPOST_TRENDS_INDEX.get("rows", [])
    vectors = AUTPOST_TRENDS_INDEX.get("vectors", [])
    if AUTPOST_QDRANT_URL:
        results = _search_qdrant_trends(query_text, category, limit)
        if results:
            return results
    if not rows or not vectors:
        rows = _load_trends_csv()
        return rows[:limit]

    category_key = (category or "").strip().lower()
    query_vecs = _embed_texts([f"{query_text} {category_key}".strip()])
    if not query_vecs or not query_vecs[0]:
        return rows[:limit]
    query_vec = query_vecs[0]
    scored: List[Dict[str, Any]] = []
    for idx, row in enumerate(rows):
        score = _cosine_vec(query_vec, vectors[idx]) if idx < len(vectors) else 0.0
        if row.get("category") == category_key:
            score += 0.05
        elif row.get("category") in ("", "general", "all"):
            score += 0.02
        scored.append({
            "hashtag": row.get("hashtag"),
            "category": row.get("category"),
            "score": score,
            "weight": row.get("weight", 1.0)
        })
    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:limit]


def _qdrant_headers() -> Dict[str, str]:
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if AUTPOST_QDRANT_API_KEY:
        headers["api-key"] = AUTPOST_QDRANT_API_KEY
    return headers


def _ensure_qdrant_collection(vector_size: int) -> None:
    try:
        response = httpx.get(
            f"{AUTPOST_QDRANT_URL}/collections/{AUTPOST_QDRANT_COLLECTION}",
            headers=_qdrant_headers(),
            timeout=10.0
        )
        if response.status_code == 200:
            return
    except Exception:
        pass

    httpx.put(
        f"{AUTPOST_QDRANT_URL}/collections/{AUTPOST_QDRANT_COLLECTION}",
        headers=_qdrant_headers(),
        json={"vectors": {"size": vector_size, "distance": "Cosine"}},
        timeout=20.0
    ).raise_for_status()


def _upsert_qdrant_trends(rows: List[Dict[str, Any]], vectors: List[List[float]]) -> None:
    if not AUTPOST_QDRANT_URL or not vectors:
        return
    vector_size = len(vectors[0]) if vectors and vectors[0] else 0
    if vector_size == 0:
        return
    _ensure_qdrant_collection(vector_size)
    points = []
    for idx, row in enumerate(rows):
        if idx >= len(vectors):
            break
        points.append({
            "id": idx + 1,
            "vector": vectors[idx],
            "payload": {
                "category": row.get("category"),
                "hashtag": row.get("hashtag"),
                "weight": row.get("weight", 1.0)
            }
        })
    httpx.put(
        f"{AUTPOST_QDRANT_URL}/collections/{AUTPOST_QDRANT_COLLECTION}/points",
        headers=_qdrant_headers(),
        json={"points": points},
        timeout=30.0
    ).raise_for_status()


def _search_qdrant_trends(query_text: str, category: Optional[str], limit: int) -> List[Dict[str, Any]]:
    if not AUTPOST_QDRANT_URL:
        return []
    query_vecs = _embed_texts([query_text])
    if not query_vecs or not query_vecs[0]:
        return []
    query_vec = query_vecs[0]
    filter_obj = None
    category_key = (category or "").strip().lower()
    if category_key:
        filter_obj = {"must": [{"key": "category", "match": {"value": category_key}}]}
    response = httpx.post(
        f"{AUTPOST_QDRANT_URL}/collections/{AUTPOST_QDRANT_COLLECTION}/points/search",
        headers=_qdrant_headers(),
        json={"vector": query_vec, "limit": limit, "with_payload": True, "filter": filter_obj},
        timeout=20.0
    )
    if response.status_code != 200:
        return []
    data = response.json()
    results = data.get("result", [])
    scored = []
    for item in results:
        payload = item.get("payload") or {}
        score = float(item.get("score", 0.0))
        if payload.get("category") == category_key:
            score += 0.05
        elif payload.get("category") in ("", "general", "all"):
            score += 0.02
        scored.append({
            "hashtag": payload.get("hashtag"),
            "category": payload.get("category"),
            "score": score,
            "weight": payload.get("weight", 1.0)
        })
    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:limit]


def _qdrant_count(category: Optional[str]) -> Optional[int]:
    if not AUTPOST_QDRANT_URL:
        return None
    category_key = (category or "").strip().lower()
    filter_obj = None
    if category_key:
        filter_obj = {"must": [{"key": "category", "match": {"value": category_key}}]}
    response = httpx.post(
        f"{AUTPOST_QDRANT_URL}/collections/{AUTPOST_QDRANT_COLLECTION}/points/count",
        headers=_qdrant_headers(),
        json={"filter": filter_obj, "exact": True},
        timeout=10.0
    )
    if response.status_code != 200:
        return None
    data = response.json()
    return data.get("result", {}).get("count")


def _get_trend_context(
    title: Optional[str],
    caption: Optional[str],
    hook_text: Optional[str],
    cta_text: Optional[str],
    hashtags: Optional[str],
    category: Optional[str]
) -> Tuple[List[str], float, List[Dict[str, Any]]]:
    query = " ".join([t for t in [title, caption, hook_text, cta_text, hashtags] if t])
    results = _search_trends(query, category, limit=8)
    trend_list = [r.get("hashtag") for r in results if r.get("hashtag")]
    best_score = max([r.get("score", 0.0) for r in results], default=0.0)
    return trend_list, best_score, results


def _log_score_details(context: str, details: Dict[str, Any]) -> None:
    logger.info(
        f"[AUTPOST SCORE] {context} "
        f"score={details.get('score')} hook={details.get('hook_score')} "
        f"cta={details.get('cta_score')} trend={details.get('trend_score')} "
        f"feedback_delta={details.get('feedback_delta')} threshold={details.get('threshold')} "
        f"signals={details.get('signals')} rec={details.get('recommendation')}"
    )


def _compute_engagement_rate(views: int, likes: int, comments: int, shares: int) -> float:
    if views <= 0:
        return 0.0
    return (likes + comments + shares) / views


def _fetch_recent_performance(
    conn: sqlite3.Connection,
    user_id: str,
    limit: int = 50
) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT v.category, v.hook_text, v.cta_text, v.hashtags,
               m.views, m.likes, m.comments, m.shares
        FROM autopost_metrics m
        JOIN autopost_videos v ON v.id = m.video_id
        WHERE m.user_id = ?
        ORDER BY m.created_at DESC
        LIMIT ?
        """,
        (user_id, limit)
    ).fetchall()
    results: List[Dict[str, Any]] = []
    for row in rows:
        results.append({
            "category": row["category"],
            "hook_text": row["hook_text"],
            "cta_text": row["cta_text"],
            "hashtags": row["hashtags"] or "",
            "engagement_rate": _compute_engagement_rate(
                int(row["views"] or 0),
                int(row["likes"] or 0),
                int(row["comments"] or 0),
                int(row["shares"] or 0)
            )
        })
    return results


def _apply_feedback_loop(
    user_id: Optional[str],
    category: Optional[str],
    hook_text: Optional[str],
    cta_text: Optional[str],
    trend_tags: List[str]
) -> Dict[str, Any]:
    if not user_id:
        return {
            "overall_rate": 0.0,
            "category_rate": None,
            "trend_rate": None,
            "hook_rate": None,
            "cta_rate": None,
            "delta": 0.0,
            "reasons": []
        }
    conn = get_db_connection()
    rows = _fetch_recent_performance(conn, user_id, limit=50)
    conn.close()
    if not rows:
        return {
            "overall_rate": 0.0,
            "category_rate": None,
            "trend_rate": None,
            "hook_rate": None,
            "cta_rate": None,
            "delta": 0.0,
            "reasons": []
        }

    def _avg(values: List[float]) -> Optional[float]:
        if not values:
            return None
        return sum(values) / max(1, len(values))

    overall_rate = _avg([r["engagement_rate"] for r in rows]) or 0.0
    category_rate = _avg([
        r["engagement_rate"]
        for r in rows
        if category and (r["category"] or "").lower() == category.lower()
    ])
    hook_rate = _avg([
        r["engagement_rate"]
        for r in rows
        if hook_text and (r["hook_text"] or "").strip().lower() == hook_text.strip().lower()
    ])
    cta_rate = _avg([
        r["engagement_rate"]
        for r in rows
        if cta_text and (r["cta_text"] or "").strip().lower() == cta_text.strip().lower()
    ])
    trend_rate = None
    if trend_tags:
        trend_rate = _avg([
            r["engagement_rate"]
            for r in rows
            if any(tag in (r["hashtags"] or "") for tag in trend_tags)
        ])

    delta = 0.0
    reasons: List[str] = []
    baseline = overall_rate if overall_rate > 0 else 0.03

    if category_rate is not None:
        if category_rate > baseline * 1.15:
            delta += 0.3
            reasons.append("past engagement")
        elif category_rate < baseline * 0.85:
            delta -= 0.3
            reasons.append("past engagement")
    if trend_rate is not None:
        if trend_rate > baseline * 1.1:
            delta += 0.3
            reasons.append("trend match")
        elif trend_rate < baseline * 0.9:
            delta -= 0.2
            reasons.append("trend match")
    if hook_rate is not None and hook_rate < baseline * 0.8:
        delta -= 0.2
        reasons.append("past engagement")
    if cta_rate is not None and cta_rate < baseline * 0.8:
        delta -= 0.2
        reasons.append("past engagement")

    delta = max(-1.0, min(1.0, delta))

    return {
        "overall_rate": round(overall_rate, 4),
        "category_rate": None if category_rate is None else round(category_rate, 4),
        "trend_rate": None if trend_rate is None else round(trend_rate, 4),
        "hook_rate": None if hook_rate is None else round(hook_rate, 4),
        "cta_rate": None if cta_rate is None else round(cta_rate, 4),
        "delta": round(delta, 3),
        "reasons": sorted(set(reasons))
    }


def _adjust_threshold_with_feedback(base_threshold: float, feedback: Dict[str, Any], trend_similarity: float) -> float:
    threshold = base_threshold
    feedback_delta = float(feedback.get("delta") or 0.0)
    overall_rate = float(feedback.get("overall_rate") or 0.0)
    trend_rate = feedback.get("trend_rate")

    if feedback_delta >= 0.4:
        threshold -= 0.3
    elif feedback_delta <= -0.4:
        threshold += 0.3

    if trend_similarity >= 0.6 and trend_rate is not None and trend_rate >= max(0.01, overall_rate):
        threshold -= 0.2

    return float(max(0.0, min(10.0, threshold)))


def _normalize_metrics_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Accept JSON or TXT metrics from connector and normalize to internal schema.
    TXT format supports lines like:
      views: 1200
      likes=34
      retention: 1.0,0.8,0.6
    """
    normalized: Dict[str, Any] = {}
    if isinstance(payload, dict) and "raw_text" in payload and isinstance(payload["raw_text"], str):
        raw = payload["raw_text"]
        for line in raw.splitlines():
            if not line.strip():
                continue
            if ":" in line:
                key, value = line.split(":", 1)
            elif "=" in line:
                key, value = line.split("=", 1)
            else:
                continue
            key = key.strip().lower()
            value = value.strip()
            normalized[key] = value
    else:
        normalized.update(payload)

    def _get_int(keys: List[str]) -> int:
        for k in keys:
            if k in normalized and str(normalized[k]).strip() != "":
                try:
                    return int(float(normalized[k]))
                except Exception:
                    continue
        return 0

    def _get_float(keys: List[str]) -> Optional[float]:
        for k in keys:
            if k in normalized and str(normalized[k]).strip() != "":
                try:
                    return float(normalized[k])
                except Exception:
                    continue
        return None

    def _get_str(keys: List[str]) -> Optional[str]:
        for k in keys:
            if k in normalized and str(normalized[k]).strip() != "":
                return str(normalized[k]).strip()
        return None

    def _get_retention(keys: List[str]) -> Optional[List[float]]:
        for k in keys:
            if k in normalized and str(normalized[k]).strip() != "":
                raw = str(normalized[k])
                parts = [p.strip() for p in raw.split(",") if p.strip()]
                try:
                    return [float(p) for p in parts]
                except Exception:
                    continue
        return None

    return {
        "video_id": normalized.get("video_id") or normalized.get("videoId") or normalized.get("id"),
        "views": _get_int(["views", "view"]),
        "likes": _get_int(["likes", "like"]),
        "comments": _get_int(["comments", "comment"]),
        "shares": _get_int(["shares", "share"]),
        "avg_watch_time": _get_float(["avg_watch_time", "avgWatchTime", "watch_time"]),
        "retention_curve": _get_retention(["retention_curve", "retention", "retentionCurve"]),
        "posted_at": _get_str(["posted_at", "postedAt", "post_time", "postTime"])
    }


def _summarize_retention(curves: List[List[float]]) -> Dict[str, Any]:
    if not curves:
        return {"avg_retention": [], "dropoff_second": None}
    max_len = max(len(c) for c in curves)
    sums = [0.0] * max_len
    counts = [0] * max_len
    for curve in curves:
        for idx, val in enumerate(curve):
            sums[idx] += val
            counts[idx] += 1
    avg = [round(sums[i] / counts[i], 3) if counts[i] else 0.0 for i in range(max_len)]
    dropoff = None
    for i in range(1, len(avg)):
        if avg[i] < avg[i - 1] * 0.7:
            dropoff = i
            break
    return {"avg_retention": avg, "dropoff_second": dropoff}


def _detect_pattern_fatigue(rows: List[sqlite3.Row]) -> List[Dict[str, Any]]:
    hooks = {}
    ctas = {}
    for row in rows:
        hook = (row["hook_text"] or "").strip()
        cta = (row["cta_text"] or "").strip()
        if hook:
            hooks[hook] = hooks.get(hook, 0) + 1
        if cta:
            ctas[cta] = ctas.get(cta, 0) + 1
    alerts = []
    for hook, count in hooks.items():
        if count >= 4:
            alerts.append({"type": "hook_fatigue", "text": f"Hook dipakai {count}x: {hook[:60]}..."})
    for cta, count in ctas.items():
        if count >= 4:
            alerts.append({"type": "cta_fatigue", "text": f"CTA dipakai {count}x: {cta[:60]}..."})
    return alerts


def _trend_decay(scores: List[float]) -> Dict[str, Any]:
    if len(scores) < 6:
        return {"status": "insufficient_data", "delta": 0.0}
    mid = len(scores) // 2
    prev = sum(scores[:mid]) / max(1, mid)
    recent = sum(scores[mid:]) / max(1, len(scores) - mid)
    delta = round(recent - prev, 3)
    status = "declining" if delta < -0.5 else "stable"
    return {"status": status, "delta": delta}


def _analyze_scene_with_openscenesense(file_path: str) -> Optional[Dict[str, Any]]:
    try:
        import openscenesense  # type: ignore
    except Exception as exc:
        logger.warning(f"OpenSceneSense not available: {exc}")
        return None
    try:
        if hasattr(openscenesense, "analyze_video"):
            result = openscenesense.analyze_video(file_path)
        elif hasattr(openscenesense, "analyze"):
            result = openscenesense.analyze(file_path)
        else:
            logger.warning("OpenSceneSense API not recognized. Expected analyze_video/analyze.")
            return None
        if isinstance(result, dict):
            return result
        if hasattr(result, "to_dict"):
            return result.to_dict()
    except Exception as exc:
        logger.error(f"OpenSceneSense analysis failed: {exc}", exc_info=True)
    return None


def _get_ffprobe_path() -> str:
    ffmpeg_path = get_ffmpeg_path()
    if ffmpeg_path.lower().endswith("ffmpeg.exe"):
        return ffmpeg_path[:-9] + "ffprobe.exe"
    if ffmpeg_path.lower().endswith("ffmpeg"):
        return ffmpeg_path[:-6] + "ffprobe"
    return "ffprobe"


def _detect_audio_presence(file_path: str) -> Optional[bool]:
    try:
        ffprobe_path = _get_ffprobe_path()
        cmd = [
            ffprobe_path,
            "-v",
            "error",
            "-show_streams",
            "-of",
            "json",
            file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=6)
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout or "{}")
        streams = data.get("streams") or []
        return any(stream.get("codec_type") == "audio" for stream in streams)
    except Exception:
        return None


def _detect_voice_presence(file_path: str) -> Optional[bool]:
    try:
        import webrtcvad  # type: ignore
    except Exception:
        return None
    try:
        ffmpeg_path = get_ffmpeg_path()
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp.close()
        cmd = [
            ffmpeg_path,
            "-y",
            "-i",
            file_path,
            "-t",
            str(AUTPOST_VOICE_SAMPLE_SECONDS),
            "-ac",
            "1",
            "-ar",
            "16000",
            tmp.name
        ]
        subprocess.run(cmd, capture_output=True, check=False, timeout=10)
        if not os.path.exists(tmp.name) or os.path.getsize(tmp.name) == 0:
            return None
        with open(tmp.name, "rb") as f:
            wav = f.read()
        os.remove(tmp.name)
        if len(wav) < 44:
            return None
        pcm = wav[44:]  # skip wav header
        vad = webrtcvad.Vad(AUTPOST_VOICE_VAD_MODE)
        frame_ms = 30
        frame_bytes = int(16000 * 2 * frame_ms / 1000)
        if frame_bytes <= 0:
            return None
        total_frames = 0
        speech_frames = 0
        for i in range(0, len(pcm) - frame_bytes + 1, frame_bytes):
            frame = pcm[i:i + frame_bytes]
            total_frames += 1
            if vad.is_speech(frame, 16000):
                speech_frames += 1
        if total_frames == 0:
            return None
        speech_ratio = speech_frames / total_frames
        return speech_ratio >= 0.2
    except Exception:
        return None


def _analyze_scene_with_http(file_path: str) -> Optional[Dict[str, Any]]:
    if not AUTPOST_SCENE_ENDPOINT:
        return None
    try:
        with open(file_path, "rb") as f:
            response = httpx.post(
                AUTPOST_SCENE_ENDPOINT,
                files={"file": (Path(file_path).name, f, "video/mp4")},
                timeout=AUTPOST_SCENE_TIMEOUT
            )
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict):
            return data
    except Exception as exc:
        logger.error(f"Scene HTTP analysis failed: {exc}", exc_info=True)
    return None


def _prepare_scene_sample(file_path: str) -> Tuple[Optional[str], bool, Dict[str, Any]]:
    meta = {"sampled": False, "skipped_reason": None}
    try:
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
    except Exception:
        size_mb = 0.0
    if AUTPOST_SCENE_LIGHT_MODE:
        if not check_ffmpeg_available():
            if size_mb > AUTPOST_SCENE_MAX_MB:
                meta["skipped_reason"] = "ffmpeg_unavailable_and_file_too_large"
                return None, False, meta
            meta["skipped_reason"] = "ffmpeg_unavailable"
            return file_path, False, meta
        try:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            tmp.close()
            ffmpeg_path = get_ffmpeg_path()
            vf = f"scale='min({AUTPOST_SCENE_SAMPLE_SCALE},iw)':-2,fps={AUTPOST_SCENE_SAMPLE_FPS}"
            cmd = [
                ffmpeg_path,
                "-y",
                "-i",
                file_path,
                "-t",
                str(AUTPOST_SCENE_SAMPLE_SECONDS),
                "-vf",
                vf,
                "-an",
                tmp.name
            ]
            subprocess.run(cmd, capture_output=True, check=False, timeout=10)
            if not os.path.exists(tmp.name) or os.path.getsize(tmp.name) == 0:
                meta["skipped_reason"] = "sample_failed"
                return file_path, False, meta
            meta["sampled"] = True
            return tmp.name, True, meta
        except Exception:
            meta["skipped_reason"] = "sample_exception"
            return file_path, False, meta
    if size_mb > AUTPOST_SCENE_MAX_MB:
        meta["skipped_reason"] = "file_too_large"
        return None, False, meta
    return file_path, False, meta


def _get_scene_signals(file_path: Optional[str]) -> Optional[Dict[str, Any]]:
    if not file_path:
        return None
    audio_present = _detect_audio_presence(file_path)
    voice_present = _detect_voice_presence(file_path) if audio_present else False if audio_present is False else None
    sample_path, should_cleanup, meta = _prepare_scene_sample(file_path)
    if not sample_path:
        return {"_meta": meta, "audio_present": audio_present, "voice_present": voice_present}
    provider = AUTPOST_SCENE_PROVIDER
    try:
        if provider == "http":
            result = _analyze_scene_with_http(sample_path)
        elif provider == "openscenesense":
            result = _analyze_scene_with_openscenesense(sample_path)
        else:
            result = None
    finally:
        if should_cleanup:
            try:
                os.remove(sample_path)
            except Exception:
                pass
    if not result:
        return {"_meta": meta, "audio_present": audio_present, "voice_present": voice_present}
    result["_meta"] = meta
    result["audio_present"] = audio_present
    result["voice_present"] = voice_present
    return result


async def _async_scene_analysis(video_id: int, file_path: str, user_id: str) -> None:
    try:
        conn = get_db_connection()
        row = conn.execute("SELECT * FROM autopost_videos WHERE id = ?", (video_id,)).fetchone()
        if not row:
            return
        scene_signals = _get_scene_signals(file_path)
        details = _score_video_metadata(
            row["title"],
            row["caption"],
            row["hook_text"],
            row["cta_text"],
            row["hashtags"],
            row["category"],
            user_id,
            scene_signals
        )
        score = float(details.get("score", 0.0))
        threshold = _adjust_threshold_with_feedback(
            row["threshold"] or DEFAULT_AUTPOST_THRESHOLD,
            details.get("feedback") or {},
            float(details.get("trend_similarity") or 0.0)
        )
        details["threshold"] = threshold
        compliance_blocked = bool(details.get("compliance_blocked"))
        if compliance_blocked:
            status = "WAITING_RECHECK"
            next_check_at = _schedule_next_check()
        else:
            status = "QUEUED" if score >= threshold else "WAITING_RECHECK"
            next_check_at = None if status == "QUEUED" else _schedule_next_check()
        _update_autopost_record(
            conn,
            video_id,
            status=status,
            score=score,
            score_details=json.dumps(details),
            next_check_at=next_check_at,
            threshold=threshold
        )
        conn.commit()
        try:
            await _broadcast_autopost_event(user_id, "autopost.updated", {"id": video_id, "status": status})
        except Exception as exc:
            logger.warning(f"Broadcast autopost update failed: {exc}")
    except Exception as exc:
        logger.error(f"Async scene analysis failed for video_id={video_id}: {exc}", exc_info=True)
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _evaluate_compliance_gate(
    title: Optional[str],
    caption: Optional[str],
    hook_text: Optional[str],
    cta_text: Optional[str],
    hashtags: Optional[str],
    category: Optional[str],
    scene_signals: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    text_parts = [title or "", caption or "", hook_text or "", cta_text or "", hashtags or ""]
    combined = " ".join([p.strip() for p in text_parts if p]).lower()
    penalties: List[Dict[str, Any]] = []
    risk_score = 0.0
    scene_signals = scene_signals or {}

    promo_keywords = [
        "diskon", "promo", "gratis", "limited", "terbatas", "voucher",
        "beli sekarang", "order", "checkout", "link di bio", "klik link",
        "cod", "harga", "rp", "flash sale", "sale", "murah"
    ]
    product_keywords = [
        "produk", "barang", "detail", "material", "warna", "ukuran",
        "fungsi", "manfaat", "review", "unboxing", "tutorial", "cara pakai"
    ]

    if combined and any(k in combined for k in promo_keywords) and not any(k in combined for k in product_keywords):
        penalties.append({"type": "promo_without_context", "score": 0.35, "text": "Promo dominan tanpa konteks produk."})
        risk_score += 0.35

    total_len = len(" ".join([title or "", caption or ""]).strip())
    if total_len < 20:
        penalties.append({"type": "low_context", "score": 0.2, "text": "Judul/caption terlalu minim konteks."})
        risk_score += 0.2

    if not hook_text and not cta_text:
        penalties.append({"type": "no_hook_cta", "score": 0.15, "text": "Tidak ada hook/CTA untuk keterlibatan."})
        risk_score += 0.15

    if hashtags:
        hashtag_list = re.findall(r"#\w+", hashtags)
        if len(hashtag_list) >= 12:
            penalties.append({"type": "hashtag_spam", "score": 0.2, "text": "Hashtag terlalu banyak (terlihat spam)."})
            risk_score += 0.2

    if category and combined and category.lower() not in combined:
        penalties.append({"type": "category_mismatch", "score": 0.15, "text": "Kategori tidak terlihat relevan di teks."})
        risk_score += 0.15

    text_density = float(scene_signals.get("text_density") or 0.0)
    if text_density >= 0.5:
        penalties.append({"type": "text_overlay_high", "score": 0.45, "text": "Terlalu banyak teks di video."})
        risk_score += 0.45
    elif text_density >= 0.35:
        penalties.append({"type": "text_overlay_medium", "score": 0.3, "text": "Teks cukup dominan di video."})
        risk_score += 0.3

    static_score = float(scene_signals.get("static_score") or 0.0)
    if static_score >= 0.7:
        penalties.append({"type": "static_video", "score": 0.25, "text": "Konten terlalu statis."})
        risk_score += 0.25

    product_relevance = scene_signals.get("product_relevance")
    if product_relevance is not None:
        relevance_score = float(product_relevance)
        if relevance_score < 0.4:
            penalties.append({"type": "product_irrelevant", "score": 0.35, "text": "Produk kurang relevan di visual."})
            risk_score += 0.35

    blur_score = float(scene_signals.get("blur_score") or 0.0)
    if blur_score >= 0.6:
        penalties.append({"type": "blurry_visual", "score": 0.2, "text": "Visual terlihat buram."})
        risk_score += 0.2

    risk_score = min(1.0, round(risk_score, 3))
    blocked = risk_score >= 0.6
    return {
        "risk_score": risk_score,
        "penalties": penalties,
        "blocked": blocked,
        "summary": "Risiko pelanggaran promo/tidak relevan" if blocked else "Risiko rendah",
        "scene_signals": scene_signals
    }


def _score_video_metadata(
    title: Optional[str],
    caption: Optional[str],
    hook_text: Optional[str],
    cta_text: Optional[str],
    hashtags: Optional[str],
    category: Optional[str],
    user_id: Optional[str] = None,
    scene_signals: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """LLM scoring with cache + heuristic fallback."""
    cache_key = _build_score_cache_key(title, caption, hook_text, cta_text, hashtags, category, user_id)
    cached = _get_cached_score(cache_key)
    if cached:
        return cached

    llm_result = _score_video_with_llm(title, caption, hook_text, cta_text, hashtags, category)
    if llm_result:
        details: Dict[str, Any] = dict(llm_result)
    else:
        details = {"signals": [], "recommendation": "Perkuat hook, CTA, dan hashtag tren."}

    trend_list, trend_similarity, trend_rows = _get_trend_context(
        title, caption, hook_text, cta_text, hashtags, category
    )
    details["trend_matches"] = trend_list
    details["trend_similarity"] = round(trend_similarity, 3)

    def has_keywords(text: str, keywords: List[str]) -> bool:
        text_lower = text.lower()
        return any(k in text_lower for k in keywords)

    hook_keywords = ["diskon", "promo", "gratis", "terbatas", "viral", "trend", "baru", "limited"]
    cta_keywords = ["cek", "beli", "klik", "follow", "share", "comment", "komen", "save"]

    if llm_result:
        score = float(details.get("score", 0.0))
        hook_score = float(details.get("hook_score", 0.0))
        cta_score = float(details.get("cta_score", 0.0))
        trend_score = float(details.get("trend_score", trend_similarity * 10.0))
        details.setdefault("signals", [])
        details.setdefault("recommendation", "Perkuat hook, CTA, dan hashtag tren.")
    else:
        score = 6.0
        hook_score = 5.0
        if hook_text and len(hook_text.strip()) >= 8:
            score += 0.7
            hook_score += 2.0
            details["signals"].append("hook_present")
            if has_keywords(hook_text, hook_keywords):
                score += 0.4
                hook_score += 1.5
                details["signals"].append("hook_keywords")

        cta_score = 4.0
        if cta_text and len(cta_text.strip()) >= 5:
            score += 0.6
            cta_score += 2.0
            details["signals"].append("cta_present")
            if has_keywords(cta_text, cta_keywords):
                score += 0.4
                cta_score += 1.5
                details["signals"].append("cta_keywords")

        if caption and len(caption.strip()) >= 30:
            score += 0.4
            details["signals"].append("caption_length")

        if title and len(title.strip()) >= 10:
            score += 0.3
            details["signals"].append("title_length")

        if hashtags:
            hashtag_list = re.findall(r"#\w+", hashtags)
            if len(hashtag_list) >= 3:
                score += 0.3
                details["signals"].append("hashtags_count")
            if trend_list:
                if any(tag in hashtags for tag in trend_list):
                    score += 0.3
                    details["signals"].append("trend_hashtag_match")

        if category and category.lower() in ["fashion", "apparel", "accessories", "bag", "shoes", "footwear", "sandal", "sepatu", "beauty"]:
            score += 0.2
            details["signals"].append("category_match")

        trend_score = trend_similarity * 10.0

    feedback = _apply_feedback_loop(user_id, category, hook_text, cta_text, trend_list)
    feedback_delta = float(feedback.get("delta") or 0.0)
    if feedback_delta > 0:
        details["signals"].append("feedback_positive")
    elif feedback_delta < 0:
        details["signals"].append("feedback_negative")
    score += feedback_delta

    compliance = _evaluate_compliance_gate(title, caption, hook_text, cta_text, hashtags, category, scene_signals)
    compliance_penalty = float(compliance.get("risk_score") or 0.0) * 4.0
    if compliance.get("penalties"):
        details["signals"].append("compliance_risk")
    score -= compliance_penalty
    details["compliance"] = compliance
    details["compliance_penalty"] = round(compliance_penalty, 3)
    details["compliance_blocked"] = bool(compliance.get("blocked"))
    details["scene_signals"] = scene_signals or {}

    audio_present = (scene_signals or {}).get("audio_present")
    if audio_present is True:
        score += 0.2
        details["signals"].append("audio_present")
    elif audio_present is False:
        score -= 0.3
        details["signals"].append("audio_missing")

    voice_present = (scene_signals or {}).get("voice_present")
    if voice_present is True:
        score += 0.3
        details["signals"].append("voice_present")
    elif voice_present is False and audio_present is True:
        score -= 0.2
        details["signals"].append("voice_missing")
    score = min(10.0, max(0.0, score))
    hook_score = min(10.0, max(0.0, hook_score))
    cta_score = min(10.0, max(0.0, cta_score))
    trend_score = min(10.0, max(0.0, trend_score))
    details["score"] = score
    details["hook_score"] = hook_score
    details["cta_score"] = cta_score
    details["trend_score"] = trend_score
    details["feedback"] = feedback
    details["feedback_delta"] = feedback_delta
    if feedback.get("reasons"):
        details["feedback_reasons"] = feedback.get("reasons")
        details["feedback_summary"] = " + ".join(feedback.get("reasons"))
    _set_cached_score(cache_key, details)
    return details


def _score_video_with_llm(
    title: Optional[str],
    caption: Optional[str],
    hook_text: Optional[str],
    cta_text: Optional[str],
    hashtags: Optional[str],
    category: Optional[str]
) -> Optional[Dict[str, Any]]:
    prompt = _build_tiktok_prompt(title, caption, hook_text, cta_text, hashtags, category)
    try:
        raw = ""
        if AUTPOST_LLM_PROVIDER == "gemini":
            if not client:
                return None
            result = client.models.generate_content(
                model=AUTPOST_LLM_MODEL,
                contents=prompt
            )
            raw = (result.text or "").strip()
        elif AUTPOST_LLM_PROVIDER == "ollama":
            # Ollama local server (quantized LLaMA/Mistral)
            response = httpx.post(
                f"{AUTPOST_LLM_BASE_URL}/api/generate",
                json={
                    "model": AUTPOST_LLM_MODEL,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            raw = (data.get("response") or "").strip()
        elif AUTPOST_LLM_PROVIDER == "openai_compat":
            # OpenAI-compatible API (e.g., vLLM/llama.cpp server)
            response = httpx.post(
                f"{AUTPOST_LLM_BASE_URL}/v1/chat/completions",
                json={
                    "model": AUTPOST_LLM_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            raw = (data.get("choices", [{}])[0].get("message", {}).get("content") or "").strip()
        else:
            return None

        if not raw:
            return None
        # Extract JSON if the model wrapped it
        if "{" in raw and "}" in raw:
            raw = raw[raw.find("{"):raw.rfind("}") + 1]
        parsed = json.loads(raw)
        score = float(parsed.get("score", 0.0))
        parsed["score"] = max(0.0, min(10.0, score))
        parsed["provider"] = AUTPOST_LLM_PROVIDER
        return parsed
    except Exception as e:
        logger.warning(f"LLM scoring failed, fallback to heuristic: {e}")
        return None


def _build_score_cache_key(
    title: Optional[str],
    caption: Optional[str],
    hook_text: Optional[str],
    cta_text: Optional[str],
    hashtags: Optional[str],
    category: Optional[str],
    user_id: Optional[str] = None
) -> str:
    raw = json.dumps({
        "title": title or "",
        "caption": caption or "",
        "hook_text": hook_text or "",
        "cta_text": cta_text or "",
        "hashtags": hashtags or "",
        "category": category or "",
        "user_id": user_id or "",
        "provider": AUTPOST_LLM_PROVIDER,
        "model": AUTPOST_LLM_MODEL
    }, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def _get_cached_score(key: str) -> Optional[Dict[str, Any]]:
    cached = AUTPOST_SCORE_CACHE.get(key)
    if not cached:
        return None
    ts, payload = cached
    if (datetime.now().timestamp() - ts) > AUTPOST_SCORE_CACHE_TTL:
        AUTPOST_SCORE_CACHE.pop(key, None)
        return None
    return payload


def _set_cached_score(key: str, payload: Dict[str, Any]) -> None:
    AUTPOST_SCORE_CACHE[key] = (datetime.now().timestamp(), payload)


def _load_trends_csv() -> List[Dict[str, Any]]:
    if not AUTPOST_TRENDS_CSV.exists():
        return []
    rows: List[Dict[str, Any]] = []
    try:
        with open(AUTPOST_TRENDS_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append({
                    "category": (row.get("category") or "").strip().lower(),
                    "hashtag": (row.get("hashtag") or "").strip(),
                    "weight": float(row.get("weight") or 1.0)
                })
    except Exception as e:
        logger.warning(f"Failed to load trends CSV: {e}")
    return rows




def _select_trending_hashtags(category: Optional[str], limit: int = 8) -> List[str]:
    trend_list, _, _ = _get_trend_context("", "", "", "", "", category)
    return trend_list[:limit]


def _build_tiktok_prompt(
    title: Optional[str],
    caption: Optional[str],
    hook_text: Optional[str],
    cta_text: Optional[str],
    hashtags: Optional[str],
    category: Optional[str]
) -> str:
    trends, best_score, _ = _get_trend_context(title, caption, hook_text, cta_text, hashtags, category)
    trend_list = ", ".join(trends)
    return f"""
Anda adalah analis performa video TikTok berbahasa Indonesia. Nilai potensi engagement (view, like, follow, share).
Konteks kategori: {category or "-"}
Hashtag tren relevan (RAG): {trend_list or "-"} (trend_similarity={best_score:.2f})

Berikan output HANYA JSON valid dengan schema:
{{
  "score": number,         // 0-10 total engagement
  "hook_score": number,    // 0-10 kekuatan hook
  "cta_score": number,     // 0-10 kekuatan CTA
  "trend_score": number,   // 0-10 kesesuaian tren
  "recommendation": string,
  "signals": string[]
}}

Data:
title: {title or ""}
caption: {caption or ""}
hook_text: {hook_text or ""}
cta_text: {cta_text or ""}
hashtags: {hashtags or ""}
""".strip()


def _update_autopost_record(conn: sqlite3.Connection, record_id: int, **fields: Any) -> None:
    if not fields:
        return
    fields["updated_at"] = _now_iso()
    keys = list(fields.keys())
    values = [fields[k] for k in keys]
    set_clause = ", ".join([f"{k} = ?" for k in keys])
    conn.execute(f"UPDATE autopost_videos SET {set_clause} WHERE id = ?", (*values, record_id))


async def _broadcast_autopost_event(user_id: str, event: str, payload: Dict[str, Any]) -> None:
    connections = AUTPOST_WS_CONNECTIONS.get(user_id, [])
    if not connections:
        return
    message = {"event": event, "payload": payload}
    stale: List[WebSocket] = []
    for ws in connections:
        try:
            await ws.send_json(message)
        except Exception:
            stale.append(ws)
    if stale:
        AUTPOST_WS_CONNECTIONS[user_id] = [ws for ws in connections if ws not in stale]

app = FastAPI()
AUTPOST_WS_CONNECTIONS: Dict[str, List[WebSocket]] = {}
AUTPOST_SCORE_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
AUTPOST_RATE_LIMIT: Dict[str, List[float]] = {}
AUTPOST_TRENDS_INDEX: Dict[str, Any] = {"rows": [], "vectors": []}

# Initialize trends index on startup (after AUTPOST_TRENDS_INDEX is defined)
_refresh_trends_index()
AUTPOST_IMPORT_STATUS: Dict[str, Any] = {
    "status": "idle",
    "processed": 0,
    "total": 0,
    "valid": 0,
    "invalid": 0,
    "errors": []
}

def _get_cors_origins() -> List[str]:
    raw = os.getenv("CORS_ORIGINS", "")
    defaults = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "https://picture-on-frame.vercel.app",
        "https://picture-on-frame.onrender.com",
    ]
    if not raw:
        return defaults
    extras = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return list(dict.fromkeys(defaults + extras))


app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Pydantic models
class StudioConfig(BaseModel):
    modelType: str
    category: str
    background: str
    pose: str
    handInteraction: str
    style: str
    lighting: str
    aspectRatio: str
    angle: str
    additionalPrompt: Optional[str] = ""
    customBackgroundPrompt: Optional[str] = ""
    customPosePrompt: Optional[str] = ""
    customStylePrompt: Optional[str] = ""
    customLightingPrompt: Optional[str] = ""

class ImageDataModel(BaseModel):
    base64: str
    mimeType: str

class GenerationOptionsModel(BaseModel):
    background: str
    customBackgroundPrompt: str = ""
    pose: str
    customPosePrompt: str = ""
    style: str
    customStylePrompt: str = ""
    lighting: str
    customLightingPrompt: str = ""
    aspectRatio: str
    cameraAngle: str
    additionalPrompt: str = ""
    contentType: str
    modelType: str
    category: str
    interactionType: str
    backgroundColor: str = "#ffffff"

# Helper functions for GenerationOptionsModel
def get_current_pose_options_for_generation(options: GenerationOptionsModel) -> List[str]:
    """Get dynamic pose options based on GenerationOptionsModel"""
    if is_product_only(options.modelType):
        if is_foot_interaction(options.interactionType):
            return FOOT_INTERACTION_POSES
        category_data = DYNAMIC_POSES.get(options.category, DYNAMIC_POSES['Fashion'])
        return category_data['productOnly'] + ['Prompt Kustom']
    
    if is_animal(options.modelType):
        return ANIMAL_POSES + ['Prompt Kustom']
    
    category_data = DYNAMIC_POSES.get(options.category, DYNAMIC_POSES['Fashion'])
    return category_data['withModel'] + ['Prompt Kustom']

def get_current_background_options_for_generation(options: GenerationOptionsModel) -> List[str]:
    """Get dynamic background options based on GenerationOptionsModel"""
    if is_human_model(options.modelType):
        return BACKGROUNDS
    return [bg for bg in BACKGROUNDS if bg != 'Interior Mobil (Selfie)']

class GenerateRequest(BaseModel):
    config: StudioConfig
    productImage: str  # base64 string
    faceImage: Optional[str] = None  # base64 string
    customBgImage: Optional[str] = None  # base64 string

class GeneratedImage(BaseModel):
    url: str
    videoPrompt: str

# Authentication models
class GoogleLoginRequest(BaseModel):
    email: str

class GoogleTokenRequest(BaseModel):
    token: str

class VerifyEmailRequest(BaseModel):
    email: str

class AddUserRequest(BaseModel):
    email: str
    role: str = "user"

# Constants (same as in original app.py)
MODELS = ['Pria', 'Wanita', 'Anak Laki-Laki', 'Anak Perempuan', 'Hewan (Peliharaan)', 'Cartoon', 'Manekin', 'Tanpa Model (Hanya Produk)']
CATEGORIES = ['Fashion', 'Tas & Sepatu', 'Beauty & Skincare', 'Aksesories', 'Home & Living', 'Gadget & Elektronik', 'Food & Beverage (FnB)', 'Others']
HAND_INTERACTIONS = [
    'Tanpa Interaksi', 
    'Pegang produk – 1 tangan (Pria)', 
    'Pegang produk – 2 tangan (Pria)', 
    'Pegang produk – 1 tangan (Wanita)', 
    'Pegang produk – 2 tangan (Wanita)',
    'Interaksi Kaki (Pria)',
    'Interaksi Kaki (Wanita)'
]
ANIMAL_POSES = [
    'Pose di Samping Produk',
    'Interaksi (Mencium/Menyentuh)',
    'Berbaring Bersama Produk',
    'Melihat Kamera & Produk',
    'Action Shot (Bermain)',
    'Luxury Pet Lifestyle'
]
MODEL_SPECIFIC_POSES = [
    'Sitting Pose Relax',
    'Casual Selfie (Front Camera)',
    'Mirror Selfie dengan iPhone'
]
FOOT_INTERACTION_POSES = [
    'Berdiri Natural',
    'Berdiri Melangkah',
    'Pose Kaki Berdiri (Detail)',
    'Hand Holding Shot',
    'Shoulder Carry Shot',
    'Foot Wearing Shot',
    'Walking Step Motion',
    'Cropped Lifestyle Shot',
    'Prompt Custom (bisa diedit)'
]

DYNAMIC_POSES = {
    'Fashion': {
        'productOnly': [
            'Pegang Hanger Dengan Produk', 'Flat Lay Premium', 'Hanging Natural', 'Folded Neat (Lipatan Rapi)', 
            'Detail Fabric Close-Up', 'Sofa / Chair Lay', 'Minimal Studio'
        ],
        'withModel': [
            'Lifestyle Natural', 'Standing Pose Casual', 'Walking Motion', 'Detail Wear Shot'
        ] + MODEL_SPECIFIC_POSES
    },
    'Tas & Sepatu': {
        'productOnly': [
            'Hero Product Shot', 'Styled Flat Lay', 'Side Angle View', 'Back & Bottom Detail', 
            'Texture Close-Up', 'Clean Background'
        ],
        'withModel': [
            'Hand Holding Shot', 'Shoulder Carry Shot', 'Foot Wearing Shot', 'Walking Step Motion'
        ] + MODEL_SPECIFIC_POSES
    },
    'Beauty & Skincare': {
        'productOnly': [
            'Clean Studio Look', 'Ingredient Concept', 'Texture Swatch Shot', 'Bathroom Aesthetic', 
            'Minimal Table Setup'
        ],
        'withModel': [
            'Hand Application Shot', 'Half Face Glow', 'Close Skin Detail', 'Natural Daily Use'
        ] + MODEL_SPECIFIC_POSES
    },
    'Aksesories': {
        'productOnly': [
            'Flat Lay Elegant', 'Display Stand Shot', 'Hanging Display', 'Macro Detail Shot'
        ],
        'withModel': [
            'Wrist Wearing Shot', 'Neck / Shoulder Shot', 'Soft Lifestyle Detail'
        ] + MODEL_SPECIFIC_POSES
    },
    'Home & Living': {
        'productOnly': [
            'Room Styling', 'Tabletop Aesthetic', 'Minimal Interior', 'Functional Close-Up'
        ],
        'withModel': [
            'Hand Activity Shot', 'Daily Home Moment'
        ] + MODEL_SPECIFIC_POSES
    },
    'Gadget & Elektronik': {
        'productOnly': [
            'Clean Tech Studio', 'Desk Setup Shot', 'Product Angle View', 'Feature Detail Shot'
        ],
        'withModel': [
            'Hand Interaction', 'Lifestyle Usage', 'Close Feature Usage'
        ] + MODEL_SPECIFIC_POSES
    },
    'Food & Beverage (FnB)': {
        'productOnly': [
            'Flat Lay Food', 'Close Texture Shot', 'Serving Presentation', 'Minimal Table Style'
        ],
        'withModel': [
            'Hand Serving Shot', 'Eating Moment', 'Lifestyle Dining Shot'
        ] + MODEL_SPECIFIC_POSES
    },
    'Others': {
        'productOnly': [
            'Minimalist Studio Placement', 'Floating in Soft Space', 'Premium Tabletop Shot', 
            'Dynamic Shadows Concept', 'Macro Feature Focus'
        ],
        'withModel': [
            'Holding Product Naturally', 'Lifestyle Scene Interaction', 'Close-up Hand & Product', 
            'Looking at Product'
        ] + MODEL_SPECIFIC_POSES
    }
}

BACKGROUNDS = [
    'Studio', 'Kamar Aesthetic', 'Minimalis', 'Jalan', 'Meja Aesthetic', 
    'Karpet', 'Gorden', 'Interior Mobil (Selfie)', 'Hapus Latar', 'Warna (Custom)', 
    'Upload Latar', 'Custom Prompt'
]

STYLES = [
    'Studio Clean', 'Lifestyle', 'Indoor/Outdoor', 'Editorial', 'Beauty Glamour',
    'Minimalist', 'TikTok Trendy', 'Cinematic', 'Neon Futuristic', 'Flat Lay',
    'Product-on-Table', 'Campaign Poster', 'Macro', 'Outdoor Cafe', 'Custom'
]

LIGHTING = [
    'Natural Daylight', 'Golden Hour', 'Sunset Glow', 'Dramatic Contrast',
    'Low-key', 'High-key', 'Diffused Window Light', 'Neon Ambience',
    'Warm Candle', 'Reflective Glow', 'Softbox', 'Ring Light', 'Cool Tone',
    'Editorial', 'Custom'
]

ANGLES = [
    'Eye-Level', '45° Angle', 'Over-the-Shoulder', 'Macro Close-Up',
    'Medium Shot', 'Tight Portrait Crop', 'Dutch Angle', 'Top-Down Flat Lay',
    'Side Angle (30-60°)', 'Front Symmetrical', 'Wide Full Body', 'Bird\'s-Eye View'
]

RATIOS = [
    {'label': '1:1 (Square)', 'value': '1:1'},
    {'label': '2:3 (Portrait)', 'value': '2:3'},
    {'label': '4:5 (Portrait)', 'value': '4:5'},
    {'label': '16:9 (Landscape)', 'value': '16:9'},
    {'label': '3:4 (Portrait)', 'value': '3:4'},
    {'label': '9:16 (Story)', 'value': '9:16'}
]

# Helper functions
def is_human_model(model_type: str) -> bool:
    return model_type in ['Pria', 'Wanita', 'Anak Laki-Laki', 'Anak Perempuan']

def is_product_only(model_type: str) -> bool:
    return model_type == 'Tanpa Model (Hanya Produk)'

def is_animal(model_type: str) -> bool:
    return model_type == 'Hewan (Peliharaan)'

def is_foot_interaction(hand_interaction: str) -> bool:
    return 'Kaki' in hand_interaction or 'Interaksi Kaki' in hand_interaction

# Legacy functions for StudioConfig (used by /api/generate endpoint)
def get_current_pose_options(config: StudioConfig) -> List[str]:
    """Get dynamic pose options based on config (legacy for StudioConfig)"""
    if is_product_only(config.modelType):
        if is_foot_interaction(config.handInteraction):
            return FOOT_INTERACTION_POSES
        category_data = DYNAMIC_POSES.get(config.category, DYNAMIC_POSES['Fashion'])
        return category_data['productOnly'] + ['Prompt Kustom']
    
    if is_animal(config.modelType):
        return ANIMAL_POSES + ['Prompt Kustom']
    
    category_data = DYNAMIC_POSES.get(config.category, DYNAMIC_POSES['Fashion'])
    return category_data['withModel'] + ['Prompt Kustom']

def get_current_background_options(config: StudioConfig) -> List[str]:
    """Get dynamic background options based on config (legacy for StudioConfig)"""
    if is_human_model(config.modelType):
        return BACKGROUNDS
    return [bg for bg in BACKGROUNDS if bg != 'Interior Mobil (Selfie)']

def generate_video_prompt(image_url: str) -> str:
    """Generates a video prompt for a 6-second clip based on the generated image."""
    try:
        # Extract pure base64 and mime_type from data URL
        image_base64, image_mime = extract_base64_and_mime_type(image_url, "image/png")
        
        if not image_base64:
            raise ValueError("Image base64 is empty")
        
        # Validate base64
        try:
            base64.b64decode(image_base64)
        except Exception as decode_error:
            raise ValueError(f"Invalid base64 data: {str(decode_error)}")
        
        prompt_text = """
STEP 1: Analyze the generated image carefully to determine human presence (full body, face, hand, foot, etc.).
STEP 2: Select ONE motion style: Subtle Static, Natural Micro Movement, or Slow Confident Presentation.
STEP 3: Generate ONE video prompt exactly 6 seconds long.

STRICT VIDEO RULES:
- Do NOT include headers like "TASK" or "STEP" in your final response.
- Do NOT include any analysis text or reasoning.
- Do NOT alter product appearance.
- Match lighting and background exactly.
- Motion must be realistic and natural.

FINAL OUTPUT FORMAT:
Only return the text section titled exactly as:
"GROK VIDEO PROMPT (6 SECONDS)"
followed by the concise video prompt. 
Example:
"GROK VIDEO PROMPT (6 SECONDS)"
A high-resolution video of the watch on the table, with subtle light glints reflecting off the glass as the camera breathes slightly.
        """
        
        # Use new SDK with inline_data format
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[
                {
                    "role": "user",
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": image_mime,  # Use extracted mime_type
                                "data": image_base64  # Pure base64 string, no data URL prefix
                            }
                        },
                        {"text": prompt_text}
                    ]
                }
            ]
        )
        
        # Extract text from response
        if hasattr(response, 'text'):
            return response.text
        elif hasattr(response, 'candidates') and response.candidates:
            if hasattr(response.candidates[0], 'content'):
                if hasattr(response.candidates[0].content, 'parts'):
                    text_parts = [part.text for part in response.candidates[0].content.parts if hasattr(part, 'text')]
                    return ' '.join(text_parts)
        return str(response)
    except Exception as e:
        error_msg = str(e)
        if "API_KEY" in error_msg or "api_key" in error_msg or "authentication" in error_msg.lower():
            raise HTTPException(status_code=401, detail="API Key tidak valid atau tidak ditemukan.")
        elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
            raise HTTPException(status_code=429, detail="Quota API telah habis.")
        else:
            raise HTTPException(status_code=500, detail=f"Failed to generate video prompt: {error_msg}")

def generate_studio_image(config: StudioConfig, product_image: str, face_image: Optional[str] = None, custom_bg_image: Optional[str] = None):
    """Generate one variation of the studio image"""
    is_human = config.modelType in ['Pria', 'Wanita', 'Anak Laki-Laki', 'Anak Perempuan']
    
    image_generation_rules = """
1. Generate a realistic product photograph using the product image (Part 2) as primary reference.
2. If Part 3 is provided, integrate the face/model naturally with accurate proportions.
3. STRICT RULES: No changes to product shape/color/logo. No added objects. No text/watermarks. 
4. Render realistic micro-details (pores, fine hairs, natural textures). ABSOLUTELY NO artificial smoothness or "plastic" look.
    """
    
    # Build instructions
    model_instructions = ""
    background_instructions = config.background if config.background != 'Custom Prompt' else (config.customBackgroundPrompt or '')
    pose_instructions = config.pose if config.pose not in ['Prompt Kustom', 'Prompt Custom (bisa diedit)'] else (config.customPosePrompt or '')
    perspective_instructions = config.angle
    lighting_instructions = config.lighting if config.lighting != 'Custom' else (config.customLightingPrompt or '')
    style_instructions = config.style if config.style != 'Custom' else (config.customStylePrompt or '')
    
    # Handle special background cases
    if config.background == 'Interior Mobil (Selfie)':
        background_instructions = "Inside a modern car interior. Include car seat upholstery, headrest, and dashboard details. High-fidelity interior lighting."
    elif config.background == 'Upload Latar':
        background_instructions = "Use the exact environment from the provided background reference image (Part 4)."
    
    # Handle special pose cases
    if config.pose == 'Casual Selfie (Front Camera)':
        pose_instructions = "Casual front-facing selfie pose. One arm extended forward holding the camera. Relaxed shoulders, natural posture."
    
    # Build model instructions
    if config.modelType == 'Tanpa Model (Hanya Produk)':
        model_instructions = "Focus EXCLUSIVELY on the product from Part 2. Clean, professional product placement shot."
        if config.handInteraction != 'Tanpa Interaksi':
            interaction_type = 'foot/leg' if 'Kaki' in config.handInteraction else 'hand'
            model_instructions += f" The scene includes a partial human interaction: {config.handInteraction}. The {interaction_type} element should look raw, detailed, and realistic (visible skin pores, fine hair, natural texture) but the focus remains on the product."
    else:
        model_instructions = f"A real human {config.modelType} model interacting naturally with the product from Part 2. Face identity from Part 3 if provided."
        if config.handInteraction != 'Tanpa Interaksi':
            model_instructions += f" Model interaction: {config.handInteraction}."
    
    # Build prompt
    aspect_ratio_text = f"\nASPECT RATIO: {config.aspectRatio}" if config.aspectRatio else ""
    prompt = f"""
{image_generation_rules}

COMPOSITION:
- SUBJECT: {model_instructions}
- BACKGROUND: {background_instructions}
- POSE: {pose_instructions}
- PERSPECTIVE: {perspective_instructions}
- LIGHTING: {lighting_instructions}
- STYLE: {style_instructions}
{aspect_ratio_text}

TECHNICAL: Shot on Phase One IQ4, 150MP, sharp focus, 8K, high-frequency texture detail, zero digital noise.
    """
    
    # Build parts for new SDK format
    parts = []
    
    # Add text prompt first
    parts.append({"text": prompt})
    
    # Part 2: Product image
    if product_image:
        try:
            # Extract pure base64 and mime_type from data URL
            product_base64, product_mime = extract_base64_and_mime_type(product_image, "image/png")
            if not product_base64:
                raise ValueError("Product image base64 is empty")
            
            # Validate base64
            try:
                base64.b64decode(product_base64)
            except Exception as decode_error:
                raise ValueError(f"Invalid base64 data: {str(decode_error)}")
            
            # Use inline_data format with correct mime_type (pure base64, no prefix)
            parts.append({
                "inline_data": {
                    "mime_type": product_mime,
                    "data": product_base64  # Pure base64 string, no data URL prefix
                }
            })
            logger.info(f"Added product image with mime_type: {product_mime}")
        except Exception as e:
            logger.error(f"Failed to process product image: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to decode product image: {str(e)}")
    
    # Part 3: Face reference (if provided and is human model)
    if face_image and is_human:
        try:
            # Extract pure base64 and mime_type from data URL
            face_base64, face_mime = extract_base64_and_mime_type(face_image, "image/png")
            if not face_base64:
                logger.warning("Face image base64 is empty, skipping")
            else:
                # Validate base64
                try:
                    base64.b64decode(face_base64)
                except Exception:
                    logger.warning("Invalid face image base64, skipping")
                else:
                    parts.append({
                        "inline_data": {
                            "mime_type": face_mime,
                            "data": face_base64  # Pure base64 string, no data URL prefix
                        }
                    })
                    logger.info(f"Added face image with mime_type: {face_mime}")
        except Exception as e:
            logger.warning(f"Failed to process face image: {str(e)}, continuing without it")
    
    # Part 4: Custom background (if provided)
    if custom_bg_image and config.background == 'Upload Latar':
        try:
            # Extract pure base64 and mime_type from data URL
            bg_base64, bg_mime = extract_base64_and_mime_type(custom_bg_image, "image/png")
            if not bg_base64:
                logger.warning("Background image base64 is empty, skipping")
            else:
                # Validate base64
                try:
                    base64.b64decode(bg_base64)
                except Exception:
                    logger.warning("Invalid background image base64, skipping")
                else:
                    parts.append({
                        "inline_data": {
                            "mime_type": bg_mime,
                            "data": bg_base64  # Pure base64 string, no data URL prefix
                        }
                    })
                    logger.info(f"Added background image with mime_type: {bg_mime}")
        except Exception as e:
            logger.warning(f"Failed to process background image: {str(e)}, continuing without it")
    
    # Generate image using Gemini
    try:
        # Convert parts to new SDK format
        request_contents = [
            {
                "role": "user",
                "parts": parts
            }
        ]
        
        logger.info(f"Generating image with {len(parts)} parts")
        
        # Convert multimodal input to text-only prompt for imagen-3.0-generate-001
        # imagen is text-to-image only, so we enhance the text prompt to describe images
        enhanced_prompt = prompt
        
        # Add image reference descriptions
        image_refs = []
        if product_image:
            image_refs.append("product reference image")
        if face_image and is_human:
            image_refs.append("model face reference image")
        if custom_bg_image and config.background == 'Upload Latar':
            image_refs.append("background reference image")
        
        if image_refs:
            enhanced_prompt = f"{enhanced_prompt}\n\nIMPORTANT: Use the provided reference images ({', '.join(image_refs)}) as exact visual guides. Match product appearance, model features, and background environment precisely from the reference images."
        
        # Use imagen-3.0-generate-001 for image generation (text-to-image model)
        # WARNING: imagen-3.0-generate-001 may require Vertex AI SDK instead of google.genai
        # If this fails, consider using Node.js backend with gemini-2.5-flash-image
        try:
            response = client.models.generate_content(
                model="imagen-3.0-generate-001",
                contents=[
                    {
                        "role": "user",
                        "parts": [{"text": enhanced_prompt}]
                    }
                ],
                config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                }
            )
        except Exception as imagen_error:
            error_msg = str(imagen_error)
            if "not found" in error_msg.lower() or "404" in error_msg or "imagen" in error_msg.lower():
                logger.error(f"imagen-3.0-generate-001 may not be available through google.genai SDK. Error: {error_msg}")
                logger.error("Consider using Node.js backend with gemini-2.5-flash-image instead, or switch to Vertex AI SDK for imagen models.")
                # Re-raise with more context
                raise HTTPException(
                    status_code=500,
                    detail=f"imagen-3.0-generate-001 not available. Consider using Node.js backend with gemini-2.5-flash-image. Original error: {error_msg}"
                )
            raise
        except Exception as e:
            # Capture detailed error information from Google AI Studio
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "model": "imagen-3.0-generate-001",  # Note: May require Vertex AI SDK
                "parts_count": len(parts),
                "has_product_image": bool(product_image),
                "has_face_image": bool(face_image and is_human),
                "has_custom_bg": bool(custom_bg_image and config.background == 'Upload Latar')
            }
            
            # Try to extract response data if available
            if hasattr(e, 'response'):
                try:
                    if hasattr(e.response, 'data'):
                        error_details["response_data"] = e.response.data
                    if hasattr(e.response, 'status_code'):
                        error_details["status_code"] = e.response.status_code
                    if hasattr(e.response, 'headers'):
                        error_details["response_headers"] = dict(e.response.headers)
                except Exception as parse_error:
                    error_details["response_parse_error"] = str(parse_error)
            
            # Check for safety filter or content filter errors
            error_str = str(e).lower()
            if "safety" in error_str or "filter" in error_str or "blocked" in error_str or "content" in error_str:
                error_details["safety_filter_issue"] = True
                logger.warning("⚠️ SAFETY FILTER DETECTED - Content may have been blocked by Google AI Studio")
            
            # Log full error details as JSON
            logger.error(f"Error calling Gemini API:\n{json.dumps(error_details, indent=2, default=str)}")
            logger.error(f"Full exception traceback:", exc_info=True)
            raise
        
        # Extract image from response
        image_url = product_image  # Default fallback
        
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content'):
                content = candidate.content
                if hasattr(content, 'parts'):
                    for part in content.parts:
                        if hasattr(part, 'inline_data'):
                            inline_data = part.inline_data
                            if hasattr(inline_data, 'data'):
                                image_url = f"data:image/png;base64,{inline_data.data}"
                                break
                        elif hasattr(part, 'mime_type') and part.mime_type == 'image/png':
                            if hasattr(part, 'data'):
                                image_url = f"data:image/png;base64,{part.data}"
                                break
        
        # Generate video prompt
        try:
            video_prompt = generate_video_prompt(image_url)
        except Exception as e:
            logger.warning(f"Failed to generate video prompt: {str(e)}")
            video_prompt = f""""GROK VIDEO PROMPT (6 SECONDS)"
A high-resolution video showing the product in this setting, with subtle natural movement and realistic lighting effects."""
        
        logger.info("Image generated successfully")
        return {
            "url": image_url,
            "videoPrompt": video_prompt
        }
    except Exception as e:
        error_msg = str(e)
        
        # Capture detailed error information from Google AI Studio
        error_details = {
            "error_type": type(e).__name__,
            "error_message": error_msg,
            "function": "generate_studio_image",
            "config": {
                "modelType": config.modelType,
                "category": config.category,
                "background": config.background,
                "pose": config.pose,
                "style": config.style,
                "lighting": config.lighting,
                "has_product_image": bool(product_image),
                "has_face_image": bool(face_image and is_human),
                "has_custom_bg": bool(custom_bg_image and config.background == 'Upload Latar')
            }
        }
        
        # Try to extract response data if available
        if hasattr(e, 'response'):
            try:
                if hasattr(e.response, 'data'):
                    error_details["response_data"] = e.response.data
                if hasattr(e.response, 'status_code'):
                    error_details["status_code"] = e.response.status_code
                if hasattr(e.response, 'headers'):
                    error_details["response_headers"] = dict(e.response.headers)
            except Exception as parse_error:
                error_details["response_parse_error"] = str(parse_error)
        
        # Check for safety filter or content filter errors
        error_str = error_msg.lower()
        if "safety" in error_str or "filter" in error_str or "blocked" in error_str or "content" in error_str:
            error_details["safety_filter_issue"] = True
            logger.warning("⚠️ SAFETY FILTER DETECTED in generate_studio_image - Content may have been blocked by Google AI Studio")
        
        # Log full error details as JSON
        logger.error(f"Error generating image:\n{json.dumps(error_details, indent=2, default=str)}")
        logger.error(f"Full exception traceback:", exc_info=True)
        
        # Provide more helpful error messages
        if "API_KEY" in error_msg or "api_key" in error_msg or "authentication" in error_msg.lower():
            raise HTTPException(status_code=401, detail="API Key tidak valid atau tidak ditemukan. Pastikan GEMINI_API_KEY sudah diatur dengan benar di config.env")
        elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
            raise HTTPException(status_code=429, detail="Quota API telah habis. Silakan cek quota di Google AI Studio.")
        else:
            raise HTTPException(status_code=500, detail="Generate failed")

# API Routes
@app.get("/")
async def root():
    return {"message": "Premium AI Studio API"}

@app.get("/api/constants")
async def get_constants():
    """Get all constants for the frontend"""
    return {
        "models": MODELS,
        "categories": CATEGORIES,
        "handInteractions": HAND_INTERACTIONS,
        "animalPoses": ANIMAL_POSES,
        "footInteractionPoses": FOOT_INTERACTION_POSES,
        "dynamicPoses": DYNAMIC_POSES,
        "backgrounds": BACKGROUNDS,
        "styles": STYLES,
        "lighting": LIGHTING,
        "angles": ANGLES,
        "ratios": RATIOS
    }

# Authentication endpoints
@app.post("/api/verify-email")
async def verify_email(request: VerifyEmailRequest):
    """Verify if email is authorized"""
    if is_email_authorized(request.email):
        role = get_user_role(request.email)
        return {
            "authorized": True,
            "email": request.email,
            "role": role
        }
    else:
        raise HTTPException(
            status_code=403,
            detail="Akses Ditolak: Email Anda belum terdaftar dalam sistem premium kami."
        )

@app.options("/auth/google-login")
async def google_login_options():
    """Handle CORS preflight for Google login"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Max-Age": "3600"
        }
    )

@app.post("/auth/google-login")
async def google_login(payload: GoogleLoginRequest):
    """Handle Google OAuth login"""
    try:
        logger.info(f"Google login attempt for email: {payload.email}")
        
        email = payload.email.lower()

        # 🔒 Check if email is in authorized_users database
        if not is_email_authorized(email):
            logger.warning(f"Unauthorized login attempt: {email}")
            raise HTTPException(
                status_code=403,
                detail="Akses Ditolak: Email Anda belum terdaftar dalam sistem premium kami."
            )
        
        # Get user role from Supabase profile
        role = get_user_role_from_email(email) or "user"
        
        logger.info(f"Login successful for {email} with role {role}")

        return {
            "user": {
                "email": email,
                "role": role
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in google_login: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")

@app.post("/api/verify-google-token")
async def verify_google_token(request: GoogleTokenRequest):
    """Verify Google OAuth token and check email authorization"""
    try:
        from google.auth.transport import requests  # type: ignore
        from google.oauth2 import id_token  # type: ignore
        
        # Verify the token
        idinfo = id_token.verify_oauth2_token(
            request.token, 
            requests.Request(),
            os.getenv('GOOGLE_CLIENT_ID', '')  # You'll need to set this in config.env
        )
        
        email = idinfo.get('email')
        if not email:
            raise HTTPException(status_code=400, detail="Email tidak ditemukan dalam token")
        
        # Check if email is authorized
        if is_email_authorized(email):
            role = get_user_role_from_email(email)
            return {
                "authorized": True,
                "email": email,
                "role": role,
                "name": idinfo.get('name', ''),
                "picture": idinfo.get('picture', '')
            }
        else:
            raise HTTPException(
                status_code=403,
                detail="Akses Ditolak: Email Anda belum terdaftar dalam sistem premium kami."
            )
    except ValueError:
        raise HTTPException(status_code=401, detail="Token tidak valid")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verifikasi token: {str(e)}")

# Admin endpoints
@app.post("/admin/add-user")
async def add_user(
    request: AddUserRequest,
    _: Dict[str, Any] = Depends(require_admin)
):
    """Add new user to authorized_users (Admin only)"""
    success = add_authorized_user(request.email, request.role)
    if success:
        return {
            "success": True,
            "message": f"User {request.email} berhasil ditambahkan dengan role {request.role}"
        }
    else:
        raise HTTPException(status_code=400, detail=f"Email {request.email} sudah terdaftar")

@app.post("/api/generate", response_model=List[GeneratedImage])
async def generate_images_legacy(request: GenerateRequest):
    """Generate 4 variations of studio images"""
    results = []
    for i in range(4):
        try:
            result = generate_studio_image(
                request.config,
                request.productImage,
                request.faceImage,
                request.customBgImage
            )
            results.append(result)
        except Exception as e:
            # Log detailed error information from Google AI Studio
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "variation_index": i,
                "config": {
                    "modelType": request.config.modelType,
                    "category": request.config.category,
                    "has_product_image": bool(request.productImage),
                    "has_face_image": bool(request.faceImage),
                    "has_custom_bg": bool(request.customBgImage)
                }
            }
            
            # Try to extract response data if available
            if hasattr(e, 'response'):
                try:
                    if hasattr(e.response, 'data'):
                        error_details["response_data"] = e.response.data
                    if hasattr(e.response, 'status_code'):
                        error_details["status_code"] = e.response.status_code
                    if hasattr(e.response, 'headers'):
                        error_details["response_headers"] = dict(e.response.headers)
                except Exception as parse_error:
                    error_details["response_parse_error"] = str(parse_error)
            
            # Check for safety filter or content filter errors
            error_str = str(e).lower()
            if "safety" in error_str or "filter" in error_str or "blocked" in error_str:
                error_details["safety_filter_issue"] = True
                logger.warning("⚠️ SAFETY FILTER DETECTED - Content may have been blocked")
            
            # Log full error details as JSON
            logger.error(f"Error generating image variation {i+1}:\n{json.dumps(error_details, indent=2, default=str)}")
            
            # Also log the full exception traceback
            logger.error(f"Full exception traceback:", exc_info=True)
            
            # Fallback for failed generation
            try:
                video_prompt = generate_video_prompt(request.productImage)
            except Exception as video_error:
                logger.warning(f"Failed to generate video prompt: {str(video_error)}")
                video_prompt = f""""GROK VIDEO PROMPT (6 SECONDS)"
A high-resolution video showing the product in this setting, with subtle natural movement and realistic lighting effects."""
            results.append({
                "url": request.productImage,
                "videoPrompt": video_prompt
            })
    
    return results

# New Pydantic models for new API (ImageDataModel and GenerationOptionsModel already defined above)
class GeneratePhotoRequest(BaseModel):
    productImages: List[ImageDataModel]
    faceImage: Optional[ImageDataModel] = None
    backgroundImage: Optional[ImageDataModel] = None
    options: GenerationOptionsModel

class GenerateVideoRequest(BaseModel):
    image: str  # base64 string
    options: GenerationOptionsModel

# Endpoints that use GenerationOptionsModel (defined after model to avoid forward reference issues)
@app.post("/api/pose-options")
async def get_pose_options(options: GenerationOptionsModel):
    """Get dynamic pose options based on options"""
    pose_options = get_current_pose_options_for_generation(options)
    return {"options": pose_options}

@app.post("/api/background-options")
async def get_background_options(options: GenerationOptionsModel):
    """Get dynamic background options based on options"""
    background_options = get_current_background_options_for_generation(options)
    return {"options": background_options}

@app.post("/api/generate-photo")
async def generate_photo(request: GeneratePhotoRequest):
    """Generate a single product photo with two video prompts (Version A and B)"""
    try:
        logger.info("Received generate-photo request")
        
        if not request.productImages:
            raise HTTPException(status_code=400, detail="At least one product image is required")
        
        # Convert Pydantic models to dict format for gemini_service
        product_images = [
            {"base64": img.base64, "mimeType": img.mimeType}
            for img in request.productImages
        ]
        
        face_image = None
        if request.faceImage:
            face_image = {
                "base64": request.faceImage.base64,
                "mimeType": request.faceImage.mimeType
            }
        
        background_image = None
        if request.backgroundImage:
            background_image = {
                "base64": request.backgroundImage.base64,
                "mimeType": request.backgroundImage.mimeType
            }
        
        logger.info(f"Generating photo with category: {request.options.category}, modelType: {request.options.modelType}")
        
        # Convert options to dict for backward compatibility with gemini_service
        # gemini_service expects dict format
        options_dict = {
            "background": request.options.background,
            "customBackgroundPrompt": request.options.customBackgroundPrompt,
            "pose": request.options.pose,
            "customPosePrompt": request.options.customPosePrompt,
            "style": request.options.style,
            "customStylePrompt": request.options.customStylePrompt,
            "lighting": request.options.lighting,
            "customLightingPrompt": request.options.customLightingPrompt,
            "aspectRatio": request.options.aspectRatio,
            "cameraAngle": request.options.cameraAngle,
            "additionalPrompt": request.options.additionalPrompt,
            "contentType": request.options.contentType,
            "modelType": request.options.modelType,
            "category": request.options.category,
            "interactionType": request.options.interactionType,
            "backgroundColor": request.options.backgroundColor
        }
        
        # Use the new gemini_service function
        result = generate_product_photo(
            product_images,
            face_image,
            background_image,
            options_dict
        )
        
        logger.info("Photo generated successfully")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_photo endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Generate failed")

# Node.js Image Service Proxy
IMAGE_SERVICE_URL = os.getenv('IMAGE_SERVICE_URL', 'http://localhost:3002')

class ImageGenerationRequest(BaseModel):
    prompt: str
    productImages: Optional[List[ImageDataModel]] = None
    faceImage: Optional[ImageDataModel] = None
    backgroundImage: Optional[ImageDataModel] = None
    images: Optional[List[ImageDataModel]] = None  # Legacy format

# ==================== SaaS AI Image & Video Generator Routes ====================

# Request models for SaaS routes
class GenerateImageRequest(BaseModel):
    prompt: str
    product_images: Optional[List[str]] = None  # Multiple product images (base64 atau data URL)
    face_image: Optional[str] = None  # Face image (base64 atau data URL)
    background_image: Optional[str] = None  # Background image (base64 atau data URL)
    # Legacy field untuk backward compatibility
    reference_image: Optional[str] = None  # Base64 image atau data URL (optional, akan dimap ke product_images[0])

class GenerateVideoRequestSaaS(BaseModel):
    prompt: str
    image_url: Optional[str] = None

class MidtransWebhookRequest(BaseModel):
    transaction_status: str
    order_id: str
    gross_amount: str
    payment_type: str
    fraud_status: Optional[str] = None
    user_id: Optional[str] = None  # Custom field from frontend

@app.get("/api/user/profile")
async def get_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user's profile"""
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in token")
        
        profile = get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        return {
            "free_image_quota": profile.get("free_image_quota", 0),
            "coins_balance": profile.get("coins_balance", 0)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/debug/last-prompt")
async def get_last_prompt(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Debug endpoint: Get last prompt that was sent to Fal.ai
    Returns the most recent prompt log entry for debugging
    """
    try:
        from debug_prompt_log import get_latest_prompt_log
        log_entry = get_latest_prompt_log()
        
        if log_entry:
            return log_entry
        else:
            raise HTTPException(
                status_code=404, 
                detail="No prompt log found. Please generate a batch first to create log entry."
            )
    except ImportError:
        raise HTTPException(
            status_code=500, 
            detail="Debug prompt log module not available."
        )
    except Exception as e:
        logger.error(f"Error getting last prompt log: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.post("/api/generate-image")
async def generate_image_saas(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Generate 2 images using Fal.ai flux/schnell
    - Image-to-image: jika image file diupload (upload ke Supabase Storage, lalu kirim image_url ke Fal.ai)
    - Text-to-image: jika tidak ada image file
    
    Endpoint: https://fal.run/fal-ai/flux/schnell
    Reduces coins_balance by 75 after successful generation
    
    Supports TWO formats:
    1. JSON body (backward compatible): {"prompt": "...", "product_images": [...], "face_image": "...", "background_image": "..."}
    2. Multipart/form-data (new): prompt (Form), image (File)
    """
    try:
        start_time = time.perf_counter()
        upload_elapsed = None
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in token")
        
        # Check user profile and coins balance
        profile = get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        coins = profile.get("coins_balance", 0)
        image_batch_cost = 75
        if coins < image_batch_cost:
            raise HTTPException(
                status_code=403,
                detail="Insufficient coins. You need at least 75 coins to generate images. Please top up to continue."
            )
        
        # Determine request format based on Content-Type
        content_type = request.headers.get("content-type", "").lower()
        prompt_to_use = None
        init_image_url = None  # Public URL dari Supabase Storage - LEGACY, gunakan init_image_urls
        init_image_urls = []  # Array of public URLs dari Supabase Storage - REQUIRED untuk image-to-image pipeline (multiple images)
        uploaded_images = []  # Store all uploaded image URLs (for logging/debugging)
        primary_image_type = None  # Type of primary image used for Fal.ai generation (legacy)
        fal_image_strength = None  # Image strength parameter from request (default: 0.67 - balanced for reference adherence)
        fal_num_inference_steps = None  # Number of inference steps from request (default: 24 - increased to prevent blank images)
        fal_guidance_scale = None  # Guidance scale (CFG) parameter from request (default: 4.5 - natural and realistic)
        fal_negative_prompt = None  # Negative prompt from request
        aspect_ratio = None  # Aspect ratio from request (e.g., "9:16", "16:9", "1:1")
        
        if "multipart/form-data" in content_type:
            # Handle multipart/form-data (file upload)
            form_data = await request.form()
            prompt_to_use = form_data.get("prompt")
            aspect_ratio = form_data.get("aspect_ratio") or form_data.get("aspectRatio")  # Support both formats
            
            if not prompt_to_use:
                raise HTTPException(status_code=422, detail="Missing required field: prompt")
            
            # Handle file upload - REQUIRED untuk image-to-image pipeline
            image_file = form_data.get("image")
            if not image_file or not hasattr(image_file, 'filename') or not image_file.filename:
                raise HTTPException(
                    status_code=422,
                    detail="Missing required image file. This is an image-to-image pipeline - image upload is required."
                )
            
            try:
                # Reset file pointer to beginning (in case it was read before)
                if hasattr(image_file, 'file') and hasattr(image_file.file, 'seek'):
                    image_file.file.seek(0)
                
                # Read uploaded file content
                file_content = await image_file.read()
                file_name = image_file.filename
                file_size = len(file_content)
                
                logger.info(f"📤 Received image file upload: {file_name} ({file_size} bytes)")
                
                if file_size == 0:
                    raise HTTPException(
                        status_code=422,
                        detail="Empty file uploaded. Please upload a valid image file."
                    )
                
                # PREPROCESSING PIPELINE: Process image before uploading
                # Get aspect ratio from form data (default to 1:1 if not provided)
                target_aspect_ratio = aspect_ratio or "1:1"
                
                try:
                    logger.info(f"🔄 Starting image preprocessing pipeline...")
                    logger.info(f"   Target aspect ratio: {target_aspect_ratio}")
                    
                    # Determine image type (default to full_body for multipart uploads)
                    image_type = "full_body"  # Can be enhanced with detection later
                    
                    # Preprocess image
                    processed_bytes, file_ext, preprocess_metadata = preprocess_image(
                        image_bytes=file_content,
                        target_aspect_ratio=target_aspect_ratio,
                        image_type=image_type,
                        filename=file_name
                    )
                    
                    logger.info(f"✅ Image preprocessing complete:")
                    logger.info(f"   Original: {preprocess_metadata.get('original_resolution')}, {preprocess_metadata.get('original_size_mb')} MB")
                    logger.info(f"   Final: {preprocess_metadata.get('final_resolution')} ({preprocess_metadata.get('final_megapixels')} MP), {preprocess_metadata.get('final_size_mb')} MB")
                    
                    # Use processed image for upload
                    file_content = processed_bytes
                    file_name = f"processed_{file_name.rsplit('.', 1)[0]}{file_ext}" if '.' in file_name else f"processed_image{file_ext}"
                    
                except Exception as preprocess_error:
                    logger.error(f"❌ Image preprocessing failed: {str(preprocess_error)}", exc_info=True)
                    raise HTTPException(
                        status_code=422,
                        detail=f"Image preprocessing failed: {str(preprocess_error)}"
                    )
                
                # Upload to Supabase Storage - REQUIRED (now using processed image)
                # Extract category from filename or use default
                category = "upload"  # Default category for multipart uploads
                public_url = upload_image_to_supabase_storage(
                    file_content=file_content,
                    file_name=file_name,
                    bucket_name="IMAGES_UPLOAD",
                    user_id=user_id,
                    category=category
                )
                
                init_image_url = public_url  # Legacy compatibility
                init_image_urls = [public_url]  # Array format untuk Fal.ai
                primary_image_type = "multipart_upload"
                uploaded_images = [{"type": "multipart_upload", "url": public_url}]
                logger.info(f"✅ Image uploaded to Supabase Storage successfully")
                logger.info(f"   Public URL: {init_image_url}")
                logger.info(f"   Image-to-image pipeline: Using uploaded image as reference")
                logger.info(f"✅ Total 1 image(s) uploaded to Supabase Storage")
                upload_elapsed = time.perf_counter() - start_time
                logger.info(f"⏱️ Upload + preprocess time: {upload_elapsed:.2f}s")
                
            except Exception as e:
                logger.error(f"Error uploading image to Supabase Storage: {str(e)}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to upload image to Supabase Storage: {str(e)}. Image is required for image-to-image pipeline."
                )
        else:
            # Handle JSON body (backward compatible)
            try:
                json_data = await request.json()
                prompt_to_use = json_data.get("prompt")
                
                if not prompt_to_use:
                    raise HTTPException(status_code=422, detail="Missing required field: prompt")
                
                # Read Fal.ai parameters from request body (if provided)
                # Default: image_strength=0.67, num_inference_steps=24, guidance_scale=4.5 (natural and realistic)
                fal_image_strength = json_data.get("image_strength")
                fal_num_inference_steps = json_data.get("num_inference_steps")
                fal_guidance_scale = json_data.get("guidance_scale")
                fal_negative_prompt = json_data.get("negative_prompt")
                aspect_ratio = json_data.get("aspect_ratio") or json_data.get("aspectRatio")  # Support both formats
                
                # Handle base64 images - REQUIRED untuk image-to-image pipeline
                # Upload ALL images to Supabase Storage, but use priority for Fal.ai generation
                # Priority: face_image > product_images[0] > background_image
                product_images = json_data.get("product_images") or []
                reference_image = json_data.get("reference_image")
                if reference_image and not product_images:
                    product_images = [reference_image]
                
                face_image = json_data.get("face_image")
                background_image = json_data.get("background_image")
                
                # Check if any images provided (base64) - REQUIRED untuk image-to-image pipeline
                has_images = (product_images and len([img for img in product_images if img]) > 0) or face_image or background_image
                
                if not has_images:
                    raise HTTPException(
                        status_code=422,
                        detail="Missing required image. This is an image-to-image pipeline - please provide at least one image (face_image, product_images, or background_image)."
                    )
                
                # Upload ALL images to Supabase Storage (for storage/backup)
                uploaded_images = []  # Store all uploaded image URLs
                primary_image_url = None  # Primary image for Fal.ai generation
                
                try:
                    # 1. Upload face_image if provided
                    if face_image:
                        try:
                            # Convert base64 to bytes
                            raw_image_bytes, raw_file_ext = convert_base64_to_image_bytes(face_image, compress_if_over_1mb=False)
                            
                            # PREPROCESSING PIPELINE: Process image before uploading
                            target_aspect_ratio = aspect_ratio or "1:1"
                            logger.info(f"🔄 Preprocessing face_image (target aspect: {target_aspect_ratio})...")
                            
                            try:
                                processed_bytes, file_ext, preprocess_metadata = preprocess_image(
                                    image_bytes=raw_image_bytes,
                                    target_aspect_ratio=target_aspect_ratio,
                                    image_type="face_dominant",  # Face images are typically face-dominant
                                    filename=f"face_image{raw_file_ext}"
                                )
                                
                                logger.info(f"✅ Face image preprocessing complete:")
                                logger.info(f"   Final: {preprocess_metadata.get('final_resolution')} ({preprocess_metadata.get('final_megapixels')} MP), {preprocess_metadata.get('final_size_mb')} MB")
                                
                                # Use processed image
                                image_bytes = processed_bytes
                                file_size = len(image_bytes)
                                
                            except Exception as preprocess_error:
                                logger.error(f"❌ Face image preprocessing failed: {str(preprocess_error)}", exc_info=True)
                                raise HTTPException(
                                    status_code=422,
                                    detail=f"Face image preprocessing failed: {str(preprocess_error)}"
                                )
                            
                            logger.info(f"📤 Uploading preprocessed face_image to Supabase Storage (size: {file_size} bytes)")
                            
                            public_url = upload_image_to_supabase_storage(
                                file_content=image_bytes,
                                file_name=f"face_image{file_ext}",
                                bucket_name="IMAGES_UPLOAD",
                                user_id=user_id,
                                category="face"
                            )
                            
                            uploaded_images.append({"type": "face_image", "url": public_url})
                            if not primary_image_url:
                                primary_image_url = public_url
                                primary_image_type = "face_image"
                            logger.info(f"✅ face_image uploaded successfully: {public_url}")
                        except Exception as e:
                            logger.error(f"❌ Failed to upload face_image: {str(e)}")
                            raise  # Stop process on failure
                    
                    # 2. Upload all product_images if provided
                    if product_images and len([img for img in product_images if img]) > 0:
                        valid_product_images = [img for img in product_images if img]  # Filter out None/empty
                        logger.info(f"📤 Uploading {len(valid_product_images)} product_image(s) to Supabase Storage")
                        
                        for idx, img in enumerate(valid_product_images):
                            try:
                                # Convert base64 to bytes
                                raw_image_bytes, raw_file_ext = convert_base64_to_image_bytes(img, compress_if_over_1mb=False)
                                
                                # PREPROCESSING PIPELINE: Process image before uploading
                                target_aspect_ratio = aspect_ratio or "1:1"
                                logger.info(f"🔄 Preprocessing product_image[{idx}] (target aspect: {target_aspect_ratio})...")
                                
                                try:
                                    # Determine image type based on index (first product might be full body, second might be half body)
                                    image_type = "full_body" if idx == 0 else "half_body"
                                    
                                    processed_bytes, file_ext, preprocess_metadata = preprocess_image(
                                        image_bytes=raw_image_bytes,
                                        target_aspect_ratio=target_aspect_ratio,
                                        image_type=image_type,
                                        filename=f"product_image_{idx}{raw_file_ext}"
                                    )
                                    
                                    logger.info(f"✅ Product image[{idx}] preprocessing complete:")
                                    logger.info(f"   Final: {preprocess_metadata.get('final_resolution')} ({preprocess_metadata.get('final_megapixels')} MP), {preprocess_metadata.get('final_size_mb')} MB")
                                    
                                    # Use processed image
                                    image_bytes = processed_bytes
                                    file_size = len(image_bytes)
                                    
                                except Exception as preprocess_error:
                                    logger.error(f"❌ Product image[{idx}] preprocessing failed: {str(preprocess_error)}", exc_info=True)
                                    raise HTTPException(
                                        status_code=422,
                                        detail=f"Product image[{idx}] preprocessing failed: {str(preprocess_error)}"
                                    )
                                
                                logger.info(f"📤 Uploading preprocessed product_image[{idx}] to Supabase Storage (size: {file_size} bytes)")
                                
                                public_url = upload_image_to_supabase_storage(
                                    file_content=image_bytes,
                                    file_name=f"product_image_{idx}{file_ext}",
                                    bucket_name="IMAGES_UPLOAD",
                                    user_id=user_id,
                                    category="product"
                                )
                                
                                uploaded_images.append({"type": f"product_image_{idx}", "url": public_url})
                                if not primary_image_url:
                                    primary_image_url = public_url
                                    primary_image_type = f"product_image_{idx}"
                                logger.info(f"✅ product_image[{idx}] uploaded successfully: {public_url}")
                            except Exception as e:
                                logger.error(f"❌ Failed to upload product_image[{idx}]: {str(e)}")
                                raise  # Stop process on failure
                    
                    # 3. Upload background_image if provided
                    if background_image:
                        try:
                            # Convert base64 to bytes
                            raw_image_bytes, raw_file_ext = convert_base64_to_image_bytes(background_image, compress_if_over_1mb=False)
                            
                            # PREPROCESSING PIPELINE: Process image before uploading
                            target_aspect_ratio = aspect_ratio or "1:1"
                            logger.info(f"🔄 Preprocessing background_image (target aspect: {target_aspect_ratio})...")
                            
                            try:
                                processed_bytes, file_ext, preprocess_metadata = preprocess_image(
                                    image_bytes=raw_image_bytes,
                                    target_aspect_ratio=target_aspect_ratio,
                                    image_type="full_body",  # Backgrounds are typically full scene
                                    filename=f"background_image{raw_file_ext}"
                                )
                                
                                logger.info(f"✅ Background image preprocessing complete:")
                                logger.info(f"   Final: {preprocess_metadata.get('final_resolution')} ({preprocess_metadata.get('final_megapixels')} MP), {preprocess_metadata.get('final_size_mb')} MB")
                                
                                # Use processed image
                                image_bytes = processed_bytes
                                file_size = len(image_bytes)
                                
                            except Exception as preprocess_error:
                                logger.error(f"❌ Background image preprocessing failed: {str(preprocess_error)}", exc_info=True)
                                raise HTTPException(
                                    status_code=422,
                                    detail=f"Background image preprocessing failed: {str(preprocess_error)}"
                                )
                            
                            logger.info(f"📤 Uploading preprocessed background_image to Supabase Storage (size: {file_size} bytes)")
                            
                            public_url = upload_image_to_supabase_storage(
                                file_content=image_bytes,
                                file_name=f"background_image{file_ext}",
                                bucket_name="IMAGES_UPLOAD",
                                user_id=user_id,
                                category="background"
                            )
                            
                            uploaded_images.append({"type": "background_image", "url": public_url})
                            if not primary_image_url:
                                primary_image_url = public_url
                                primary_image_type = "background_image"
                            logger.info(f"✅ background_image uploaded successfully: {public_url}")
                        except Exception as e:
                            logger.error(f"❌ Failed to upload background_image: {str(e)}")
                            raise  # Stop process on failure
                    
                    # Collect ALL uploaded images for Fal.ai generation (products + face + background)
                    # Priority order: Main Product (Ref 1) → Optional Product (Ref 2) → Face (Ref 3) → Background (Ref 4)
                    # Fal.ai flux-2/lora/edit supports up to 3 images in image_urls array
                    init_image_urls = []  # Array untuk multiple images
                    
                    # Priority order untuk Fal.ai (max 3 images):
                    # 1. Product images (REQUIRED - at least 1)
                    # 2. Background (CRITICAL - must be included if uploaded, as it's the environment)
                    # 3. Face (optional, only if space available)
                    
                    # Check if background exists
                    background_image_info = next((img for img in uploaded_images if img["type"] == "background_image"), None)
                    has_background = background_image_info is not None
                    
                    # 1. Add Main Product first (REQUIRED - at least 1 product)
                    product_image_infos = [img for img in uploaded_images if img["type"].startswith("product_image_")]
                    # Sort by index to maintain order (product_image_0 = Main, product_image_1 = Optional)
                    product_image_infos.sort(key=lambda x: int(x["type"].split("_")[-1]) if x["type"].split("_")[-1].isdigit() else 999)
                    
                    # Calculate available slots (max 3 total)
                    max_slots = 3
                    slots_used = 0
                    
                    # Add at least 1 product (required)
                    if len(product_image_infos) > 0:
                        init_image_urls.append(product_image_infos[0]["url"])
                        slots_used += 1
                        logger.info(f"   ✅ Added {product_image_infos[0]['type']} to Fal.ai request (Ref {slots_used}: The Main - REQUIRED)")
                    
                    # 2. Add background_image (CRITICAL - must be included if uploaded)
                    # Background is critical because it defines the entire scene/environment
                    if background_image_info and slots_used < max_slots:
                        init_image_urls.append(background_image_info["url"])
                        slots_used += 1
                        logger.info(f"   ✅ Added background_image to Fal.ai request (Ref {slots_used}: The Background Environment - CRITICAL)")
                    
                    # 3. Add second product if available and space allows
                    if len(product_image_infos) > 1 and slots_used < max_slots:
                        init_image_urls.append(product_image_infos[1]["url"])
                        slots_used += 1
                        logger.info(f"   ✅ Added {product_image_infos[1]['type']} to Fal.ai request (Ref {slots_used}: The Optional)")
                    
                    # 4. Add face_image LAST (only if space available)
                    face_image_info = next((img for img in uploaded_images if img["type"] == "face_image"), None)
                    if face_image_info and slots_used < max_slots:
                        init_image_urls.append(face_image_info["url"])
                        slots_used += 1
                        logger.info(f"   ✅ Added face_image to Fal.ai request (Ref {slots_used}: The Face)")
                    elif face_image_info:
                        logger.warning(f"   ⚠️ Skipping face_image - max 3 images reached (background takes priority)")
                    
                    # Final order: [Product1, Background, Product2/Face] or [Product1, Product2, Face] if no background
                    # This ensures background is always included if uploaded (priority over face)
                    logger.info(f"   📋 Final image order for Fal.ai ({len(init_image_urls)} images):")
                    for idx, url in enumerate(init_image_urls):
                        img_type = next((img["type"] for img in uploaded_images if img["url"] == url), "unknown")
                        if img_type == "background_image":
                            ref_name = "The Background Environment (CRITICAL)"
                        elif idx == 0:
                            ref_name = "The Main Product"
                        elif idx == 1 and has_background:
                            ref_name = "The Background Environment (CRITICAL)"
                        elif idx == 2 or (idx == 1 and not has_background):
                            ref_name = "The Optional Product" if "product_image" in img_type else "The Face"
                        else:
                            ref_name = "The Face"
                        logger.info(f"      [{idx+1}] {ref_name}: {img_type}")
                    
                    # Legacy: keep init_image_url for backward compatibility (first image in array)
                    init_image_url = init_image_urls[0] if len(init_image_urls) > 0 else None
                    
                    if not init_image_url or len(init_image_urls) == 0:
                        raise HTTPException(
                            status_code=422,
                            detail="Invalid image format. Please provide valid base64 encoded image."
                        )
                    
                    logger.info(f"✅ Total {len(uploaded_images)} image(s) uploaded to Supabase Storage")
                    logger.info(f"   Sending {len(init_image_urls)} image(s) to Fal.ai for generation:")
                    for idx, url in enumerate(init_image_urls):
                        img_type = next((img["type"] for img in uploaded_images if img["url"] == url), "unknown")
                        logger.info(f"      [{idx+1}] {img_type}: {url[:80]}...")
                    logger.info(f"   Image-to-image pipeline: Using {len(init_image_urls)} reference image(s)")
                    upload_elapsed = time.perf_counter() - start_time
                    logger.info(f"⏱️ Upload + preprocess time: {upload_elapsed:.2f}s")
                    
                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"Failed to upload images to Supabase Storage: {str(e)}", exc_info=True)
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to upload image to Supabase Storage: {str(e)}. Image is required for image-to-image pipeline."
                    )
                
            except HTTPException:
                # Re-raise HTTPException (validation errors)
                raise
            except Exception as e:
                logger.error(f"Error parsing JSON request: {str(e)}", exc_info=True)
                raise HTTPException(status_code=422, detail=f"Invalid request format: {str(e)}")
        
        # Image-to-image pipeline - init_image_urls is REQUIRED at this point
        if not init_image_urls or len(init_image_urls) == 0:
            raise HTTPException(
                status_code=500,
                detail="Internal error: Image URLs not available. This should not happen in image-to-image pipeline."
            )
        
        # ALWAYS use image-to-image mode and model (this is an image-to-image pipeline)
        generation_mode = "image-to-image"
        model_name = "fal-ai/flux-2/lora/edit"  # ALWAYS use image-to-image editing model (FLUX.2 [dev])
        
        logger.info(f"Generating images for user {user_id} using Fal.ai {model_name} ({generation_mode} mode). Current coins: {coins}")
        logger.info(f"📝 FINAL PROMPT YANG DIKIRIM KE FAL.AI (IMAGE-TO-IMAGE PIPELINE):")
        logger.info(f"   Model: {model_name} (IMAGE-TO-IMAGE PIPELINE)")
        logger.info(f"   Mode: {generation_mode} (REQUIRED)")
        logger.info(f"   Steps: 24 (INFERENCE, BUKAN training), CFG: 4.5, Image Strength: 0.67 (natural and realistic)")
        logger.info(f"   Image Strength: 0.4 (FIXED: menjaga identitas wajah)")
        logger.info(f"   Image URL: {init_image_url} (REQUIRED)")
        logger.info(f"   Prompt: {prompt_to_use}")
        logger.info(f"   Prompt length: {len(prompt_to_use)} chars")
        logger.info(f"   Init image URL: YES (REQUIRED for image-to-image pipeline)")
        logger.info(f"   ==========================================")
        
        # Save prompt to file for debugging
        try:
            from debug_prompt_log import save_prompt_log
            fal_request_data = {
                "model": model_name,
                "prompt": prompt_to_use,
                "num_inference_steps": 24,
                "guidance_scale": 4.5
            }
            # Image-to-image pipeline - always include image_urls (array) and image_strength
            fal_request_data["image_strength"] = 0.67
            fal_request_data["image_urls"] = init_image_urls  # flux-2/lora/edit menggunakan image_urls (array) - REQUIRED
            
            save_prompt_log(
                request_data={
                    "prompt": prompt_to_use,
                    "image_url": init_image_url,  # Primary image URL for Fal.ai generation
                    "all_uploaded_images": uploaded_images,  # All uploaded image URLs
                    "primary_image_type": primary_image_type,  # Type of primary image
                    "request_format": "multipart/form-data" if "multipart/form-data" in content_type else "application/json",
                    "has_image_url": True  # Always True in image-to-image pipeline
                },
                enhanced_prompt=prompt_to_use,
                fal_request=fal_request_data
            )
            logger.info(f"💾 Prompt saved to debug_prompt_log.json for debugging")
        except Exception as e:
            logger.warning(f"Failed to save prompt log: {str(e)}")
        
        # Generate images dengan init_image_urls (image-to-image pipeline - REQUIRED)
        # Use init_image_urls (multiple images array) - flux-2/lora/edit supports up to 3 images
        # Use Fal.ai parameters from request (if provided), otherwise use defaults: image_strength=0.67, num_inference_steps=24, guidance_scale=4.5 (natural and realistic)
        # Lower image strength (0.4) for identity preservation: face, fabric, color
        fal_start = time.perf_counter()
        image_urls = await fal_generate_images(
            prompt_to_use, 
            num_images=1, 
            init_image_urls=init_image_urls,
            image_strength=fal_image_strength if fal_image_strength is not None else 0.67,
            num_inference_steps=fal_num_inference_steps if fal_num_inference_steps is not None else 24,
            guidance_scale=fal_guidance_scale if fal_guidance_scale is not None else 4.5,
            negative_prompt=fal_negative_prompt,
            aspect_ratio=aspect_ratio
        )
        fal_elapsed = time.perf_counter() - fal_start
        logger.info(f"⏱️ Fal.ai call time: {fal_elapsed:.2f}s")
        
        # Only reduce coins if generation was successful (no exception raised)
        # Reduce coins_balance by 75 after successful generation
        logger.info(f"Images generated successfully. Reducing coins by {image_batch_cost} for user {user_id}")
        updated_profile = update_user_coins(user_id, -image_batch_cost)
        remaining_coins = updated_profile.get("coins_balance", 0) if updated_profile else coins - image_batch_cost
        logger.info(f"Coins deducted. Remaining coins for user {user_id}: {remaining_coins}")
        
        # Include prompt in response for debugging (user bisa lihat di browser dev tools -> Network tab)
        response_data = {
            "images": image_urls,
            "remaining_coins": remaining_coins
        }
        
        # Log debug info server-side only (no UI exposure)
        try:
            logger.info(
                "Fal.ai debug info: model=%s mode=%s steps=%s guidance=%s strength=%s pipeline=%s format=%s prompt_len=%s image_url=%s",
                model_name,
                generation_mode,
                24,
                4.5,
                0.67,
                "image-to-image",
                "multipart/form-data" if "multipart/form-data" in content_type else "application/json",
                len(prompt_to_use),
                init_image_url
            )
        except Exception as e:
            logger.warning(f"Failed to log Fal.ai debug info: {str(e)}")
        
        total_elapsed = time.perf_counter() - start_time
        logger.info(f"⏱️ Total generate-image time: {total_elapsed:.2f}s")
        return response_data
    except HTTPException:
        raise
    except ValueError as e:
        # Check if it's a Supabase table error
        error_msg = str(e)
        if "tidak ditemukan" in error_msg.lower() or "not found" in error_msg.lower() or "PGRST205" in error_msg:
            raise HTTPException(
                status_code=500,
                detail=f"Database configuration error: {error_msg}. Please run setup.sql in Supabase SQL Editor."
            )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error generating images: {str(error_msg)}", exc_info=True)
        
        # Check for Supabase table errors
        if "PGRST205" in error_msg or "could not find the table" in error_msg.lower():
            raise HTTPException(
                status_code=500,
                detail="Tabel 'profiles' tidak ditemukan di Supabase. Silakan jalankan setup.sql di Supabase SQL Editor dan refresh schema cache."
            )
        
        raise HTTPException(status_code=500, detail=f"Server error: {error_msg}")


@app.post("/api/create-video")
async def create_video(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create 3 TikTok-ready videos from a single image (same as batch).
    Converts static image to 5-second MP4s with cinematic motion.
    
    Request body:
    {
        "image_url": "https://...",  # URL of generated image
        "category": "Fashion",        # Optional: Product category
        "model_character": "female",  # Optional
        "model_type": "Wanita"        # Optional
    }
    
    Returns:
    {
        "videos": [
            {
                "video_url": "https://...",
                "preset_name": "Elegant Zoom",
                "file_size_mb": 1.5
            },
            ...
        ]
    }
    """
    # For consistency: always return 3 videos from a single image
    return await create_videos_batch(request, current_user)


@app.post("/api/create-videos-batch")
async def create_videos_batch(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create 3 TikTok-ready videos from generated image based on product category.
    Each category has 3 different fake motion variations.
    
    Request body:
    {
        "image_url": "https://...",  # URL of generated image
        "category": "Fashion"  # Product category (Fashion, Beauty, Tas, etc.)
    }
    
    Returns:
    {
        "videos": [
            {
                "video_url": "https://...",
                "preset_name": "Elegant Zoom",
                "file_size_mb": 1.5
            },
            ...
        ]  # 3 videos with different fake motion
    }
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # Check FFmpeg availability
        if not check_ffmpeg_available():
            raise HTTPException(
                status_code=503,
                detail="Video generation service unavailable. FFmpeg is not installed."
            )
        
        # Parse request body
        body = await request.json()
        image_url = body.get("image_url")
        category = body.get("category", "Fashion")
        model_character = body.get("model_character")  # Optional: female, male, child, etc.
        model_type = body.get("model_type")  # Optional: Pria, Wanita, etc.
        
        if not image_url:
            raise HTTPException(status_code=400, detail="image_url is required")
        
        logger.info(f"Creating 3 videos for user {user_id}")
        logger.info(f"Image URL: {image_url}")
        logger.info(f"Category: {category}")
        logger.info(f"Model type: {model_type}, Character: {model_character}")
        
        # Download image temporarily to check for human face and detect product region
        import tempfile
        import httpx
        from pathlib import Path
        
        temp_dir = tempfile.mkdtemp()
        temp_image_path = None
        has_face = False
        product_region = None
        final_focus_y = None
        
        try:
            # Download image to check for face and detect product region
            logger.info("Downloading image to check for human face and detect product region...")
            response = httpx.get(image_url, timeout=30)
            response.raise_for_status()
            
            image_ext = Path(image_url).suffix or '.jpg'
            if image_ext not in ['.jpg', '.jpeg', '.png', '.webp']:
                image_ext = '.jpg'
            
            temp_image_path = os.path.join(temp_dir, f"check_face{image_ext}")
            with open(temp_image_path, 'wb') as f:
                f.write(response.content)
            
            # Check for human face
            has_face = has_human_face(temp_image_path)
            logger.info(f"Face detection result: {'HUMAN FACE DETECTED' if has_face else 'NO HUMAN FACE'}")
            
            # Detect product region if no face (for non-human images)
            if not has_face:
                product_region = detect_product_region(temp_image_path)
                logger.info(f"Product region detected: center=({product_region['center_x']:.2f}, {product_region['center_y']:.2f})")

            # Lightweight focal point detection (used only for variation #3)
            image_focus_y = detect_focus_y_from_edges(temp_image_path)
            if image_focus_y is not None:
                category_bias_y = compute_category_bias_y(category, model_type, model_character)
                blended_focus_y = image_focus_y * 0.6 + category_bias_y * 0.4
                final_focus_y = max(0.25, min(0.75, blended_focus_y))
                logger.info(
                    f"Focus Y: image={image_focus_y:.2f} bias={category_bias_y:.2f} final={final_focus_y:.2f}"
                )
            
        except Exception as e:
            logger.warning(f"Failed to check for face/detect product region, using defaults: {str(e)}")
            has_face = False
            product_region = None
        
        videos = []
        temp_files = []
        duration_seconds = 15.0
        fps = 60
        total_frames = max(1, int(duration_seconds * fps) - 1)
        
        try:
            # Get motion variations based on category, face, and model character
            motion_variations = get_motion_variations(
                category=category,
                has_face=has_face,
                model_character=model_character or model_type,
                product_region=product_region
            )
            
            logger.info(f"Generated {len(motion_variations)} motion variations")
            if len(motion_variations) < 3:
                logger.warning(f"⚠️ Only {len(motion_variations)} motion variations generated, expected 3!")
            for idx, mv in enumerate(motion_variations):
                logger.info(f"  Motion {idx + 1}: {mv.get('name', 'Unknown')} - {mv.get('motion_type', 'Unknown')}")
            if len(motion_variations) < 3:
                logger.warning(f"⚠️ Only {len(motion_variations)} motion variations generated, expected 3!")
            for idx, mv in enumerate(motion_variations):
                logger.info(f"  Motion {idx + 1}: {mv.get('name', 'Unknown')} - {mv.get('motion_type', 'Unknown')}")
            
            if has_face:
                # HUMAN FACE DETECTED: Use the same cinematic FFmpeg pipeline (no alpha overlays)
                logger.info("Using CINEMATIC FFmpeg pipeline for human images (no alpha overlays)")

                for motion_index, motion_config in enumerate(motion_variations[:3]):
                    try:
                        logger.info(f"Creating cinematic video {motion_index + 1}/3 for human image")

                        use_focus = (motion_index == 2 and final_focus_y is not None)
                        is_variation_2 = motion_index == 1
                        zoom_expr_override = None
                        x_expr_override = None
                        y_expr_override = None
                        apply_zoom_boost = True
                        rotate_override = motion_config.get('rotate', 0.0)

                        if is_variation_2:
                            # Linear zoom 1.00 -> 1.05 across full duration (no sin/cos)
                            zoom_speed = 0.05 / total_frames
                            zoom_expr_override = f"1+{zoom_speed:.8f}*on"

                            category_lower = (category or "").strip().lower()
                            center_x = "iw/2-(iw/zoom/2)"
                            center_y = "ih/2-(ih/zoom/2)"
                            if "shoe" in category_lower or "sepatu" in category_lower or "sandal" in category_lower or "footwear" in category_lower:
                                x_expr_override = center_x
                                y_expr_override = f"{center_y}-0.03*ih*on/{total_frames}"
                            elif "bag" in category_lower or "tas" in category_lower:
                                x_expr_override = center_x
                                y_expr_override = f"{center_y}+0.03*ih*on/{total_frames}"
                            elif "accessor" in category_lower or "small" in category_lower:
                                x_expr_override = f"{center_x}+0.02*iw*on/{total_frames}"
                                y_expr_override = f"{center_y}+0.02*ih*on/{total_frames}"
                            elif "apparel" in category_lower or "model" in category_lower or "fashion" in category_lower:
                                x_expr_override = f"{center_x}+0.03*iw*on/{total_frames}"
                                y_expr_override = center_y
                            else:
                                x_expr_override = f"{center_x}+0.03*iw*on/{total_frames}"
                                y_expr_override = center_y

                            apply_zoom_boost = False
                            rotate_override = 0.0

                        try:
                            video_path = await create_video_from_url(
                                image_url=image_url,
                                output_filename=f"video_{user_id}_human_{motion_index}_{int(os.urandom(4).hex(), 16)}",
                                duration=duration_seconds,
                                zoom_start=motion_config.get('zoom_start', 1.0),
                                zoom_end=motion_config.get('zoom_end', 1.08),
                                zoom_speed=motion_config.get('zoom_speed', 0.0015),
                                pan_x=motion_config.get('pan_x', 0.0),
                                pan_y=motion_config.get('pan_y', 0.0),
                                pan_speed=motion_config.get('pan_speed', 0.0),
                                rotate=rotate_override,
                                focus_x=0.5 if use_focus else None,
                                focus_y=final_focus_y if use_focus else None,
                                zoom_expr_override=zoom_expr_override,
                                x_expr_override=x_expr_override,
                                y_expr_override=y_expr_override,
                                apply_zoom_boost=apply_zoom_boost
                            )
                        except Exception as focus_error:
                            if use_focus:
                                logger.warning(f"Variation 3 focus failed, retrying centered: {focus_error}")
                                video_path = await create_video_from_url(
                                    image_url=image_url,
                                    output_filename=f"video_{user_id}_human_{motion_index}_{int(os.urandom(4).hex(), 16)}",
                                    duration=duration_seconds,
                                    zoom_start=motion_config.get('zoom_start', 1.0),
                                    zoom_end=motion_config.get('zoom_end', 1.08),
                                    zoom_speed=motion_config.get('zoom_speed', 0.0015),
                                    pan_x=motion_config.get('pan_x', 0.0),
                                    pan_y=motion_config.get('pan_y', 0.0),
                                    pan_speed=motion_config.get('pan_speed', 0.0),
                                    rotate=rotate_override,
                                focus_x=None,
                                focus_y=None,
                                    zoom_expr_override=zoom_expr_override if is_variation_2 else None,
                                    x_expr_override=x_expr_override if is_variation_2 else None,
                                    y_expr_override=y_expr_override if is_variation_2 else None,
                                    apply_zoom_boost=apply_zoom_boost
                                )
                            else:
                                raise

                        temp_files.append(video_path)

                        video_filename = os.path.basename(video_path)
                        with open(video_path, 'rb') as video_file:
                            video_bytes = video_file.read()
                            video_size_mb = len(video_bytes) / (1024 * 1024)

                            video_url = upload_image_to_supabase_storage(
                                file_content=video_bytes,
                                file_name=video_filename,
                                bucket_name="IMAGES_UPLOAD",
                                user_id=user_id,
                                category="videos"
                            )

                            videos.append({
                                "video_url": video_url,
                                "preset_name": motion_config.get('name', f"Variation {motion_index + 1}"),
                                "file_size_mb": round(video_size_mb, 2),
                                "description": motion_config.get('description', 'Cinematic motion'),
                                "type": "standard"
                            })

                            logger.info(f"✅ Cinematic video {motion_index + 1}/3 uploaded: {video_url} ({video_size_mb:.2f} MB)")

                    except Exception as video_error:
                        logger.error(f"Failed to create cinematic video {motion_index + 1}/3: {str(video_error)}")
                        continue
                        
            else:
                # NO HUMAN FACE: Use dynamic motion variations with product focus
                logger.info("Using DYNAMIC motion variations (no face, product-focused)")
                
                # Get text presets for category (for hook/CTA text)
                presets = get_video_presets(category)
                logger.info(f"Using {len(presets)} presets for category '{category}'")
                
                # CRITICAL: Ensure we have exactly 3 motion variations
                logger.info(f"Motion variations before validation: {len(motion_variations)}")
                if len(motion_variations) < 3:
                    logger.warning(f"⚠️ Only {len(motion_variations)} motion variations received, expected 3!")
                    logger.warning(f"⚠️ Motion variation names: {[mv.get('name', 'Unknown') for mv in motion_variations]}")
                    # Duplicate last config to reach 3
                    while len(motion_variations) < 3:
                        last_config = motion_variations[-1].copy()
                        last_config['name'] = f"{last_config.get('name', 'Variation')} (Copy {len(motion_variations) + 1})"
                        motion_variations.append(last_config)
                    logger.info(f"✅ Extended motion variations to {len(motion_variations)}")
                
                # Generate 3 videos with different motion variations
                logger.info(f"Starting video generation loop with {len(motion_variations)} motion configs")
                for motion_index, motion_config in enumerate(motion_variations):
                    if motion_index >= 3:
                        logger.warning(f"⚠️ Skipping motion config {motion_index + 1} (only generating 3 videos)")
                        break
                    try:
                        preset = presets[motion_index] if motion_index < len(presets) else presets[0]
                        logger.info(f"🎬 [VIDEO {motion_index + 1}/3] Starting: {motion_config['name']}")
                        logger.info(f"   Motion config: zoom={motion_config.get('zoom_start', 1.0)}→{motion_config.get('zoom_end', 1.08)}, pan=({motion_config.get('pan_x', 0.0)}, {motion_config.get('pan_y', 0.0)})")
                        
                        # Create video with dynamic motion configuration
                        logger.info(f"   Step 1/3: Calling create_video_from_url...")
                        use_focus = (motion_index == 2 and final_focus_y is not None)
                        is_variation_2 = motion_index == 1
                        zoom_expr_override = None
                        x_expr_override = None
                        y_expr_override = None
                        apply_zoom_boost = True
                        rotate_override = motion_config.get('rotate', 0.0)

                        if is_variation_2:
                            zoom_speed = 0.05 / total_frames
                            zoom_expr_override = f"1+{zoom_speed:.8f}*on"

                            category_lower = (category or "").strip().lower()
                            center_x = "iw/2-(iw/zoom/2)"
                            center_y = "ih/2-(ih/zoom/2)"
                            if "shoe" in category_lower or "sepatu" in category_lower or "sandal" in category_lower or "footwear" in category_lower:
                                x_expr_override = center_x
                                y_expr_override = f"{center_y}-0.03*ih*on/{total_frames}"
                            elif "bag" in category_lower or "tas" in category_lower:
                                x_expr_override = center_x
                                y_expr_override = f"{center_y}+0.03*ih*on/{total_frames}"
                            elif "accessor" in category_lower or "small" in category_lower:
                                x_expr_override = f"{center_x}+0.02*iw*on/{total_frames}"
                                y_expr_override = f"{center_y}+0.02*ih*on/{total_frames}"
                            elif "apparel" in category_lower or "model" in category_lower or "fashion" in category_lower:
                                x_expr_override = f"{center_x}+0.03*iw*on/{total_frames}"
                                y_expr_override = center_y
                            else:
                                x_expr_override = f"{center_x}+0.03*iw*on/{total_frames}"
                                y_expr_override = center_y

                            apply_zoom_boost = False
                            rotate_override = 0.0

                        try:
                            video_path = await create_video_from_url(
                                image_url=image_url,
                                hook_text=preset['hook_text'],
                                cta_text=preset['cta_text'],
                                output_filename=f"video_{user_id}_{motion_index}_{int(os.urandom(4).hex(), 16)}",
                                duration=duration_seconds,
                                zoom_start=motion_config['zoom_start'],
                                zoom_end=motion_config['zoom_end'],
                                zoom_speed=motion_config['zoom_speed'],
                                hook_position=preset['hook_position'],
                                hook_timing=preset['hook_timing'],
                                cta_position=preset['cta_position'],
                                cta_timing=preset['cta_timing'],
                                pan_x=motion_config.get('pan_x', 0.0),
                                pan_y=motion_config.get('pan_y', 0.0),
                                pan_speed=motion_config.get('pan_speed', 0.0),
                                rotate=rotate_override,
                                focus_x=0.5 if use_focus else None,
                                focus_y=final_focus_y if use_focus else None,
                                zoom_expr_override=zoom_expr_override,
                                x_expr_override=x_expr_override,
                                y_expr_override=y_expr_override,
                                apply_zoom_boost=apply_zoom_boost
                            )
                        except Exception as focus_error:
                            if use_focus:
                                logger.warning(f"Variation 3 focus failed, retrying centered: {focus_error}")
                                video_path = await create_video_from_url(
                                    image_url=image_url,
                                    hook_text=preset['hook_text'],
                                    cta_text=preset['cta_text'],
                                    output_filename=f"video_{user_id}_{motion_index}_{int(os.urandom(4).hex(), 16)}",
                                    duration=duration_seconds,
                                    zoom_start=motion_config['zoom_start'],
                                    zoom_end=motion_config['zoom_end'],
                                    zoom_speed=motion_config['zoom_speed'],
                                    hook_position=preset['hook_position'],
                                    hook_timing=preset['hook_timing'],
                                    cta_position=preset['cta_position'],
                                    cta_timing=preset['cta_timing'],
                                    pan_x=motion_config.get('pan_x', 0.0),
                                    pan_y=motion_config.get('pan_y', 0.0),
                                    pan_speed=motion_config.get('pan_speed', 0.0),
                                    rotate=rotate_override,
                                focus_x=None,
                                focus_y=None,
                                    zoom_expr_override=zoom_expr_override if is_variation_2 else None,
                                    x_expr_override=x_expr_override if is_variation_2 else None,
                                    y_expr_override=y_expr_override if is_variation_2 else None,
                                    apply_zoom_boost=apply_zoom_boost
                                )
                            else:
                                raise
                        
                        temp_files.append(video_path)
                        
                        # Upload video to Supabase Storage (file_path-based for lower memory)
                        video_filename = os.path.basename(video_path)
                        with open(video_path, 'rb') as video_file:
                            video_bytes = video_file.read()
                            video_size_mb = len(video_bytes) / (1024 * 1024)
                            
                            video_url = upload_image_to_supabase_storage(
                                file_content=video_bytes,
                                file_name=video_filename,
                                bucket_name="IMAGES_UPLOAD",  # Using same bucket for now
                                user_id=user_id,
                                category="videos"
                            )
                            
                            logger.info(f"   ✅ Step 2/3: Uploaded to Supabase: {video_url[:50]}...")
                            
                            videos.append({
                                "video_url": video_url,
                                "preset_name": motion_config['name'],
                                "file_size_mb": round(video_size_mb, 2),
                                "description": motion_config.get('description', preset.get('description', '')),
                                "type": "standard"
                            })
                            
                            logger.info(f"   ✅ Step 3/3: Added to videos array")
                            logger.info(f"✅ [VIDEO {motion_index + 1}/3] COMPLETE: {motion_config['name']} → {video_url[:50]}... ({video_size_mb:.2f} MB)")
                            
                    except Exception as video_error:
                        logger.error(f"❌ [VIDEO {motion_index + 1}/3] FAILED: {str(video_error)}", exc_info=True)
                        logger.error(f"   Error type: {type(video_error).__name__}")
                        logger.error(f"   Motion config that failed: {motion_config.get('name', 'Unknown')}")
                        # Continue with other videos even if one fails
                        continue
            
            # Clean up temporary files
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temp file {temp_file}: {cleanup_error}")
            
            # Clean up temp directory
            try:
                if temp_files:
                    temp_dir = os.path.dirname(temp_files[0])
                    if os.path.exists(temp_dir):
                        os.rmdir(temp_dir)
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temp directory: {cleanup_error}")
            
            # Return videos even if not all 3 were created (partial success is better than complete failure)
            if len(videos) == 0:
                logger.error("❌ CRITICAL: No videos were created successfully!")
                logger.error(f"   Motion variations count: {len(motion_variations)}")
                logger.error(f"   Temp files created: {len(temp_files)}")
                raise HTTPException(status_code=500, detail="Failed to create any videos. Please check server logs for details.")
            
            logger.info(f"✅ Successfully created {len(videos)}/3 videos for user {user_id}")
            if len(videos) < 3:
                logger.warning(f"⚠️ Only {len(videos)}/3 videos were created successfully. Some videos may have failed.")
                logger.warning(f"⚠️ This is a partial success - returning {len(videos)} video(s) instead of failing completely.")
            for idx, video in enumerate(videos):
                logger.info(f"  Video {idx + 1}: {video.get('preset_name', 'Unknown')} - {video.get('video_url', 'No URL')[:50]}...")
            
            return JSONResponse(content={
                "videos": videos,
                "category": category,
                "total_videos": len(videos),
                "has_human_face": has_face,
                "video_type": "human_safe" if has_face else "standard"
            })
            
        except Exception as batch_error:
            # Clean up any remaining temp files
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except:
                    pass
            raise batch_error
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating videos batch: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create videos: {str(e)}")


@app.post("/api/create-kling-video")
async def create_kling_video(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in token")
        profile = get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        coins = profile.get("coins_balance", 0)
        pro_video_cost = 185
        if coins < pro_video_cost:
            raise HTTPException(
                status_code=403,
                detail="Insufficient coins. You need at least 185 coins to generate a Pro Video. Please top up."
            )
        body = await request.json()
        image_url = body.get("image_url")
        prompt = body.get("prompt") or "A cinematic product showcase with subtle camera movement and realistic lighting."
        negative_prompt = body.get("negative_prompt")
        if not image_url:
            raise HTTPException(status_code=400, detail="image_url is required")
        video_url = await fal_generate_kling_video(prompt, image_url, negative_prompt)
        updated_profile = update_user_coins(user_id, -pro_video_cost)
        remaining_coins = updated_profile.get("coins_balance", 0) if updated_profile else coins - pro_video_cost
        return {"video_url": video_url, "remaining_coins": remaining_coins}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating Kling video: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Server error: Gagal membuat video")


@app.post("/api/generate-video-saas")
async def generate_video_saas(
    request: GenerateVideoRequestSaaS,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Generate video using Fal.ai kling-v2/video-generation
    Costs 5 coins from coins_balance
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in token")
        
        # Check user profile and coins
        profile = get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        coins = profile.get("coins_balance", 0)
        if coins < 5:
            raise HTTPException(
                status_code=403,
                detail="Insufficient coins. You need 5 coins to generate a video. Please top up."
            )
        
        # Generate video using Fal.ai
        video_url = await fal_generate_video(request.prompt, request.image_url)
        
        # Deduct 5 coins
        update_user_coins(user_id, -5)
        
        return {
            "video_url": video_url,
            "remaining_coins": coins - 5
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating video: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

class CreateMidtransTransactionRequest(BaseModel):
    package_id: str
    order_id: str
    gross_amount: float
    user_id: str


MIDTRANS_COIN_PACKAGES = {
    "package-10k": {"price": 10000, "coins": 300},
    "package-50k": {"price": 50000, "coins": 1500},
    "package-100k": {"price": 100000, "coins": 3200},
    "package-150k": {"price": 150000, "coins": 5000},
    "package-200k": {"price": 200000, "coins": 6800},
    "package-250k": {"price": 250000, "coins": 8850},
}

@app.post("/api/midtrans/create-transaction")
async def create_midtrans_transaction(
    request: CreateMidtransTransactionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create Midtrans Snap transaction
    Returns snap_token for frontend
    """
    try:
        import hashlib
        import hmac
        
        # Verify user matches
        if current_user.get("id") != request.user_id:
            raise HTTPException(status_code=403, detail="User ID mismatch")
        
        MIDTRANS_SERVER_KEY = os.getenv('MIDTRANS_SERVER_KEY')
        MIDTRANS_CLIENT_KEY = os.getenv('MIDTRANS_CLIENT_KEY')
        MIDTRANS_IS_PRODUCTION = os.getenv('MIDTRANS_IS_PRODUCTION', 'false').lower() == 'true'
        
        if not MIDTRANS_SERVER_KEY or not MIDTRANS_CLIENT_KEY:
            raise HTTPException(status_code=500, detail="Midtrans credentials not configured")
        
        package_data = MIDTRANS_COIN_PACKAGES.get(request.package_id)
        if not package_data:
            raise HTTPException(status_code=400, detail="Invalid package_id")

        # Create transaction data
        transaction_data = {
            "transaction_details": {
                "order_id": request.order_id,
                "gross_amount": int(package_data["price"])
            },
            "customer_details": {
                "user_id": request.user_id
            },
            "custom_field1": request.user_id,
            "custom_field2": request.package_id,
            "item_details": [
                {
                    "id": request.package_id,
                    "price": int(package_data["price"]),
                    "quantity": 1,
                    "name": f"Coin Package - {request.package_id}"
                }
            ]
        }
        
        # Call Midtrans API to create transaction
        midtrans_url = "https://app.midtrans.com/snap/v1/transactions" if MIDTRANS_IS_PRODUCTION else "https://app.sandbox.midtrans.com/snap/v1/transactions"
        
        auth_string = base64.b64encode(f"{MIDTRANS_SERVER_KEY}:".encode()).decode()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                midtrans_url,
                headers={
                    "Authorization": f"Basic {auth_string}",
                    "Content-Type": "application/json"
                },
                json=transaction_data
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "snap_token": result.get("token"),
                "order_id": request.order_id
            }
    except httpx.HTTPStatusError as e:
        logger.error(f"Midtrans API error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=500, detail=f"Failed to create transaction: {e.response.text}")
    except Exception as e:
        logger.error(f"Error creating Midtrans transaction: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/webhook/midtrans")
async def midtrans_webhook(request: Request):
    """
    Handle Midtrans payment webhook
    Updates coins_balance when payment is successful
    """
    try:
        body = await request.json()
        transaction_status = body.get("transaction_status")
        order_id = body.get("order_id")
        gross_amount = body.get("gross_amount")
        status_code = body.get("status_code")
        signature_key = body.get("signature_key")
        fraud_status = body.get("fraud_status")
        user_id = body.get("custom_field1") or body.get("user_id")
        package_id = body.get("custom_field2")

        if not order_id or not gross_amount or not status_code:
            raise HTTPException(status_code=400, detail="Invalid webhook payload")

        MIDTRANS_SERVER_KEY = os.getenv('MIDTRANS_SERVER_KEY')
        if not MIDTRANS_SERVER_KEY:
            raise HTTPException(status_code=500, detail="Midtrans server key not configured")

        if not signature_key:
            raise HTTPException(status_code=400, detail="Missing signature_key")

        signature_payload = f"{order_id}{status_code}{gross_amount}{MIDTRANS_SERVER_KEY}"
        expected_signature = hashlib.sha512(signature_payload.encode()).hexdigest()
        if signature_key != expected_signature:
            raise HTTPException(status_code=403, detail="Invalid signature")

        # Verify transaction status
        if transaction_status != "settlement" and transaction_status != "capture":
            logger.info(f"Transaction {order_id} status: {transaction_status} - not processing")
            return {"status": "ignored", "message": "Transaction not settled"}
        
        # Verify fraud status
        if fraud_status and fraud_status != "accept":
            logger.warning(f"Transaction {order_id} has fraud status: {fraud_status}")
            return {"status": "rejected", "message": "Fraud check failed"}
        
        # Extract user_id from order_id (format: "coins-{user_id}-{timestamp}")
        # Or use custom field if provided
        if not user_id:
            # Try to extract from order_id
            if order_id.startswith("coins-"):
                parts = order_id.split("-")
                if len(parts) >= 2:
                    user_id = parts[1]
        
        if not user_id:
            logger.error(f"Could not extract user_id from order_id: {order_id}")
            raise HTTPException(status_code=400, detail="User ID not found in order")
        
        # Calculate coins based on gross_amount
        try:
            gross_amount_value = int(float(gross_amount))
        except ValueError:
            logger.error(f"Invalid gross_amount: {gross_amount}")
            raise HTTPException(status_code=400, detail="Invalid payment amount")

        coins_to_add = None
        for package in MIDTRANS_COIN_PACKAGES.values():
            if package["price"] == gross_amount_value:
                coins_to_add = package["coins"]
                break

        if coins_to_add is None:
            logger.error(f"Unsupported gross_amount: {gross_amount_value}")
            raise HTTPException(status_code=400, detail="Unsupported payment amount")
        
        # Update user coins
        update_user_coins(user_id, coins_to_add)

        # Log transaction to Supabase
        try:
            insert_midtrans_transaction_log({
                "user_id": user_id,
                "order_id": order_id,
                "package_id": package_id,
                "gross_amount": gross_amount_value,
                "coins_added": coins_to_add,
                "transaction_status": transaction_status,
                "payment_type": body.get("payment_type"),
                "fraud_status": fraud_status,
                "midtrans_signature": signature_key,
                "raw_payload": body
            })
        except Exception:
            logger.warning("Failed to log Midtrans transaction to Supabase", exc_info=True)
        
        logger.info(f"Added {coins_to_add} coins to user {user_id} from transaction {order_id}")
        
        return {
            "status": "success",
            "coins_added": coins_to_add,
            "user_id": user_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Midtrans webhook: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/midtrans/status")
async def admin_midtrans_status(
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    Admin-only endpoint to validate Midtrans config at runtime.
    """
    midtrans_server_key = os.getenv('MIDTRANS_SERVER_KEY')
    midtrans_client_key = os.getenv('MIDTRANS_CLIENT_KEY')
    midtrans_is_production = os.getenv('MIDTRANS_IS_PRODUCTION', 'false').lower() == 'true'
    return {
        "midtrans_is_production": midtrans_is_production,
        "server_key_configured": bool(midtrans_server_key),
        "client_key_configured": bool(midtrans_client_key),
        "packages": MIDTRANS_COIN_PACKAGES
    }

# ==================== AutoPost Dashboard & Queue ====================

class AutopostTaskUpdateRequest(BaseModel):
    status: str
    error: Optional[str] = None


def _recheck_due_videos(conn: sqlite3.Connection, user_id: str) -> int:
    now = _now_iso()
    rows = conn.execute(
        """
        SELECT * FROM autopost_videos
        WHERE user_id = ? AND status = 'WAITING_RECHECK'
          AND next_check_at IS NOT NULL AND next_check_at <= ?
        ORDER BY next_check_at ASC
        """,
        (user_id, now)
    ).fetchall()
    updated = 0
    for row in rows:
        previous_details = {}
        try:
            previous_details = json.loads(row["score_details"] or "{}")
        except Exception:
            previous_details = {}
        scene_signals = previous_details.get("scene_signals")
        if not scene_signals and row.get("file_path"):
            scene_signals = _get_scene_signals(row["file_path"])
        details = _score_video_metadata(
            row["title"],
            row["caption"],
            row["hook_text"],
            row["cta_text"],
            row["hashtags"],
            row["category"],
            user_id,
            scene_signals
        )
        score = float(details.get("score", 0.0))
        threshold = _adjust_threshold_with_feedback(
            row["threshold"] or DEFAULT_AUTPOST_THRESHOLD,
            details.get("feedback") or {},
            float(details.get("trend_similarity") or 0.0)
        )
        details["threshold"] = threshold
        _log_score_details(f"user={user_id} video_id={row['id']}", details)
        compliance_blocked = bool(details.get("compliance_blocked"))
        if compliance_blocked:
            _update_autopost_record(
                conn,
                row["id"],
                status="WAITING_RECHECK",
                score=score,
                score_details=json.dumps(details),
                next_check_at=_schedule_next_check(),
                threshold=threshold
            )
        elif score >= threshold:
            _update_autopost_record(
                conn,
                row["id"],
                status="QUEUED",
                score=score,
                score_details=json.dumps(details),
                next_check_at=None,
                threshold=threshold
            )
        else:
            _update_autopost_record(
                conn,
                row["id"],
                status="WAITING_RECHECK",
                score=score,
                score_details=json.dumps(details),
                next_check_at=_schedule_next_check(),
                threshold=threshold
            )
        updated += 1
    if updated:
        conn.commit()
    return updated


@app.post("/api/autopost/upload")
async def autopost_upload_video(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    caption: Optional[str] = Form(None),
    hook_text: Optional[str] = Form(None),
    cta_text: Optional[str] = Form(None),
    hashtags: Optional[str] = Form(None),
    category: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID not found in token")
        _enforce_rate_limit(user_id)
        profile = get_user_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        coins = profile.get("coins_balance", 0)
        autopost_upload_cost = 90
        if coins < autopost_upload_cost:
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "INSUFFICIENT_COINS",
                    "required_coins": autopost_upload_cost,
                    "action": "topup",
                    "message": "Coins kamu tidak cukup."
                }
            )
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")

        file_ext = Path(file.filename).suffix or ".mp4"
        safe_name = f"{user_id}_{int(datetime.now().timestamp())}_{os.urandom(4).hex()}{file_ext}"
        file_path = AUTPOST_TEMP_DIR / safe_name

        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        scene_signals = _get_scene_signals(str(file_path))
        details = _score_video_metadata(
            title,
            caption,
            hook_text,
            cta_text,
            hashtags,
            category,
            user_id,
            scene_signals
        )
        score = float(details.get("score", 0.0))
        threshold = _adjust_threshold_with_feedback(
            DEFAULT_AUTPOST_THRESHOLD,
            details.get("feedback") or {},
            float(details.get("trend_similarity") or 0.0)
        )
        details["threshold"] = threshold
        _log_score_details(f"user={user_id} video={file.filename}", details)
        compliance_blocked = bool(details.get("compliance_blocked"))
        if compliance_blocked:
            status = "WAITING_RECHECK"
            next_check_at = _schedule_next_check()
        else:
            status = "QUEUED" if score >= threshold else "WAITING_RECHECK"
            next_check_at = None if status == "QUEUED" else _schedule_next_check()

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO autopost_videos
            (user_id, file_name, file_path, title, caption, hook_text, cta_text, hashtags, category,
             status, score, score_details, threshold, next_check_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                file.filename,
                str(file_path),
                title,
                caption,
                hook_text,
                cta_text,
                hashtags,
                category,
                status,
                score,
                json.dumps(details),
                threshold,
                next_check_at,
                _now_iso(),
                _now_iso()
            )
        )
        record_id = cursor.lastrowid
        conn.commit()
        record_id = cursor.lastrowid
        updated_profile = update_user_coins(user_id, -autopost_upload_cost)
        remaining_coins = updated_profile.get("coins_balance", 0) if updated_profile else coins - autopost_upload_cost

        if AUTPOST_SCENE_PROVIDER != "none" and background_tasks is not None:
            background_tasks.add_task(_async_scene_analysis, record_id, str(file_path), user_id)
        conn.close()

        response_payload = {
            "id": record_id,
            "status": status,
            "score": score,
            "threshold": threshold,
            "next_check_at": next_check_at,
            "remaining_coins": remaining_coins
        }
        _cleanup_old_temp_videos()
        await _broadcast_autopost_event(
            user_id,
            "autopost.updated",
            {"id": record_id, "status": status, "score": score, "next_check_at": next_check_at, "video_name": file.filename}
        )
        return response_payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading autopost video: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to upload video")


@app.get("/api/autopost/dashboard")
async def autopost_dashboard(
    status: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found in token")

    conn = get_db_connection()
    _recheck_due_videos(conn, user_id)
    _cleanup_old_temp_videos()
    if status:
        rows = conn.execute(
            "SELECT * FROM autopost_videos WHERE user_id = ? AND status = ? ORDER BY created_at DESC",
            (user_id, status)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM autopost_videos WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
    conn.close()

    items = []
    for row in rows:
        item = dict(row)
        try:
            item["score_details"] = json.loads(item.get("score_details") or "{}")
        except Exception:
            item["score_details"] = {}
        item["video_name"] = item.get("file_name")
        item["credit_used"] = item.get("credit_used") if "credit_used" in item else 0
        items.append(item)
    return {"items": items}


@app.post("/api/autopost/recheck")
async def autopost_recheck(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found in token")
    conn = get_db_connection()
    updated = _recheck_due_videos(conn, user_id)
    conn.close()
    _cleanup_old_temp_videos()
    await _broadcast_autopost_event(user_id, "autopost.recheck", {"updated": updated})
    return {"updated": updated}


@app.get("/api/autopost/tasks/next")
async def autopost_next_task(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found in token")

    conn = get_db_connection()
    _recheck_due_videos(conn, user_id)
    row = conn.execute(
        "SELECT * FROM autopost_videos WHERE user_id = ? AND status = 'QUEUED' ORDER BY created_at ASC LIMIT 1",
        (user_id,)
    ).fetchone()
    if not row:
        conn.close()
        return {"task": None}

    _update_autopost_record(conn, row["id"], status="IN_PROGRESS")
    conn.commit()
    conn.close()

    return {
        "task": {
            "id": row["id"],
            "file_name": row["file_name"],
            "download_url": f"/api/autopost/video/{row['id']}",
            "title": row["title"],
            "caption": row["caption"],
            "hook_text": row["hook_text"],
            "cta_text": row["cta_text"],
            "hashtags": row["hashtags"],
            "category": row["category"],
            "score": row["score"]
        }
    }


@app.get("/api/autopost/video/{video_id}")
async def autopost_download_video(
    video_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found in token")

    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM autopost_videos WHERE id = ? AND user_id = ?",
        (video_id, user_id)
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Video not found")
    if not os.path.exists(row["file_path"]):
        raise HTTPException(status_code=404, detail="Video file not found")
    return FileResponse(row["file_path"], filename=row["file_name"])


@app.post("/api/autopost/tasks/{video_id}/complete")
async def autopost_complete_task(
    video_id: int,
    payload: AutopostTaskUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found in token")

    status = payload.status.upper()
    if status not in ["POSTED", "FAILED"]:
        raise HTTPException(status_code=400, detail="Invalid status. Use POSTED or FAILED.")

    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM autopost_videos WHERE id = ? AND user_id = ?",
        (video_id, user_id)
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Video not found")

    _update_autopost_record(conn, video_id, status=status, error=payload.error)
    conn.commit()
    conn.close()

    # Cleanup file after POSTED or FAILED
    try:
        if row["file_path"] and os.path.exists(row["file_path"]):
            os.remove(row["file_path"])
    except Exception as cleanup_error:
        logger.warning(f"Failed to delete temp video {row['file_path']}: {cleanup_error}")

    await _broadcast_autopost_event(user_id, "autopost.updated", {"id": video_id, "status": status})
    return {"status": status}


@app.post("/api/autopost/tasks/{video_id}/retry")
async def autopost_retry_task(
    video_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found in token")

    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM autopost_videos WHERE id = ? AND user_id = ?",
        (video_id, user_id)
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Video not found")

    _update_autopost_record(conn, video_id, status="QUEUED", error=None)
    conn.commit()
    conn.close()
    await _broadcast_autopost_event(user_id, "autopost.updated", {"id": video_id, "status": "QUEUED"})
    return {"status": "QUEUED"}


@app.post("/api/autopost/metrics")
async def autopost_metrics(
    payload: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found in token")
    normalized = _normalize_metrics_payload(payload)
    video_id = normalized.get("video_id")
    if not video_id:
        raise HTTPException(status_code=400, detail="video_id is required")
    views = int(normalized.get("views", 0))
    likes = int(normalized.get("likes", 0))
    comments = int(normalized.get("comments", 0))
    shares = int(normalized.get("shares", 0))
    avg_watch_time = normalized.get("avg_watch_time")
    retention_curve = normalized.get("retention_curve")
    posted_at = normalized.get("posted_at")

    conn = get_db_connection()
    conn.execute(
        """
        INSERT INTO autopost_metrics
        (user_id, video_id, views, likes, comments, shares, avg_watch_time, retention_curve, posted_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            int(video_id),
            views,
            likes,
            comments,
            shares,
            avg_watch_time,
            json.dumps(retention_curve) if retention_curve is not None else None,
            posted_at,
            _now_iso()
        )
    )
    conn.commit()
    conn.close()
    await _broadcast_autopost_event(user_id, "autopost.metrics", {"video_id": video_id})
    return {"status": "ok"}


@app.get("/api/autopost/insights")
async def autopost_insights(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found in token")
    conn = get_db_connection()
    video_rows = conn.execute(
        "SELECT * FROM autopost_videos WHERE user_id = ? ORDER BY created_at DESC LIMIT 30",
        (user_id,)
    ).fetchall()
    metric_rows = conn.execute(
        "SELECT * FROM autopost_metrics WHERE user_id = ? ORDER BY created_at DESC LIMIT 50",
        (user_id,)
    ).fetchall()
    conn.close()

    fatigue_alerts = _detect_pattern_fatigue(video_rows)
    scores = [float(r["score"]) for r in video_rows if r["score"] is not None]
    trend_decay = _trend_decay(scores)

    curves: List[List[float]] = []
    hours: Dict[int, List[float]] = {}
    for row in metric_rows:
        if row["retention_curve"]:
            try:
                curves.append(json.loads(row["retention_curve"]))
            except Exception:
                pass
        posted_at = row["posted_at"]
        if posted_at:
            try:
                hour = datetime.fromisoformat(posted_at).hour
                rate = _compute_engagement_rate(row["views"], row["likes"], row["comments"], row["shares"])
                hours.setdefault(hour, []).append(rate)
            except Exception:
                pass
    retention_summary = _summarize_retention(curves)
    best_times = []
    for hour, rates in hours.items():
        if rates:
            best_times.append({"hour": hour, "engagement_rate": round(sum(rates) / len(rates), 4)})
    best_times.sort(key=lambda x: x["engagement_rate"], reverse=True)

    recommendations = []
    if fatigue_alerts:
        recommendations.append("Variasikan hook/CTA yang sering dipakai.")
    if trend_decay.get("status") == "declining":
        recommendations.append("Coba hashtag tren baru atau format hook berbeda.")
    if retention_summary.get("dropoff_second") is not None:
        recommendations.append("Perkuat hook sebelum detik drop-off.")

    return {
        "fatigue_alerts": fatigue_alerts,
        "trend_decay": trend_decay,
        "retention_summary": retention_summary,
        "best_times": best_times[:3],
        "recommendations": recommendations
    }


@app.post("/api/autopost/caption/check")
async def caption_check(
    payload: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    caption = (payload.get("caption") or "").strip()
    hashtags = re.findall(r"#\w+", caption)
    issues = []
    if len(caption) > 140:
        issues.append("Caption terlalu panjang.")
    if len(hashtags) > 6:
        issues.append("Hashtag terlalu banyak.")
    if "komen" not in caption.lower() and "comment" not in caption.lower():
        issues.append("CTA komentar belum ada.")
    return {"issues": issues}


@app.post("/api/autopost/tasks/{video_id}/retry-variant")
async def autopost_retry_variant(
    video_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID not found in token")
    conn = get_db_connection()
    row = conn.execute(
        "SELECT * FROM autopost_videos WHERE id = ? AND user_id = ?",
        (video_id, user_id)
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Video not found")
    templates = _get_engagement_templates(row["category"])
    new_hook = templates["hooks"][0] if templates["hooks"] else row["hook_text"]
    new_cta = templates["ctas"][0] if templates["ctas"] else row["cta_text"]
    _update_autopost_record(conn, video_id, status="QUEUED", hook_text=new_hook, cta_text=new_cta, error=None)
    conn.commit()
    conn.close()
    await _broadcast_autopost_event(user_id, "autopost.updated", {"id": video_id, "status": "QUEUED"})
    return {"status": "QUEUED", "hook_text": new_hook, "cta_text": new_cta}


@app.get("/api/autopost/competitors")
async def list_competitors(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    user_id = current_user.get("id")
    conn = get_db_connection()
    rows = conn.execute(
        "SELECT * FROM autopost_competitors WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    ).fetchall()
    conn.close()
    return {"items": [dict(r) for r in rows]}


@app.post("/api/autopost/competitors")
async def add_competitor(
    payload: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    user_id = current_user.get("id")
    title = (payload.get("title") or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="title is required")
    url = payload.get("url")
    notes = payload.get("notes")
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO autopost_competitors (user_id, title, url, notes, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, title, url, notes, _now_iso())
    )
    conn.commit()
    conn.close()
    return {"status": "ok"}


@app.get("/api/autopost/templates")
async def autopost_templates(
    category: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    _ = current_user.get("id")
    return _get_engagement_templates(category)


@app.post("/api/admin/trends/upload")
async def admin_upload_trends(
    file: UploadFile = File(...),
    _: Dict[str, Any] = Depends(require_admin)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    content = await file.read()
    try:
        decoded = content.decode("utf-8")
    except Exception:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded")
    try:
        reader = csv.DictReader(decoded.splitlines())
        required = {"category", "hashtag", "weight"}
        if not reader.fieldnames or not required.issubset(set([h.strip() for h in reader.fieldnames])):
            raise HTTPException(status_code=400, detail="CSV schema invalid. Required columns: category, hashtag, weight")

        AUTPOST_IMPORT_STATUS.update({"status": "running", "processed": 0, "total": 0, "valid": 0, "invalid": 0, "errors": []})
        rows = list(reader)
        AUTPOST_IMPORT_STATUS["total"] = len(rows)
        errors: List[str] = []
        for idx, row in enumerate(rows, start=1):
            error = _validate_trend_row(row, idx)
            if error:
                errors.append(error)
            AUTPOST_IMPORT_STATUS["processed"] = idx
        AUTPOST_IMPORT_STATUS["invalid"] = len(errors)
        AUTPOST_IMPORT_STATUS["valid"] = max(0, AUTPOST_IMPORT_STATUS["total"] - AUTPOST_IMPORT_STATUS["invalid"])
        if errors:
            AUTPOST_IMPORT_STATUS.update({"status": "failed", "errors": errors})
            raise HTTPException(status_code=400, detail={"message": "CSV validation failed", "errors": errors})
    except HTTPException:
        AUTPOST_IMPORT_STATUS.update({"status": "failed"})
        raise
    except Exception as e:
        AUTPOST_IMPORT_STATUS.update({"status": "failed"})
        logger.error(f"CSV validation error: {e}")
        raise HTTPException(status_code=400, detail="CSV schema invalid")
    try:
        AUTPOST_TRENDS_CSV.write_bytes(content)
    except Exception as e:
        logger.error(f"Failed to save trends CSV: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save CSV")

    count = _refresh_trends_index()
    AUTPOST_IMPORT_STATUS.update({"status": "done", "processed": count, "valid": count, "invalid": 0})
    return {"status": "ok", "rows": count}


@app.post("/api/admin/trends/refresh")
async def admin_refresh_trends(
    _: Dict[str, Any] = Depends(require_admin)
):
    count = _refresh_trends_index()
    return {"status": "ok", "rows": count}


@app.get("/api/admin/trends/import-status")
async def admin_trends_import_status(
    _: Dict[str, Any] = Depends(require_admin)
):
    return AUTPOST_IMPORT_STATUS


@app.get("/api/admin/trends/categories")
async def admin_trends_categories(
    _: Dict[str, Any] = Depends(require_admin)
):
    labels = _category_label_map()
    categories = [{"value": c, "label": labels.get(c, c.title())} for c in _get_category_whitelist()]
    return {"categories": categories, "hashtag_regex": AUTPOST_HASHTAG_REGEX}


@app.get("/api/admin/trends/template")
async def admin_trends_template(
    _: Dict[str, Any] = Depends(require_admin)
):
    header = "category,hashtag,weight\n"
    sample = "fashion,#ootd,0.9\nbeauty,#skincare,0.8\n"
    content = header + sample
    return Response(content=content, media_type="text/csv")


@app.get("/api/admin/trends/export")
async def admin_trends_export(
    _: Dict[str, Any] = Depends(require_admin)
):
    rows = AUTPOST_TRENDS_INDEX.get("rows", [])
    output = ["category,hashtag,weight"]
    for row in rows:
        category = (row.get("category") or "").replace("\n", " ").strip()
        hashtag = (row.get("hashtag") or "").replace("\n", " ").strip()
        weight = row.get("weight")
        output.append(f"{category},{hashtag},{weight if weight is not None else ''}")
    content = "\n".join(output) + "\n"
    headers = {"Content-Disposition": "attachment; filename=trends_export.csv"}
    return Response(content=content, media_type="text/csv", headers=headers)


@app.get("/api/admin/trends/preview")
async def admin_preview_trends(
    _: Dict[str, Any] = Depends(require_admin)
):
    rows = AUTPOST_TRENDS_INDEX.get("rows", [])
    preview = [{"category": r.get("category"), "hashtag": r.get("hashtag"), "weight": r.get("weight")} for r in rows[:200]]
    return {"rows": preview, "total": len(rows)}


@app.get("/api/admin/trends")
async def admin_list_trends(
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    category: Optional[str] = None,
    _: Dict[str, Any] = Depends(require_admin)
):
    page = max(1, page)
    page_size = min(100, max(1, page_size))
    query = (search or "").strip()

    if AUTPOST_QDRANT_URL and (query or category):
        results = _search_qdrant_trends(query or " ", category, limit=page_size + (page - 1) * page_size)
        total = _qdrant_count(category) or len(results)
        start = (page - 1) * page_size
        page_rows = results[start:start + page_size]
        preview = [{"category": r.get("category"), "hashtag": r.get("hashtag"), "weight": r.get("weight")} for r in page_rows]
        return {"rows": preview, "total": total, "page": page, "page_size": page_size}

    rows = AUTPOST_TRENDS_INDEX.get("rows", [])
    query_lower = query.lower()
    if query_lower:
        rows = [
            r for r in rows
            if query_lower in (r.get("hashtag") or "").lower() or query_lower in (r.get("category") or "").lower()
        ]
    if category:
        rows = [r for r in rows if (r.get("category") or "").lower() == category.lower()]
    total = len(rows)
    start = (page - 1) * page_size
    end = start + page_size
    page_rows = rows[start:end]
    preview = [{"category": r.get("category"), "hashtag": r.get("hashtag"), "weight": r.get("weight")} for r in page_rows]
    return {"rows": preview, "total": total, "page": page, "page_size": page_size}


@app.get("/api/admin/status")
async def admin_status(current_user: Dict[str, Any] = Depends(get_current_user)):
    user_id = current_user.get("id")
    if not user_id:
        return {"is_admin": False}
    role = get_user_role_from_profile(user_id) or "user"
    return {"is_admin": role == "admin", "role": role}


@app.get("/api/debug/profile-status")
async def debug_profile_status(current_user: Dict[str, Any] = Depends(get_current_user_raw)):
    """Debug profile lookup for the current user."""
    user_id = current_user.get("id")
    email = current_user.get("email")
    profile = get_user_profile(user_id) if user_id else None
    return {
        "user_id": user_id,
        "email": email,
        "profile_found": profile is not None,
        "profile_user_id": profile.get("user_id") if profile else None,
        "profile_role": profile.get("role_user") if profile else None,
        "supabase_url": os.getenv("SUPABASE_URL", ""),
    }


@app.get("/api/admin/autopost/logs")
async def admin_autopost_logs(
    limit: int = 100,
    _: Dict[str, Any] = Depends(require_admin)
):
    """Admin-only: view recent autopost activity across users."""
    conn = get_db_connection()
    rows = conn.execute(
        """
        SELECT v.*,
               m.views, m.likes, m.comments, m.shares,
               m.avg_watch_time, m.retention_curve,
               m.created_at AS metrics_created_at
        FROM autopost_videos v
        LEFT JOIN autopost_metrics m
          ON m.video_id = v.id
         AND m.created_at = (
             SELECT MAX(created_at) FROM autopost_metrics
             WHERE video_id = v.id
         )
        ORDER BY v.created_at DESC
        LIMIT ?
        """,
        (max(1, min(limit, 500)),)
    ).fetchall()
    conn.close()

    items = []
    for row in rows:
        item = dict(row)
        try:
            item["score_details"] = json.loads(item.get("score_details") or "{}")
        except Exception:
            item["score_details"] = {}
        try:
            item["retention_curve"] = json.loads(item.get("retention_curve") or "[]")
        except Exception:
            item["retention_curve"] = []
        items.append(item)
    return {"items": items}


@app.websocket("/ws/autopost")
async def autopost_ws(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return
    user = verify_user_token(token)
    if not user or not user.get("id"):
        await websocket.close(code=1008)
        return

    user_id = user["id"]
    await websocket.accept()
    AUTPOST_WS_CONNECTIONS.setdefault(user_id, []).append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        connections = AUTPOST_WS_CONNECTIONS.get(user_id, [])
        AUTPOST_WS_CONNECTIONS[user_id] = [ws for ws in connections if ws is not websocket]

# ==================== Legacy Routes (Keep for backward compatibility) ====================

@app.post("/api/generate-image-legacy")
async def generate_image_proxy(request: ImageGenerationRequest):
    """Proxy endpoint to Node.js image generation service"""
    try:
        # Prepare request body for Node.js service
        body = {
            "prompt": request.prompt
        }
        
        if request.productImages:
            body["productImages"] = [
                {"base64": img.base64, "mimeType": img.mimeType}
                for img in request.productImages
            ]
        
        if request.faceImage:
            body["faceImage"] = {
                "base64": request.faceImage.base64,
                "mimeType": request.faceImage.mimeType
            }
        
        if request.backgroundImage:
            body["backgroundImage"] = {
                "base64": request.backgroundImage.base64,
                "mimeType": request.backgroundImage.mimeType
            }
        
        if request.images:
            body["images"] = [
                {"base64": img.base64, "mimeType": img.mimeType}
                for img in request.images
            ]
        
        # Call Node.js image service
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{IMAGE_SERVICE_URL}/generate-image",
                json=body
            )
            response.raise_for_status()
            return response.json()
    
    except httpx.HTTPError as e:
        logger.error(f"Error calling image service: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Image generation service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in generate_image_proxy: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Image generation failed")

@app.post("/api/generate-video-legacy")
async def generate_video(request: GenerateVideoRequest):
    """Generate a video from an image"""
    try:
        # Convert options to dict
        options = {
            "contentType": request.options.contentType,
            "interactionType": request.options.interactionType,
            "category": request.options.category,
            "aspectRatio": request.options.aspectRatio
        }
        
        # Use the new gemini_service function
        video_url = generate_product_video(
            request.image,
            options
        )
        
        return {"videoUrl": video_url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn  # type: ignore
    import sys
    
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except OSError as e:
        if e.errno == 10048:  # Windows: port already in use
            print("=" * 70)
            print("❌ ERROR: Port 8000 sudah digunakan oleh process lain!")
            print("=" * 70)
            print("\n📋 SOLUSI CEPAT:")
            print("1. Jalankan script fix otomatis:")
            print("   .\\fix_port_8000.ps1")
            print("\n2. Atau manual kill process:")
            print("   a. Cek process: netstat -ano | findstr :8000")
            print("   b. Kill process: taskkill /PID [PID] /F")
            print("\n3. Lalu jalankan server lagi:")
            print("   python main.py")
            print("=" * 70)
            sys.exit(1)
        else:
            # Re-raise other OSError
            raise

