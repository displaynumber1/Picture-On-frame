# Diagnosis: Payload yang Diterima Fal.ai dari Backend

## 📊 Ringkasan

Backend mengirim request ke Fal.ai menggunakan model **`fal-ai/flux-general/image-to-image`** untuk image-to-image generation dengan parameter yang sudah dikunci (fixed).

## 🔗 Endpoint dan HTTP Request

### Endpoint:
```
POST https://fal.run/fal-ai/flux-general/image-to-image
```

### HTTP Headers:
```http
Authorization: Key {FAL_KEY}
Content-Type: application/json
```

**Note:** `FAL_KEY` diambil dari environment variable `config.env`

## 📦 JSON Payload Structure

### Payload Format (Image-to-Image):

```json
{
  "prompt": "string (text prompt untuk image generation)",
  "image_url": "string (public URL dari Supabase Storage - REQUIRED)",
  "image_strength": 0.5,
  "num_inference_steps": 7,
  "guidance_scale": 3.5,
  "loras": ["optional", "array", "of", "lora", "paths"]
}
```

### Parameter Details:

#### 1. **prompt** (string, REQUIRED)
- **Type:** `string`
- **Description:** Text prompt untuk image generation
- **Source:** Dari `prompt_to_use` di `main.py`
- **Example:** 
  ```json
  "prompt": "A professional product photo with clean white background, studio lighting, high quality"
  ```

#### 2. **image_url** (string, REQUIRED)
- **Type:** `string` (URL)
- **Description:** Public URL dari Supabase Storage untuk reference image
- **Source:** Dari `init_image_url` (uploaded ke Supabase Storage)
- **Format:** `https://{project}.supabase.co/storage/v1/object/public/IMAGES_UPLOAD/{user_id}/{category}/{uuid}.{ext}`
- **Example:**
  ```json
  "image_url": "https://your-project.supabase.co/storage/v1/object/public/IMAGES_UPLOAD/user-123/face/a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg"
  ```
- **Note:** 
  - ✅ Singular (`image_url`, bukan `image_urls`)
  - ✅ Model `fal-ai/flux-general/image-to-image` menggunakan `image_url` (singular)
  - ✅ URL harus accessible publicly (Supabase Storage public bucket)

#### 3. **image_strength** (float, REQUIRED, FIXED)
- **Type:** `float`
- **Value:** `0.5` (FIXED - tidak bisa diubah)
- **Description:** Strength untuk menjaga identitas wajah tetap konsisten
- **Range:** 0.0 - 1.0
- **Effect:**
  - `0.0` = Fully follow prompt, ignore reference image
  - `0.5` = Balanced (maintain face identity while following prompt)
  - `1.0` = Fully follow reference image, ignore prompt
- **Reason:** `0.5` dipilih untuk menjaga identitas wajah tetap konsisten sambil mengikuti prompt

#### 4. **num_inference_steps** (integer, REQUIRED, FIXED)
- **Type:** `integer`
- **Value:** `7` (FIXED - tidak bisa diubah)
- **Description:** Number of inference steps (INI ADALAH INFERENCE, BUKAN TRAINING)
- **Range:** 1 - 50 (umumnya)
- **Note:** 
  - ⚠️ **BUKAN training steps** (ini inference steps untuk generation)
  - ⚠️ Jangan disamakan dengan LoRA training steps
  - ✅ 7 steps optimal untuk speed vs quality balance

#### 5. **guidance_scale** (float, REQUIRED, FIXED)
- **Type:** `float`
- **Value:** `3.5` (FIXED - tidak bisa diubah)
- **Description:** Guidance scale (CFG) untuk prompt adherence tanpa merusak wajah
- **Range:** 1.0 - 20.0 (umumnya)
- **Effect:**
  - Lower (1-3) = More creative, less prompt adherence
  - Medium (3-7) = Balanced (3.5 = optimal untuk face consistency)
  - Higher (7-20) = Strong prompt adherence, but may distort faces
- **Reason:** `3.5` dipilih agar prompt dipatuhi tanpa merusak identitas wajah

#### 6. **loras** (array, OPTIONAL)
- **Type:** `array of strings`
- **Description:** Array of LoRA paths/IDs dari Fal.ai untuk image editing
- **Default:** Tidak ada (opsional)
- **Example:**
  ```json
  "loras": [
    "fal-ai/flux/lora/some-lora-id",
    "fal-ai/flux/lora/another-lora-id"
  ]
  ```
- **Note:** 
  - ✅ Optional parameter
  - ✅ Bisa diisi dinamis di masa depan
  - ✅ Model `fal-ai/flux-general/image-to-image` support LoRA

## 📋 Example Payload Lengkap

### ⚠️ Important Note

**Example payload di bawah adalah CONTOH GENERIC untuk ilustrasi format JSON, BUKAN prompt yang sebenarnya dari frontend.**

**Fakta:**
- ✅ Backend TIDAK mengubah prompt dari frontend
- ✅ Prompt dikirim langsung AS-IS ke Fal.ai (tidak ada enhancement/generation)
- ✅ Prompt yang dikirim = Prompt dari frontend (identik)

