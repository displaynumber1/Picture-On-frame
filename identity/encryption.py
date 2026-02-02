"""Encryption utilities for embeddings using AES-256 (Fernet)."""

from __future__ import annotations

import os
import threading
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken


_FERNET: Optional[Fernet] = None
_FERNET_LOCK = threading.Lock()


def _get_fernet() -> Fernet:
    """Return a singleton Fernet instance.

    Requires environment variable IDENTITY_EMBEDDING_KEY containing a
    URL-safe base64-encoded 32-byte key.
    """

    global _FERNET
    if _FERNET is None:
        with _FERNET_LOCK:
            if _FERNET is None:
                key = os.environ.get("IDENTITY_EMBEDDING_KEY")
                if not key:
                    raise RuntimeError("IDENTITY_EMBEDDING_KEY is not set.")
                _FERNET = Fernet(key.encode("utf-8"))
    return _FERNET


def encrypt_embedding(data: bytes) -> bytes:
    """Encrypt embedding bytes using Fernet.

    Args:
        data: Raw embedding bytes.

    Returns:
        Encrypted token bytes.
    """

    fernet = _get_fernet()
    return fernet.encrypt(data)


def decrypt_embedding(token: bytes) -> bytes:
    """Decrypt embedding bytes using Fernet.

    Args:
        token: Encrypted token bytes.

    Returns:
        Decrypted embedding bytes.

    Raises:
        InvalidToken: If the token is invalid or tampered.
    """

    fernet = _get_fernet()
    return fernet.decrypt(token)


__all__ = ["encrypt_embedding", "decrypt_embedding", "InvalidToken"]
