import os
import sys
import tempfile
from typing import Optional

import httpx


BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
AUTH_TOKEN = os.getenv("TEST_AUTH_TOKEN")
RUN_LARGE_UPLOAD = os.getenv("RUN_LARGE_UPLOAD_TEST", "0") == "1"
RUN_RATE_LIMIT = os.getenv("RUN_RATE_LIMIT_TEST", "0") == "1"

MAX_UPLOAD_BYTES = 150 * 1024 * 1024


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {AUTH_TOKEN}"} if AUTH_TOKEN else {}


def test_health(client: httpx.Client) -> None:
    resp = client.get("/health")
    _assert(resp.status_code == 200, f"/health status {resp.status_code}")
    data = resp.json()
    _assert(data.get("status") == "ok", "/health status field missing")
    _assert("service" in data, "/health service missing")
    _assert("ts" in data, "/health ts missing")


def test_ready(client: httpx.Client) -> None:
    resp = client.get("/ready")
    _assert(resp.status_code in {200, 503}, f"/ready status {resp.status_code}")
    data = resp.json()
    _assert("status" in data, "/ready status missing")
    _assert("checks" in data, "/ready checks missing")
    _assert("ts" in data, "/ready ts missing")
    checks = data.get("checks", {})
    _assert("db" in checks, "/ready db check missing")
    _assert("supabase_env" in checks, "/ready supabase_env check missing")
    _assert("ffmpeg" in checks, "/ready ffmpeg check missing")


def test_request_id_header(client: httpx.Client) -> None:
    request_id = "test-req-123"
    resp = client.get("/health", headers={"X-Request-ID": request_id})
    _assert(resp.headers.get("X-Request-ID") == request_id, "X-Request-ID header mismatch")


def test_validation_error(client: httpx.Client) -> None:
    if not AUTH_TOKEN:
        print("Skipping validation error test (TEST_AUTH_TOKEN not set)")
        return
    resp = client.post(
        "/api/generate-video-saas",
        headers=_auth_headers(),
        json={"prompt": 123}  # invalid payload to trigger validation error
    )
    _assert(resp.status_code == 422, f"Validation error status {resp.status_code}")
    data = resp.json()
    err = data.get("error") or {}
    _assert(err.get("code") == 422, "Validation error code missing")
    _assert("request_id" in err, "Validation error missing request_id")


def test_upload_size_limit(client: httpx.Client) -> None:
    if not AUTH_TOKEN or not RUN_LARGE_UPLOAD:
        print("Skipping upload size test (set TEST_AUTH_TOKEN and RUN_LARGE_UPLOAD_TEST=1)")
        return
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.seek(MAX_UPLOAD_BYTES)
        tmp.write(b"x")
        tmp.flush()
        tmp_path = tmp.name
    with open(tmp_path, "rb") as handle:
        files = {"file": ("large.mp4", handle, "video/mp4")}
        resp = client.post("/api/autopost/upload", headers=_auth_headers(), files=files)
    _assert(resp.status_code == 413, f"Upload size status {resp.status_code}")


def test_rate_limit(client: httpx.Client) -> None:
    if not AUTH_TOKEN or not RUN_RATE_LIMIT:
        print("Skipping rate limit test (set TEST_AUTH_TOKEN and RUN_RATE_LIMIT_TEST=1)")
        return
    payload = {
        "prompt": "test",
        "image_url": "https://example.com/image.png"
    }
    for _ in range(40):
        resp = client.post("/api/generate-video-saas", headers=_auth_headers(), json=payload)
        if resp.status_code == 429:
            break
    _assert(resp.status_code == 429, "Expected rate limit 429 not reached")


def main() -> None:
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        test_health(client)
        test_ready(client)
        test_request_id_header(client)
        test_validation_error(client)
        test_upload_size_limit(client)
        test_rate_limit(client)
    print("Smoke checks completed")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Smoke checks failed: {exc}")
        sys.exit(1)
