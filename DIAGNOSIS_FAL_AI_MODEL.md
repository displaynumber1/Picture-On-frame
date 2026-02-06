# Diagnosis: Model fal yang Digunakan

## 📊 Hasil Analisa dari Log Terakhir

### Log Terakhir (Text-to-Image Mode):

```json
{
  "timestamp": "2026-01-11T06:35:30.766926",
  "generation_mode": "text-to-image",
  "model": "fal-ai/flux/schnell",
  "payload": {
    "prompt": "A Woman model, for Fashion, in Mirror selfie using iPhone pose...",
    "num_inference_steps": 7,
    "guidance_scale": 3.5,
    "image_size": "square_hd"
  }
}
```

### ✅ Status: BENAR untuk Text-to-Image

Karena **TIDAK ada image upload**, sistem menggunakan:
- ✅ Model: `fal-ai/flux/schnell` (text-to-image fallback)
- ✅ Generation Mode: `text-to-image`
- ✅ Parameter: Sesuai requirement (`num_inference_steps: 7`, `guidance_scale: 3.5`)

**Ini adalah behavior yang BENAR** karena model `fal-ai/flux-general/image-to-image` hanya digunakan saat ada image upload.

## 🎯 Model Baru: `fal-ai/flux-general/image-to-image`

### Kapan Model Ini Digunakan?

Model `fal-ai/flux-general/image-to-image` digunakan **HANYA** jika:
- ✅ User mengupload image (face_image, product_image, atau background_image)
- ✅ Image berhasil di-upload ke Supabase Storage
- ✅ `init_image_url` tidak `None`

### Payload yang Diharapkan (Image-to-Image):

```json
{
  "prompt": "A Woman model, for Fashion...",
  "image_url": "https://...supabase.co/storage/v1/object/public/public/user_id/uuid.jpg",
  "image_strength": 0.5,
  "num_inference_steps": 7,
  "guidance_scale": 3.5,
  "loras": []  // Optional
}
```

**Endpoint:** `POST https://fal.run/fal-ai/flux-general/image-to-image`

### Payload yang Diharapkan (Text-to-Image):

```json
{
  "prompt": "A Woman model, for Fashion...",
  "image_size": "square_hd",
  "num_inference_steps": 7,
  "guidance_scale": 3.5
}
```

**Endpoint:** `POST https://fal.run/fal-ai/flux/schnell`

## ✅ Verifikasi Implementasi di Code

### 1. `backend/fal_service.py`

✅ **Model Endpoint:**
```python
FAL_MODEL_ENDPOINT_IMAGE_TO_IMAGE = "fal-ai/flux-general/image-to-image"  # ✅ BENAR
FAL_MODEL_ENDPOINT_TEXT_TO_IMAGE = "fal-ai/flux/schnell"  # ✅ BENAR
```

✅ **Parameter Locked:**
```python
FAL_IMAGE_STRENGTH = 0.5  # ✅ BENAR (untuk menjaga identitas wajah)
FAL_NUM_INFERENCE_STEPS = 7  # ✅ BENAR (INFERENCE, BUKAN training)
FAL_GUIDANCE_SCALE = 3.5  # ✅ BENAR (prompt adherence tanpa merusak wajah)
```

✅ **Payload Building:**
```python
if use_image_to_image and init_image_url:
    request_payload = {
        "prompt": prompt,
        "image_url": init_image_url,  # ✅ SINGULAR (bukan array)
        "image_strength": FAL_IMAGE_STRENGTH,  # ✅ 0.5
        "num_inference_steps": FAL_NUM_INFERENCE_STEPS,  # ✅ 7
        "guidance_scale": FAL_GUIDANCE_SCALE  # ✅ 3.5
    }
    # Optional LoRA
    if loras and len(loras) > 0:
        request_payload["loras"] = loras  # ✅ Optional LoRA support
```

### 2. `backend/main.py`

✅ **Model Selection:**
```python
model_name = "fal-ai/flux-general/image-to-image" if init_image_url else "fal-ai/flux/schnell"  # ✅ BENAR
```

✅ **Payload Logging:**
```python
if init_image_url:
    fal_request_data["image_strength"] = 0.5  # ✅ BENAR
    fal_request_data["image_url"] = init_image_url  # ✅ SINGULAR
```

## 🔍 Cara Melihat Payload Lengkap yang Dikirim ke fal

