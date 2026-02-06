# Migrate ke Model fal-ai/flux-2/lora/edit - COMPLETE

## ✅ Perubahan yang Diterapkan

### 1. Update Model Endpoint

**File:** `backend/fal_service.py` (line 37)

**Before:**
```python
FAL_MODEL_ENDPOINT_IMAGE_TO_IMAGE = "fal-ai/flux-general/image-to-image"
```

**After:**
```python
FAL_MODEL_ENDPOINT_IMAGE_TO_IMAGE = "fal-ai/flux-2/lora/edit"
```

### 2. Update Parameter: image_url → image_urls

**File:** `backend/fal_service.py` (line 118-124)

**Before:**
```python
request_payload = {
    "prompt": prompt,
    "image_url": init_image_url,  # Singular
    "image_strength": FAL_IMAGE_STRENGTH,
    "num_inference_steps": FAL_NUM_INFERENCE_STEPS,
    "guidance_scale": FAL_GUIDANCE_SCALE
}
```

**After:**
```python
request_payload = {
    "prompt": prompt,
    "image_urls": [init_image_url],  # Plural - array
    "image_strength": FAL_IMAGE_STRENGTH,
    "num_inference_steps": FAL_NUM_INFERENCE_STEPS,
    "guidance_scale": FAL_GUIDANCE_SCALE
}
```

### 3. Update Logging

**File:** `backend/fal_service.py` (line 131-136)

**Before:**
```python
logger.info(f"   ✅ Image-to-image: Using image_url from Supabase Storage")
logger.info(f"   📤 Image URL yang dikirim: {init_image_url}")
logger.info(f"   Model: fal-ai/flux-general/image-to-image (support LoRA)")
```

**After:**
```python
logger.info(f"   ✅ Image-to-image: Using image_urls from Supabase Storage")
logger.info(f"   📤 Image URLs yang dikirim: {[init_image_url]}")
logger.info(f"   Model: fal-ai/flux-2/lora/edit (FLUX.2 [dev] - support LoRA)")
```

### 4. Update Comments

**File:** `backend/fal_service.py`
- Line 25: Updated model description
- Line 57-59: Updated function docstring
- Line 91: Updated comment
- Line 116-117: Updated payload comment

### 5. Update Main.py

**File:** `backend/main.py`
- Line 1517: Updated model_name
- Line 1542: Updated image_urls parameter

### 6. Update Logging Payload

**File:** `backend/fal_service.py` (line 146-151)

**Before:**
```python
if 'image_url' in payload_for_log:
    payload_for_log['image_url_full'] = payload_for_log['image_url']
    payload_for_log['image_url'] = payload_for_log['image_url'][:100] + '...'
```

**After:**
```python
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

## 📊 Summary Perubahan

### Model:
- **Before:** `fal-ai/flux-general/image-to-image`
- **After:** `fal-ai/flux-2/lora/edit`

### Parameter:
- **Before:** `image_url` (singular - string)
- **After:** `image_urls` (plural - array of strings)

### Parameter Lain:
- ✅ `image_strength: 0.5` - **KEEP** (verify if valid)
- ✅ `num_inference_steps: 7` - **KEEP** (verify if valid)
- ✅ `guidance_scale: 3.5` - **KEEP** (verify if valid)
- ✅ `loras` - **KEEP** (verify if format same)

## ⚠️ Important Notes

### 1. Parameter Compatibility

**Perlu verify apakah parameter ini valid untuk `fal-ai/flux-2/lora/edit`:**
- `image_strength` - Mungkin masih valid
- `num_inference_steps` - Mungkin masih valid
- `guidance_scale` - Mungkin masih valid
- `loras` - Format mungkin sama

**Jika parameter tidak valid:**
- Error akan muncul saat test
- Perlu adjust parameter sesuai dokumentasi fal

### 2. Array Format

**image_urls harus array:**
```python
"image_urls": [init_image_url]  # Array dengan 1 element
```

**Bisa extend ke multiple images:**
```python
"image_urls": [init_image_url, another_url, ...]  # Multiple images
```

### 3. API Response

**Response format mungkin sama atau berbeda:**
- Verify response parsing masih bekerja
- Check error handling
- Test dengan model baru

## 🧪 Testing

### Steps:
1. ✅ Code changes applied
2. ⏳ Restart backend
3. ⏳ Test dengan small request
4. ⏳ Verify parameter valid
5. ⏳ Compare results dengan model lama

### Expected Behavior:
- ✅ Request berhasil (tidak ada 422/400 error)
- ✅ Response format bisa di-parse
- ✅ Images generated
- ✅ Results sesuai (atau lebih baik dari model lama)

### If Error:
- ❌ Parameter tidak valid → Check fal documentation
- ❌ Response format berbeda → Update parsing logic
- ❌ Model tidak available → Verify API key permissions

## 🔧 Next Steps

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
   - Verify parameter valid
   - Adjust jika perlu

4. **Compare Results:**
   - Compare dengan model lama
   - Evaluate quality
   - Adjust parameter jika perlu

---

**Migrate ke `fal-ai/flux-2/lora/edit` selesai! Silakan restart backend dan test.**
