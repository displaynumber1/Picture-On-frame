import os
from pathlib import Path

from dotenv import load_dotenv  # type: ignore


def load_env() -> None:
    """
    Load environment variables for local dev without overriding existing env.

    Priority:
      1) backend/.env.local
      2) backend/config.env
      3) project root .env
    """
    keys = (
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_KEY",
        "FAL_KEY",
        "GEMINI_API_KEY",
    )
    if any(os.getenv(key) for key in keys):
        return
    for key in keys:
        if key in os.environ and os.environ.get(key) == "":
            del os.environ[key]

    backend_dir = Path(__file__).resolve().parents[2]
    repo_root = Path(__file__).resolve().parents[3]
    candidates = [
        backend_dir / ".env.local",
        backend_dir / "config.env",
        repo_root / "config.env",
        repo_root / ".env",
    ]
    for path in candidates:
        if path.exists():
            load_dotenv(path, override=False)
