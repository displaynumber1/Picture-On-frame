## Runtime dependencies

Install the core runtime packages:

```
pip install "numpy>=1.24,<3" "cryptography>=41,<45" "insightface>=0.7,<0.8" "opencv-python>=4.8,<5"
```

Notes:
- `insightface` requires an ONNX runtime backend at runtime; follow the official docs for CPU-only installs if needed.
- Set `IDENTITY_EMBEDDING_KEY` with a URL-safe base64-encoded 32-byte key (Fernet). Generate via:
  `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`.

## Test dependencies

```
pip install "pytest>=7,<9" "pydantic>=1.10,<3"
```
