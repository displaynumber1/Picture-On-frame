import pytest
import httpx

from generation_adapters.fal.fal_client import FalClient


class _DummyResponse:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200

    def json(self):
        return self._payload

    def raise_for_status(self) -> None:
        return None


@pytest.mark.asyncio
async def test_fal_client_async_call_builds_request(monkeypatch) -> None:
    captured = {}

    class DummyAsyncClient:
        def __init__(self, timeout):
            captured["timeout"] = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, url, json, headers):
            captured["url"] = url
            captured["json"] = json
            captured["headers"] = headers
            return _DummyResponse({"ok": True})

    monkeypatch.setenv("FAL_KEY", "test-key")
    monkeypatch.setattr(httpx, "AsyncClient", DummyAsyncClient)

    client = FalClient()
    payload = {"prompt": "hello"}
    result = await client.call("fal-ai/ip-adapter-face-id", payload)

    assert result == {"ok": True}
    assert captured["url"] == "https://fal.run/fal-ai/ip-adapter-face-id"
    assert captured["json"] == payload
    assert captured["headers"]["Authorization"] == "Key test-key"


def test_fal_client_sync_call_builds_request(monkeypatch) -> None:
    captured = {}

    class DummyClient:
        def __init__(self, timeout):
            captured["timeout"] = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def post(self, url, json, headers):
            captured["url"] = url
            captured["json"] = json
            captured["headers"] = headers
            return _DummyResponse({"ok": True})

    monkeypatch.setenv("FAL_KEY", "test-key")
    monkeypatch.setattr(httpx, "Client", DummyClient)

    client = FalClient()
    payload = {"prompt": "hello"}
    result = client.call_sync("fal-ai/ip-adapter-face-id", payload)

    assert result == {"ok": True}
    assert captured["url"] == "https://fal.run/fal-ai/ip-adapter-face-id"
    assert captured["json"] == payload
    assert captured["headers"]["Authorization"] == "Key test-key"
