# Testing /api/generate Endpoint

## Endpoint
**POST** `http://127.0.0.1:8000/api/generate`

## Error 422 - Validation Error

Error 422 biasanya terjadi karena:
1. **Field yang required tidak ada** - Semua field di `config` adalah required
2. **Field name case sensitive** - Gunakan camelCase (misalnya `productImage`, bukan `product_image`)
3. **Type data salah** - `productImage` harus string, bukan object

## Request Body yang Benar

Gunakan file `test_api_generate.json` atau copy format berikut:

```json
{
  "config": {
    "modelType": "Tanpa Model (Hanya Produk)",
    "category": "Fashion",
    "background": "Studio Putih",
    "pose": "Standing",
    "handInteraction": "Tanpa Interaksi",
    "style": "Professional",
    "lighting": "Natural",
    "aspectRatio": "1:1",
    "angle": "Front",
    "additionalPrompt": "",
    "customBackgroundPrompt": "",
    "customPosePrompt": "",
    "customStylePrompt": "",
    "customLightingPrompt": ""
  },
  "productImage": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
  "faceImage": null,
  "customBgImage": null
}
```

## Testing di FastAPI Docs

1. Buka `http://127.0.0.1:8000/docs`
2. Cari endpoint `/api/generate`
3. Klik "Try it out"
4. Klik "Example" untuk melihat contoh request
5. Edit request body sesuai kebutuhan
6. Klik "Execute"

## Common Mistakes

### ❌ Salah: Field name dengan underscore
```json
{
  "product_image": "..."  // ❌ Salah
}
```

### ✅ Benar: Field name camelCase
```json
{
  "productImage": "..."  // ✅ Benar
}
```

### ❌ Salah: Missing required field
```json
{
  "config": {
    "modelType": "...",
    // Missing: category, background, pose, etc.
  }
}
```

### ✅ Benar: Semua field required ada
```json
{
  "config": {
    "modelType": "...",
    "category": "...",
    "background": "...",
    "pose": "...",
    "handInteraction": "...",
    "style": "...",
    "lighting": "...",
    "aspectRatio": "...",
    "angle": "...",
    "additionalPrompt": "",
    "customBackgroundPrompt": "",
    "customPosePrompt": "",
    "customStylePrompt": "",
    "customLightingPrompt": ""
  }
}
```

## Response

Success (200):
```json
[
  {
    "url": "data:image/png;base64,...",
    "videoPrompt": "GROK VIDEO PROMPT (6 SECONDS)..."
  },
  ...
]
```

Error 422:
```json
{
  "detail": [
    {
      "loc": ["body", "config", "category"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

Error ini menunjukkan field mana yang missing atau salah.

