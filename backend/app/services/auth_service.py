import os
import time
from typing import Any, Dict, Optional, Tuple

import httpx

SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").strip()
SUPABASE_ANON_KEY = (os.getenv("SUPABASE_ANON_KEY") or "").strip()

CACHE_TTL_SECONDS = int(os.getenv("AUTH_TOKEN_CACHE_TTL_SECONDS", "60"))

# token -> (expires_at_epoch, user_json)
_token_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}


def extract_bearer_token(authorization: Optional[str]) -> str:
    if not authorization:
        raise ValueError("missing_authorization")

    parts = authorization.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
        raise ValueError("invalid_authorization_format")

    return parts[1].strip()


async def verify_user_token(token: str) -> Optional[Dict[str, Any]]:
    now = time.time()

    cached = _token_cache.get(token)
    if cached:
        exp, user = cached
        if now < exp:
            return user
        _token_cache.pop(token, None)

    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return None

    url = f"{SUPABASE_URL}/auth/v1/user"
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": SUPABASE_ANON_KEY,
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(url, headers=headers)

        if r.status_code != 200:
            return None

        user = r.json()
        _token_cache[token] = (now + CACHE_TTL_SECONDS, user)
        return user
    except Exception:
        return None
