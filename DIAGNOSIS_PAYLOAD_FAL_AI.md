# Diagnosis: Payload yang Dikirim Backend ke Fal.ai

## 📊 Analisa Log Terakhir

### ✅ Status: Code SUDAH BENAR, Tapi Belum Test dengan Image Upload

Dari analisa `prompt_log.json`:

### Entry Terakhir (Tanpa Image Upload):
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
  },
  "request": {
    "has_product_images": false,
    "has_face_image": false,
    "has_background_image": false,
    "has_image_url": false,
    "image_url": null
  }
}
```

**✅ Ini BENAR** karena tidak ada image upload, jadi menggunakan `fal-ai/flux/schnell` (text-to-image fallback).

### Entry Pertama (Dengan Image Upload - Model LAMA):
```json
{
  "timestamp": "2026-01-11T02:41:48.528629",
  "model": "fal-ai/flux-1.1/image-to-image",  // ❌ MODEL LAMA (sebelum update)
  "payload": {
    "strength": 0.65,  // ❌ PARAMETER LAMA (bukan image_strength: 0.5)
    "num_inference_steps": 7,
    "guidance_scale": 3.5
  },
  "request": {
    "has_product_images": true,  // ✅ Ada image upload
    "has_face_image": true,
    "has_background_image": true
  }
}
```

**⚠️ Ini adalah log LAMA** (sebelum update ke `fal-ai/flux-general/image-to-image`).

## 🎯 Payload yang Dikirim Backend ke Fal.ai (SETELAH UPDATE)

### 1. Text-to-Image Mode (Tanpa Image Upload)

**Endpoint:** `POST https://fal.run/fal-ai/flux/schnell`

**Payload:**
```json
{
  "prompt": "A Woman model, for Fashion, in Mirror selfie using iPhone pose, in Studio Clean style, with Natural Daylight lighting, shot from Eye-Level angle, in 9:16 aspect ratio, photorealistic resolusi HD",
  "image_size": "square_hd",
  "num_inference_steps": 7,
  "guidance_scale": 3.5
}
```

**✅ Status:** SUDAH BENAR (sesuai log terakhir)

### 2. Image-to-Image Mode (Dengan Image Upload) - EXPECTED

**Endpoint:** `POST https://fal.run/fal-ai/flux-general/image-to-image`

**Payload yang Diharapkan:**
```json
{
  "prompt": "A Woman model, for Fashion, in Mirror selfie using iPhone pose, in Studio Clean style, with Natural Daylight lighting, shot from Eye-Level angle, in 9:16 aspect ratio, photorealistic resolusi HD",
  "image_url": "https://your-project.supabase.co/storage/v1/object/public/public/user_id/uuid.jpg",
  "image_strength": 0.5,
  "num_inference_steps": 7,
  "guidance_scale": 3.5,
  "loras": []  // Optional - jika ada LoRA IDs
}
```

**⚠️ Status:** BELUM ADA TEST (perlu test dengan image upload)

## ✅ Verifikasi Implementasi di Code

### 1. Model Selection (`backend/main.py`):

```python
model_name = "fal-ai/flux-general/image-to-image" if init_image_url else "fal-ai/flux/schnell"
```

✅ **SUDAH BENAR**

### 2. Payload Building (`backend/fal_service.py`):

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
        request_payload["loras"] = loras
```

✅ **SUDAH BENAR**

### 3. Constants (`backend/fal_service.py`):

```python
FAL_MODEL_ENDPOINT_IMAGE_TO_IMAGE = "fal-ai/flux-general/image-to-image"  # ✅ BENAR
FAL_IMAGE_STRENGTH = 0.5  # ✅ BENAR (untuk menjaga identitas wajah)
FAL_NUM_INFERENCE_STEPS = 7  # ✅ BENAR (INFERENCE, BUKAN training)
FAL_GUIDANCE_SCALE = 3.5  # ✅ BENAR (prompt adherence tanpa merusak wajah)
```

✅ **SUDAH BENAR**

## 🔍 Cara Melihat Payload Lengkap yang Dikirim

### Method 1: Via Backend Terminal (Saat Generate dengan Image Upload)

Setelah generate batch dengan image upload, cek terminal backend. Harus ada log:

```
INFO: ======================================================================
INFO: GENERATION SUMMARY:
INFO: ======================================================================
INFO: Generation Mode: image-to-image  ← Harus ini jika ada image
INFO: Model: fal-ai/flux-general/image-to-image  ← Harus ini jika ada image
INFO: Init Image URL: YES  ← Harus YES jika ada image
INFO: ======================================================================

