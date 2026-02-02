import sys
import types

import numpy as np
from cryptography.fernet import Fernet


def _install_fake_insightface(monkeypatch) -> None:
    cv2_module = types.ModuleType("cv2")
    cv2_module.IMREAD_COLOR = 1
    cv2_module.imdecode = lambda *_args, **_kwargs: None
    monkeypatch.setitem(sys.modules, "cv2", cv2_module)

    insightface_module = types.ModuleType("insightface")
    insightface_app_module = types.ModuleType("insightface.app")

    class FaceAnalysis:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def prepare(self, *args, **kwargs) -> None:
            pass

        def get(self, _image):
            return []

    insightface_app_module.FaceAnalysis = FaceAnalysis
    monkeypatch.setitem(sys.modules, "insightface", insightface_module)
    monkeypatch.setitem(sys.modules, "insightface.app", insightface_app_module)


def test_refine_updates_version_and_normalizes(monkeypatch) -> None:
    _install_fake_insightface(monkeypatch)

    from identity import encryption, lifecycle

    key = Fernet.generate_key().decode("ascii")
    monkeypatch.setenv("IDENTITY_EMBEDDING_KEY", key)
    encryption._FERNET = None

    stored = np.ones(lifecycle.EMBEDDING_SIZE, dtype=np.float32)
    stored = stored / np.linalg.norm(stored)
    fresh = stored.copy()

    monkeypatch.setattr(lifecycle, "extract_embedding", lambda _img: fresh)

    stored_bytes = lifecycle._serialize_embedding(stored)
    stored_encrypted = encryption.encrypt_embedding(stored_bytes)

    result = lifecycle.refine(
        user_id="user-123",
        images=[b"image-bytes"],
        stored_embedding=stored_encrypted,
        avatar_version=1,
    )

    assert result.avatar_version == 2
    decrypted = encryption.decrypt_embedding(result.payload.encrypted_embedding)
    updated = lifecycle._deserialize_embedding(decrypted)
    assert np.isclose(np.linalg.norm(updated), 1.0, atol=1e-5)
