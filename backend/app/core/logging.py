import logging
import os
import sys
from pathlib import Path

from pythonjsonlogger import jsonlogger


def _resolve_log_dir() -> Path:
    configured = os.getenv("LOG_DIR")
    if configured:
        return Path(configured)
    # Default to backend/logs for cross-platform safety.
    return Path(__file__).resolve().parents[2] / "logs"


def setup_logging() -> None:
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )

    # Avoid duplicate handlers
    if logger.handlers:
        return

    log_dir = _resolve_log_dir()
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "app.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError:
        # Fallback to console-only if file logging isn't possible.
        pass

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