### Method 1: Via Backend Terminal Logs (Paling Lengkap)

Saat generate batch dengan image upload, cek terminal backend:

```
INFO: ======================================================================
INFO: GENERATION SUMMARY:
INFO: ======================================================================
INFO: Generation Mode: image-to-image  ← Harus ini jika ada image
INFO: Model: fal-ai/flux-general/image-to-image  ← Harus ini jika ada image
INFO: Init Image URL: YES  ← Harus YES jika ada image
INFO: ======================================================================

INFO: Sending image-to-image request to fal for image 1/2
INFO:    Model: fal-ai/flux-general/image-to-image
INFO:    ✅ Image-to-image: Using image_url from Supabase Storage
INFO:    📤 Image URL yang dikirim: https://...supabase.co/...
INFO:    Model: fal-ai/flux-general/image-to-image (support LoRA)
INFO:    Image Strength: 0.5 (FIXED: menjaga identitas wajah)
INFO:    Inference Steps: 7 (FIXED: INFERENCE, BUKAN training)
INFO:    Guidance Scale: 3.5 (FIXED: prompt adherence tanpa merusak wajah)
INFO:    📤 FULL REQUEST PAYLOAD ke fal:
INFO:    {
INFO:      "prompt": "A Woman model, for Fashion...",
INFO:      "image_url": "https://...supabase.co/...",
INFO:      "image_strength": 0.5,
INFO:      "num_inference_steps": 7,
INFO:      "guidance_scale": 3.5
INFO:    }
```

### Method 2: Via Script Python

```bash
cd backend
python -c "from debug_prompt_log import get_latest_prompt_log; import json; log = get_latest_prompt_log(); print(json.dumps(log, indent=2, ensure_ascii=False))"
```

### Method 3: Via Browser Dev Tools

1. F12 → **Network** tab
2. Filter: `generate-image`
3. Klik request → **Response** tab
4. Lihat `debug_info` → ini payload yang dikirim ke fal

### Method 4: Via Debug Endpoint

```bash
GET http://localhost:8000/api/debug/last-prompt
```

## ⚠️ Test dengan Image Upload Diperlukan

Untuk memverifikasi model `fal-ai/flux-general/image-to-image` bekerja:

1. **Upload image** di frontend (face_image, product_image, atau background_image)
2. **Generate batch**
3. **Cek log backend** - harus ada:
   - `Generation Mode: image-to-image`
   - `Model: fal-ai/flux-general/image-to-image`
   - `Init Image URL: YES`
   - Payload dengan `image_url` dan `image_strength: 0.5`

## 📋 Checklist Verifikasi

### Untuk Text-to-Image (tanpa image):
- ✅ Model: `fal-ai/flux/schnell`
- ✅ Payload: `image_size`, `num_inference_steps: 7`, `guidance_scale: 3.5`
- ✅ Endpoint: `https://fal.run/fal-ai/flux/schnell`

### Untuk Image-to-Image (dengan image):
- ✅ Model: `fal-ai/flux-general/image-to-image`
- ✅ Payload: `image_url` (singular), `image_strength: 0.5`, `num_inference_steps: 7`, `guidance_scale: 3.5`
- ✅ Endpoint: `https://fal.run/fal-ai/flux-general/image-to-image`
- ✅ Optional: `loras` array (jika ada)

## 🎯 Kesimpulan

### Status Implementasi: ✅ SUDAH BENAR

1. ✅ Model `fal-ai/flux-general/image-to-image` sudah diimplementasikan di code
2. ✅ Parameter sudah locked sesuai requirement
3. ✅ Log terakhir menggunakan `fal-ai/flux/schnell` karena **TIDAK ada image upload** (ini BENAR)
4. ⚠️ **Perlu test dengan image upload** untuk memverifikasi model baru bekerja

### Action Items

1. **Test dengan image upload** untuk memverifikasi model `fal-ai/flux-general/image-to-image`
2. **Cek log backend** setelah generate dengan image upload
3. **Verify payload** mengandung:
   - `image_url` (singular, bukan array)
   - `image_strength: 0.5`
   - `num_inference_steps: 7`
   - `guidance_scale: 3.5`
   - Model: `fal-ai/flux-general/image-to-image`

---

**Silakan test dengan image upload dan share log backend untuk verifikasi lebih lanjut!**
