# Fix: Image-to-Image Pipeline Implementation

## ✅ Perubahan yang Dilakukan

### 1. **Menghapus Fallback ke Text-to-Image**

**Sebelum:**
```python
if not has_images:
    # Continue without image (fallback to text-to-image)  # ❌ SALAH
```

**Sesudah:**
```python
if not has_images:
    raise HTTPException(
        status_code=422,
        detail="Missing required image. This is an image-to-image pipeline - please provide at least one image."
    )  # ✅ BENAR - Require image
```

### 2. **Selalu Gunakan Model Image-to-Image**

**Sebelum:**
```python
model_name = "fal-ai/flux-general/image-to-image" if init_image_url else "fal-ai/flux/schnell"  # ❌ Kondisional
```

**Sesudah:**
```python
# ALWAYS use image-to-image mode and model (this is an image-to-image pipeline)
generation_mode = "image-to-image"
model_name = "fal-ai/flux-general/image-to-image"  # ALWAYS use image-to-image model  # ✅ BENAR
```

### 3. **Validasi Image URL Wajib**

**Sebelum:**
```python
if init_image_url:
    # ... do something  # ❌ Kondisional
```

**Sesudah:**
```python
# Image-to-image pipeline - init_image_url is REQUIRED at this point
if not init_image_url:
    raise HTTPException(
        status_code=500,
        detail="Internal error: Image URL not available. This should not happen in image-to-image pipeline."
    )  # ✅ BENAR - Validate required
```

### 4. **Payload Selalu Menggunakan Image URL**

**Sebelum:**
```python
if init_image_url:
    fal_request_data["image_strength"] = 0.5
    fal_request_data["image_url"] = init_image_url
else:
    fal_request_data["image_size"] = "square_hd"  # ❌ Kondisional
```

**Sesudah:**
```python
fal_request_data = {
    "model": model_name,
    "prompt": prompt_to_use,
    "num_inference_steps": 7,
    "guidance_scale": 3.5,
    "image_strength": 0.5,  # REQUIRED for image-to-image pipeline
    "image_url": init_image_url  # REQUIRED - Always present
}  # ✅ BENAR - Always include image
```

### 5. **Error Handling untuk Image Upload Gagal**

**Sebelum:**
```python
except Exception as e:
    logger.warning(f"Failed to upload... Continuing without image.")  # ❌ Fallback
```

**Sesudah:**
```python
except Exception as e:
    logger.error(f"Failed to upload...")
    raise HTTPException(
        status_code=500,
        detail=f"Failed to upload image... Image is required for image-to-image pipeline."
    )  # ✅ BENAR - Raise error, don't fallback
```

### 6. **Validasi Image File Wajib (Multipart)**

**Sebelum:**
```python
image_file = form_data.get("image")
if image_file and hasattr(image_file, 'filename') and image_file.filename:
    # ... upload  # ❌ Optional
```

**Sesudah:**
```python
image_file = form_data.get("image")
if not image_file or not hasattr(image_file, 'filename') or not image_file.filename:
    raise HTTPException(
        status_code=422,
        detail="Missing required image file. This is an image-to-image pipeline - image upload is required."
    )  # ✅ BENAR - Require image
```

### 7. **Update Fal Service untuk Validasi**

**Sebelum:**
```python
else:
    # Text-to-image payload (no image_url)
    request_payload = {...}  # ❌ Fallback to text-to-image
```

**Sesudah:**
```python
else:
    # This should NOT happen in image-to-image pipeline
    raise ValueError(
        "This is an image-to-image pipeline. init_image_url is required."
    )  # ✅ BENAR - Raise error
```

## 📋 Payload yang Dikirim ke Fal.ai (SETELAH FIX)

### Image-to-Image Pipeline (SELALU):

```json
{
  "prompt": "A Woman model, for Fashion, in Mirror selfie using iPhone pose...",
  "image_url": "https://your-project.supabase.co/storage/v1/object/public/public/user_id/uuid.jpg",
  "image_strength": 0.5,
  "num_inference_steps": 7,
  "guidance_scale": 3.5,
  "loras": []  // Optional
}
```

**Endpoint:** `POST https://fal.run/fal-ai/flux-general/image-to-image`

## ✅ Checklist Implementasi

- [x] Image wajib diupload (face_image, product_images, atau background_image)
- [x] Validasi image URL wajib tersedia sebelum generate
- [x] Selalu gunakan model `fal-ai/flux-general/image-to-image`
- [x] Selalu gunakan mode `image-to-image`
- [x] Payload selalu include `image_url` dan `image_strength`
- [x] Error handling untuk image upload gagal (tidak fallback)
- [x] Validasi image file wajib untuk multipart/form-data
- [x] Validasi image base64 wajib untuk JSON body
- [x] Update Fal service untuk reject text-to-image mode

## 🎯 Expected Behavior

1. **Request dengan Image:**
   - ✅ Upload image ke Supabase Storage
   - ✅ Gunakan `image_url` dari Supabase Storage
   - ✅ Generate dengan `fal-ai/flux-general/image-to-image`
   - ✅ Payload include `image_url` dan `image_strength: 0.5`

2. **Request TANPA Image:**
   - ❌ Raise HTTP 422: "Missing required image. This is an image-to-image pipeline..."
   - ❌ TIDAK fallback ke text-to-image
   - ❌ TIDAK menggunakan `fal-ai/flux/schnell`

3. **Image Upload Gagal:**
   - ❌ Raise HTTP 500: "Failed to upload image... Image is required..."
   - ❌ TIDAK fallback ke text-to-image
   - ❌ TIDAK continue without image

## 📊 Before vs After

### Before (Kondisional - SALAH):
- ❌ Jika tidak ada image → text-to-image mode
- ❌ Jika upload gagal → text-to-image mode
- ❌ Model dipilih kondisional
- ❌ Payload kondisional

### After (Image-to-Image Pipeline - BENAR):
- ✅ Image wajib tersedia
- ✅ Jika upload gagal → error (tidak fallback)
- ✅ Model selalu `fal-ai/flux-general/image-to-image`
- ✅ Payload selalu include `image_url` dan `image_strength`

## ✅ Testing

Setelah fix, test dengan:

1. **Test dengan Image Upload (Expected: SUCCESS):**
   - Upload face_image, product_image, atau background_image
   - Generate batch
   - Cek log: `Model: fal-ai/flux-general/image-to-image`
   - Cek payload: `image_url` dan `image_strength: 0.5`

2. **Test TANPA Image Upload (Expected: ERROR 422):**
   - Generate batch tanpa upload image
   - Expected: HTTP 422 "Missing required image..."

3. **Test dengan Image Upload Gagal (Expected: ERROR 500):**
   - Mock Supabase Storage error
   - Expected: HTTP 500 "Failed to upload image..."

---

**Pipeline sekarang SELALU image-to-image, tidak ada fallback ke text-to-image!**
