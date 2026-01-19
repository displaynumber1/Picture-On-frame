# Update Model ke fal-ai/flux-general/image-to-image

## ✅ Perubahan yang Dilakukan

### 1. Model Endpoint
- **Dari:** `fal-ai/flux-2/lora/edit`
- **Ke:** `fal-ai/flux-general/image-to-image`

### 2. Parameter Image Reference
- **Dari:** `image_urls` (array)
- **Ke:** `image_url` (singular)

### 3. Parameter Strength
- **Dari:** `strength: 0.65`
- **Ke:** `image_strength: 0.5`

### 4. Parameter Baru: LoRA Support
- **Tambahan:** `loras` (optional array) - untuk LoRA paths/IDs dari fal.ai
- Bisa diisi dinamis di masa depan
- Jika tidak diisi, request tetap berjalan normal

## 📋 Parameter WAJIB (Locked)

✅ **image_strength: 0.5**
- Untuk menjaga identitas wajah tetap konsisten
- ❗ JANGAN gunakan nilai default dari fal.ai

✅ **num_inference_steps: 7**
- Ini adalah INFERENCE, BUKAN training
- ❗ JANGAN menyamakan inference steps dengan training LoRA

✅ **guidance_scale: 3.5**
- Agar prompt dipatuhi tanpa merusak wajah
- ❗ JANGAN gunakan nilai default dari fal.ai

## 📝 Payload yang Dikirim ke Fal.ai

### Image-to-Image (dengan init image):
```json
{
  "prompt": "A Woman model, for Fashion...",
  "image_url": "https://...supabase.co/storage/v1/object/public/public/user_id/uuid.jpg",
  "image_strength": 0.5,
  "num_inference_steps": 7,
  "guidance_scale": 3.5,
  "loras": []  // Optional - bisa diisi dinamis di masa depan
}
```

**Endpoint:** `POST https://fal.run/fal-ai/flux-general/image-to-image`

### Text-to-Image (tanpa init image):
```json
{
  "prompt": "A Woman model, for Fashion...",
  "image_size": "square_hd",
  "num_inference_steps": 7,
  "guidance_scale": 3.5
}
```

**Endpoint:** `POST https://fal.run/fal-ai/flux/schnell`

## 🔧 Files yang Diupdate

1. **backend/fal_service.py**
   - Updated `FAL_MODEL_ENDPOINT_IMAGE_TO_IMAGE` ke `fal-ai/flux-general/image-to-image`
   - Updated `FAL_STRENGTH` ke `FAL_IMAGE_STRENGTH = 0.5`
   - Updated payload dari `image_urls` (array) ke `image_url` (singular)
   - Updated parameter dari `strength` ke `image_strength`
   - Added support untuk `loras` parameter (optional)
   - Updated validation messages untuk clarity

2. **backend/main.py**
   - Updated model name ke `fal-ai/flux-general/image-to-image`
   - Updated logging untuk reflect parameter baru
   - Updated `fal_request_data` untuk menggunakan `image_url` dan `image_strength`

3. **backend/debug_prompt_log.py**
   - Updated `generation_mode` detection untuk menggunakan `image_strength` bukan `strength`

## 🎯 Focus Points

1. **Image Editing + Prompt Adherence**
   - Parameter dikonfigurasi untuk fokus pada image editing sambil mematuhi prompt
   - `image_strength: 0.5` menjaga identitas wajah tetap konsisten
   - `guidance_scale: 3.5` memastikan prompt dipatuhi tanpa merusak wajah

2. **Inference vs Training**
   - `num_inference_steps: 7` adalah INFERENCE steps, BUKAN training steps
   - Jangan bingung dengan training LoRA yang memerlukan lebih banyak steps

3. **LoRA Support (Optional)**
   - LoRA paths/IDs bisa diisi dinamis di masa depan
   - Jika tidak diisi, request tetap berjalan normal (text-to-image atau image-to-image tanpa LoRA)

## ✅ Testing

Setelah update:
1. Restart backend server
2. Test dengan image upload (image-to-image mode)
3. Test tanpa image upload (text-to-image mode)
4. Verify payload di log backend:
   - Model: `fal-ai/flux-general/image-to-image`
   - Parameter: `image_url`, `image_strength: 0.5`, `num_inference_steps: 7`, `guidance_scale: 3.5`
   - LoRA: Optional (jika ada)

## 📊 Expected Behavior

- ✅ Image-to-image: Menggunakan `fal-ai/flux-general/image-to-image` dengan `image_url` (singular)
- ✅ Text-to-image: Menggunakan `fal-ai/flux/schnell` (fallback)
- ✅ Parameter locked: Tidak bisa diubah kecuali di source code
- ✅ LoRA support: Optional, bisa ditambahkan dinamis di masa depan
- ✅ Hasil: Image editing yang menjaga identitas wajah sambil mematuhi prompt

---

**Silakan restart backend dan test lagi!**