INFO: Sending image-to-image request to Fal.ai for image 1/2
INFO:    Model: fal-ai/flux-general/image-to-image
INFO:    ✅ Image-to-image: Using image_url from Supabase Storage
INFO:    📤 Image URL yang dikirim: https://...supabase.co/...
INFO:    Model: fal-ai/flux-general/image-to-image (support LoRA)
INFO:    Image Strength: 0.5 (FIXED: menjaga identitas wajah)
INFO:    Inference Steps: 7 (FIXED: INFERENCE, BUKAN training)
INFO:    Guidance Scale: 3.5 (FIXED: prompt adherence tanpa merusak wajah)
INFO:    📤 FULL REQUEST PAYLOAD ke Fal.ai:
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
python -c "from debug_prompt_log import get_latest_prompt_log; import json; log = get_latest_prompt_log(); print('Model:', log['fal_request']['model']); print('Generation Mode:', log.get('generation_mode', 'unknown')); print('Payload:', json.dumps(log['fal_request'], indent=2, ensure_ascii=False))"
```

### Method 3: Via Browser Dev Tools

1. F12 → **Network** tab
2. Filter: `generate-image`
3. Klik request → **Response** tab
4. Lihat `debug_info` → ini payload yang dikirim ke Fal.ai:

```json
{
  "images": ["https://..."],
  "remaining_coins": 99,
  "debug_info": {
    "prompt_sent": "...",
    "model": "fal-ai/flux-general/image-to-image",  // ← Harus ini jika ada image
    "generation_mode": "image-to-image",  // ← Harus ini jika ada image
    "image_strength": 0.5,  // ← Harus ini jika ada image
    "image_url": "https://...supabase.co/...",  // ← Harus ini jika ada image
    ...
  }
}
```

### Method 4: Via Debug Endpoint

```bash
GET http://localhost:8000/api/debug/last-prompt
```

## 📋 Checklist Verifikasi

### Untuk Text-to-Image (tanpa image):
- ✅ Model: `fal-ai/flux/schnell` ← **SUDAH BENAR** (sesuai log terakhir)
- ✅ Payload: `image_size`, `num_inference_steps: 7`, `guidance_scale: 3.5` ← **SUDAH BENAR**

### Untuk Image-to-Image (dengan image):
- ⚠️ Model: `fal-ai/flux-general/image-to-image` ← **BELUM ADA TEST**
- ⚠️ Payload: `image_url` (singular), `image_strength: 0.5`, `num_inference_steps: 7`, `guidance_scale: 3.5` ← **BELUM ADA TEST**

## 🎯 Kesimpulan

### ✅ Status Implementasi:

1. **Code sudah benar diimplementasikan**
   - ✅ Model endpoint sudah diupdate ke `fal-ai/flux-general/image-to-image`
   - ✅ Parameter sudah locked sesuai requirement
   - ✅ Payload building sudah benar (image_url singular, image_strength: 0.5)

2. **Log terakhir menggunakan text-to-image** (ini BENAR karena tidak ada image upload)
   - ✅ Model: `fal-ai/flux/schnell`
   - ✅ Payload sesuai untuk text-to-image

3. **⚠️ Belum ada test dengan image upload setelah update**
   - Entry pertama (timestamp 2026-01-11T02:41:48) menggunakan model lama (`fal-ai/flux-1.1/image-to-image`)
   - Semua entry setelahnya tidak ada image upload

### 🔧 Action Items:

1. **Test dengan image upload** untuk verifikasi model `fal-ai/flux-general/image-to-image`:
   - Upload face_image, product_image, atau background_image
   - Generate batch
   - Cek log backend - harus ada:
     - `Model: fal-ai/flux-general/image-to-image`
     - `Generation Mode: image-to-image`
     - Payload dengan `image_url` (singular) dan `image_strength: 0.5`

2. **Verify payload lengkap** di:
   - Backend terminal logs (paling lengkap)
   - Browser Dev Tools → Network → Response → `debug_info`
   - `prompt_log.json` (via script Python)

3. **Expected payload setelah test dengan image upload:**
```json
{
  "model": "fal-ai/flux-general/image-to-image",
  "prompt": "...",
  "image_url": "https://...supabase.co/...",
  "image_strength": 0.5,
  "num_inference_steps": 7,
  "guidance_scale": 3.5
}
```

---

**Silakan test dengan image upload dan share log backend untuk verifikasi lebih lanjut!**
