"""fal client wrapper with async support and timeouts."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import httpx


class FalError(RuntimeError):
    """Raised when fal API call fails."""


class FalClient:
    """Minimal fal client wrapper."""

    def __init__(self, api_key: Optional[str] = None, timeout_s: float = 30.0) -> None:
        self.api_key = api_key or os.environ.get("FAL_KEY")
        if not self.api_key:
            raise RuntimeError("FAL_KEY is not set.")
        self.timeout = httpx.Timeout(timeout_s)
        self.base_url = "https://fal.run"

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Key {self.api_key}"}

    async def call(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Perform an async POST call to fal."""

        url = f"{self.base_url}/{endpoint}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=self._headers())
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException as exc:
            raise FalError("fal request timed out.") from exc
        except httpx.HTTPStatusError as exc:
            raise FalError(
                f"fal request failed with status {exc.response.status_code}."
            ) from exc
        except httpx.HTTPError as exc:
            raise FalError("fal request failed.") from exc

    def call_sync(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a synchronous POST call to fal."""

        url = f"{self.base_url}/{endpoint}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload, headers=self._headers())
                response.raise_for_status()
                return response.json()
        except httpx.TimeoutException as exc:
            raise FalError("fal request timed out.") from exc
        except httpx.HTTPStatusError as exc:
            raise FalError(
                f"fal request failed with status {exc.response.status_code}."
            ) from exc
        except httpx.HTTPError as exc:
            raise FalError("fal request failed.") from exc
