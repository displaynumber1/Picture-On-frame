# Migrate ke Model fal-ai/flux-2/lora/edit - COMPLETE ✅

## ✅ Perubahan yang Diterapkan

### 1. Model Endpoint

**File:** `backend/fal_service.py` (line 37)

```python
# Before
FAL_MODEL_ENDPOINT_IMAGE_TO_IMAGE = "fal-ai/flux-general/image-to-image"

# After
FAL_MODEL_ENDPOINT_IMAGE_TO_IMAGE = "fal-ai/flux-2/lora/edit"
```

### 2. Parameter: image_url → image_urls

**File:** `backend/fal_service.py` (line 120)

```python
# Before
"image_url": init_image_url,  # Singular

# After
"image_urls": [init_image_url],  # Plural - array
```

### 3. Comments & Documentation

**Updated:**
- Line 25: Model description
- Line 57-59: Function docstring
- Line 91: Comment
- Line 116-117: Payload comment

### 4. Logging

**File:** `backend/fal_service.py` (line 131-133)

```python
# Before
logger.info(f"   ✅ Image-to-image: Using image_url from Supabase Storage")
logger.info(f"   📤 Image URL yang dikirim: {init_image_url}")
logger.info(f"   Model: fal-ai/flux-general/image-to-image (support LoRA)")

# After
logger.info(f"   ✅ Image-to-image: Using image_urls from Supabase Storage")
logger.info(f"   📤 Image URLs yang dikirim: {[init_image_url]}")
logger.info(f"   Model: fal-ai/flux-2/lora/edit (FLUX.2 [dev] - support LoRA)")
```

### 5. Logging Payload

**File:** `backend/fal_service.py` (line 147-155)

```python
# Before
if 'image_url' in payload_for_log:
    payload_for_log['image_url_full'] = payload_for_log['image_url']
    payload_for_log['image_url'] = payload_for_log['image_url'][:100] + '...'

# After
if 'image_urls' in payload_for_log:
    image_urls_full = payload_for_log['image_urls']
    payload_for_log['image_urls_full'] = image_urls_full
    payload_for_log['image_urls'] = [
        url[:100] + '...' if len(url) > 100 else url 
        for url in image_urls_full
    ]
elif 'image_url' in payload_for_log:  # Legacy support
    # ...
```

### 6. Main.py

**File:** `backend/main.py`

**Line 1517:**
```python
# Before
model_name = "fal-ai/flux-general/image-to-image"

# After
model_name = "fal-ai/flux-2/lora/edit"
```

**Line 1542:**
```python
# Before
fal_request_data["image_url"] = init_image_url

# After
fal_request_data["image_urls"] = [init_image_url]
```

## 📊 Summary Perubahan

| Aspect | Before | After |
|--------|--------|-------|
| **Model** | `fal-ai/flux-general/image-to-image` | `fal-ai/flux-2/lora/edit` |
| **Parameter** | `image_url` (singular) | `image_urls` (array) |
| **Base Model** | Flux General | FLUX.2 [dev] |
| **Purpose** | General image-to-image | Specialized image editing |

## ✅ Verifikasi

- [x] Model endpoint updated
- [x] Parameter updated (image_url → image_urls)
- [x] Comments updated
- [x] Logging updated
- [x] Main.py updated
- [x] No linter errors
- [x] Python compile success

## 🧪 Next Steps

1. **Restart Backend:**
   ```bash
   cd backend
   python main.py
   ```

2. **Test Generate:**
   - Upload image
   - Generate batch
   - Check logs untuk parameter yang dikirim
   - Verify hasil

3. **Verify Parameters:**
   - Check fal API response
   - Verify parameter valid untuk model baru
   - Adjust jika perlu (image_strength, num_inference_steps, guidance_scale)

4. **Compare Results:**
   - Compare dengan model lama
   - Evaluate quality
   - Adjust parameter jika perlu

## ⚠️ Important Notes

1. **Parameter Compatibility:**
   - `image_strength: 0.5` - **KEEP** (verify if valid)
   - `num_inference_steps: 7` - **KEEP** (verify if valid)
   - `guidance_scale: 3.5` - **KEEP** (verify if valid)
   - `loras` - **KEEP** (verify if format same)

2. **Array Format:**
   - `image_urls` harus array: `[init_image_url]`
   - Bisa extend ke multiple images: `[url1, url2, ...]`

3. **API Response:**
   - Response format mungkin sama atau berbeda
   - Verify response parsing masih bekerja
   - Test dengan model baru

## 📝 Expected Payload

```json
{
  "prompt": "string",
  "image_urls": ["https://...supabase.co/.../IMAGES_UPLOAD/.../uuid.jpg"],
  "image_strength": 0.5,
  "num_inference_steps": 7,
  "guidance_scale": 3.5,
  "loras": ["optional"]
}
```

---

**Migrate ke `fal-ai/flux-2/lora/edit` selesai! ✅ Silakan restart backend dan test.**