**Untuk melihat prompt sebenarnya:**
- Check backend logs: `INFO: 📝 FINAL PROMPT YANG DIKIRIM KE FAL.AI`
- Check `backend/prompt_log.json`
- Check browser dev tools → Network tab → Response → `debug_info.prompt_sent`

### Example 1: Basic Image-to-Image (tanpa LoRA)

```json
{
  "prompt": "A professional product photo with clean white background, studio lighting, high quality, product detail visible",
  "image_url": "https://your-project.supabase.co/storage/v1/object/public/IMAGES_UPLOAD/user-123/face/a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg",
  "image_strength": 0.5,
  "num_inference_steps": 7,
  "guidance_scale": 3.5
}
```
**Note:** `"prompt"` di atas adalah contoh generic. Prompt sebenarnya = input langsung dari user di frontend.

### Example 2: Image-to-Image dengan LoRA

```json
{
  "prompt": "A professional product photo with clean white background, studio lighting, high quality",
  "image_url": "https://your-project.supabase.co/storage/v1/object/public/IMAGES_UPLOAD/user-123/product/b2c3d4e5-f6a7-8901-bcde-f23456789012.png",
  "image_strength": 0.5,
  "num_inference_steps": 7,
  "guidance_scale": 3.5,
  "loras": [
    "fal-ai/flux/lora/some-style-lora"
  ]
}
```
**Note:** `"prompt"` di atas adalah contoh generic. Prompt sebenarnya = input langsung dari user di frontend.

## 🔧 Code Implementation

### File: `backend/fal_service.py`

#### Function: `generate_images()`

```python
async def generate_images(
    prompt: str, 
    num_images: int = 2,
    init_image_url: Optional[str] = None,  # REQUIRED untuk image-to-image
    loras: Optional[List[str]] = None  # OPTIONAL
) -> List[str]:
```

#### Payload Construction (Line 118-124):

```python
request_payload = {
    "prompt": prompt,  # From main.py prompt_to_use
    "image_url": init_image_url,  # From Supabase Storage (public URL)
    "image_strength": FAL_IMAGE_STRENGTH,  # 0.5 (FIXED)
    "num_inference_steps": FAL_NUM_INFERENCE_STEPS,  # 7 (FIXED)
    "guidance_scale": FAL_GUIDANCE_SCALE  # 3.5 (FIXED)
}

# Add loras if provided (optional)
if loras and len(loras) > 0:
    request_payload["loras"] = loras
```

#### HTTP Request (Line 156-163):

```python
response = await client.post(
    f"{FAL_API_BASE}/{model_endpoint}",  # https://fal.run/fal-ai/flux-general/image-to-image
    headers={
        "Authorization": f"Key {FAL_KEY}",
        "Content-Type": "application/json"
    },
    json=request_payload
)
```

### File: `backend/main.py`

#### Function Call (Line 1561):

```python
image_urls = await fal_generate_images(
    prompt_to_use,           # prompt (string)
    num_images=2,            # number of images to generate
    init_image_url=init_image_url  # REQUIRED - Supabase Storage public URL
)
```

## 📊 Parameter Configuration (LOCKED)

### Constants di `backend/fal_service.py`:

```python
FAL_MODEL_ENDPOINT_IMAGE_TO_IMAGE = "fal-ai/flux-general/image-to-image"
FAL_NUM_INFERENCE_STEPS = 7  # FIXED
FAL_GUIDANCE_SCALE = 3.5  # FIXED
FAL_IMAGE_STRENGTH = 0.5  # FIXED
```

### Validation (Line 82-87):

```python
# Validate locked configuration
if FAL_NUM_INFERENCE_STEPS != 7:
    raise ValueError("num_inference_steps is locked to 7")
if FAL_GUIDANCE_SCALE != 3.5:
    raise ValueError("guidance_scale is locked to 3.5")
if init_image_url and FAL_IMAGE_STRENGTH != 0.5:
    raise ValueError("image_strength is locked to 0.5")
```

## 📝 Logging Output

### Request Logging (Line 152-154):

```
INFO: 📤 FULL REQUEST PAYLOAD ke Fal.ai:
INFO: {
INFO:   "prompt": "{prompt sebenarnya dari frontend}",  ← Prompt AS-IS dari user
INFO:   "image_url": "https://...supabase.co/storage/v1/object/public/IMAGES_UPLOAD/...",
INFO:   "image_strength": 0.5,
INFO:   "num_inference_steps": 7,
INFO:   "guidance_scale": 3.5
INFO: }
```

**Note:** `"prompt"` di logs adalah prompt sebenarnya dari frontend (tidak ada perubahan).

### Debug Logging:

```
DEBUG: Full request payload (detailed): {full JSON dengan image_url lengkap}
```

### Prompt Flow Logging (Line 1520-1528):

```
INFO: 📝 FINAL PROMPT YANG DIKIRIM KE FAL.AI (IMAGE-TO-IMAGE PIPELINE):
INFO:    Prompt: {prompt sebenarnya dari frontend}  ← Langsung dari user input
INFO:    Prompt length: {length} chars
```

