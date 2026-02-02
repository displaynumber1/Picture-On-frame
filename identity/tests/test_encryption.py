from cryptography.fernet import Fernet

from identity import encryption


def test_encrypt_decrypt_roundtrip(monkeypatch) -> None:
    key = Fernet.generate_key().decode("ascii")
    monkeypatch.setenv("IDENTITY_EMBEDDING_KEY", key)
    encryption._FERNET = None

    payload = b"embedding-bytes"
    token = encryption.encrypt_embedding(payload)
    decrypted = encryption.decrypt_embedding(token)

    assert decrypted == payload