## 🎯 Flow Diagram

```
1. Frontend → Backend (/api/generate-image)
   - Upload image (multipart/form-data atau JSON base64)
   
2. Backend → Supabase Storage
   - Upload image ke bucket "IMAGES_UPLOAD"
   - Get public URL: https://...supabase.co/.../IMAGES_UPLOAD/{user_id}/{category}/{uuid}.{ext}
   
3. Backend → Fal.ai (POST https://fal.run/fal-ai/flux-general/image-to-image)
   - Payload: {
       "prompt": "...",
       "image_url": "https://...supabase.co/...",  ← Public URL dari Supabase
       "image_strength": 0.5,
       "num_inference_steps": 7,
       "guidance_scale": 3.5
     }
   
4. Fal.ai → Backend
   - Response: { "images": [{ "url": "https://..." }] }
   
5. Backend → Frontend
   - Return: { "images": [...], "remaining_coins": ... }
```

## ⚠️ Important Notes

1. **Model:** 
   - ✅ `fal-ai/flux-general/image-to-image` (image-to-image dengan LoRA support)
   - ❌ Bukan `fal-ai/flux/schnell` (text-to-image)

2. **Parameter Name:**
   - ✅ `image_url` (singular) - bukan `image_urls` (plural)
   - ✅ Model `flux-general/image-to-image` menggunakan `image_url` (singular)

3. **Fixed Parameters:**
   - ✅ `image_strength: 0.5` (FIXED - tidak bisa diubah)
   - ✅ `num_inference_steps: 7` (FIXED - ini INFERENCE, bukan training)
   - ✅ `guidance_scale: 3.5` (FIXED - optimal untuk face consistency)

4. **Image URL:**
   - ✅ Harus public URL (Supabase Storage public bucket)
   - ✅ Format: `https://{project}.supabase.co/storage/v1/object/public/IMAGES_UPLOAD/...`
   - ✅ Fal.ai harus bisa access URL ini (public access)

5. **LoRA Support:**
   - ✅ Model support LoRA (optional parameter)
   - ✅ Format: `["fal-ai/flux/lora/lora-id"]` (array of strings)

## 🔍 Debugging

### Cara Cek Payload yang Dikirim (Including Prompt Sebenarnya):

1. **Check Backend Logs:**
   ```
   INFO: 📝 FINAL PROMPT YANG DIKIRIM KE FAL.AI:
   INFO:    Prompt: {prompt sebenarnya dari frontend}
   INFO: 📤 FULL REQUEST PAYLOAD ke Fal.ai:
   INFO: {
   INFO:   "prompt": "{prompt sebenarnya dari frontend}",  ← Prompt AS-IS dari user
   INFO:   ...
   INFO: }
   ```

2. **Check Debug Prompt Log:**
   - File: `backend/prompt_log.json`
   - Contains: Last request payload dengan prompt sebenarnya
   - Field: `enhanced_prompt` atau `fal_request.prompt` = prompt sebenarnya dari frontend

3. **Check Browser Dev Tools:**
   - Network tab → `/api/generate-image` → Response
   - Field: `debug_info.prompt_sent` = prompt sebenarnya yang dikirim ke Fal.ai
   - Field: `debug_info.original_prompt` = prompt sebenarnya (truncated untuk display)

4. **Check Fal.ai API Response:**
   ```
   DEBUG: Fal.ai API response for image 1: {response JSON}
   ```

### ⚠️ Important: Prompt Flow

**Backend TIDAK mengubah prompt dari frontend:**
- ✅ Prompt diambil langsung: `prompt_to_use = form_data.get("prompt")` atau `json_data.get("prompt")`
- ✅ Prompt dikirim langsung: `await fal_generate_images(prompt_to_use, ...)`
- ✅ Tidak ada prompt enhancement, generation, atau manipulation
- ✅ Prompt yang dikirim ke Fal.ai = Prompt dari frontend (identik)

### Common Issues:

1. **404 Error:**
   - ❌ Image URL tidak accessible
   - ✅ Pastikan Supabase Storage bucket adalah PUBLIC
   - ✅ Pastikan URL format benar

2. **403 Forbidden:**
   - ❌ FAL_KEY tidak valid atau tidak punya akses ke model
   - ✅ Check FAL_KEY di config.env

3. **422 Unprocessable Entity:**
   - ❌ Payload format salah
   - ✅ Pastikan semua required fields ada
   - ✅ Pastikan image_url adalah valid URL

4. **Image tidak sesuai:**
   - ⚠️ Check `image_strength` (0.5 = balanced)
   - ⚠️ Check `guidance_scale` (3.5 = optimal untuk faces)
   - ⚠️ Check prompt quality

## 📚 References

- Fal.ai API Docs: https://fal.ai/models/fal-ai/flux-general/image-to-image
- Model Endpoint: `fal-ai/flux-general/image-to-image`
- Supabase Storage: https://supabase.com/docs/guides/storage

---

**Dokumentasi lengkap tentang payload yang diterima Fal.ai dari backend.**
