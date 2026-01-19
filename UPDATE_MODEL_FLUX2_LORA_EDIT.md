# Update Model ke fal-ai/flux-2/lora/edit

## ✅ Perubahan yang Dilakukan

### 1. **Model Endpoint** (`backend/fal_service.py`):
- **Image-to-image**: `fal-ai/flux-2/lora/edit` (baru)
- **Text-to-image**: `fal-ai/flux/schnell` (tetap)

### 2. **Parameter Payload**:
- **Image-to-image**: Menggunakan `image_urls` (array) bukan `image_url` (singular)
- **Format**: `{"image_urls": ["https://...supabase.co/..."]}`

### 3. **Parameter yang Dikirim ke Fal.ai**:

**Image-to-Image Mode:**
```json
{
  "prompt": "A Woman model, for Fashion...",
  "image_urls": ["https://...supabase.co/storage/v1/object/public/public/..."],
  "num_inference_steps": 7,
  "guidance_scale": 3.5,
  "strength": 0.65
}
```

**Text-to-Image Mode:**
```json
{
  "prompt": "A Woman model, for Fashion...",
  "image_size": "square_hd",
  "num_inference_steps": 7,
  "guidance_scale": 3.5
}
```

## 📋 Payload Lengkap yang Dikirim Backend ke Fal.ai

### Image-to-Image (dengan init image):
```json
{
  "prompt": "A Woman model, for Fashion, in Mirror selfie using iPhone pose, in Cinematic style, with Natural Daylight lighting, shot from Eye-Level angle, in 9:16 aspect ratio, photorealistic resolusi HD",
  "image_urls": [
    "https://vmbzsnkkgxchzfviqcux.supabase.co/storage/v1/object/public/public/user_id/uuid.jpg"
  ],
  "num_inference_steps": 7,
  "guidance_scale": 3.5,
  "strength": 0.65
}
```

**Endpoint:** `POST https://fal.run/fal-ai/flux-2/lora/edit`

**Headers:**
```
Authorization: Key YOUR_FAL_KEY
Content-Type: application/json
```

## 🔍 Cara Melihat Payload yang Dikirim

### 1. **Via Backend Logs:**
Setelah generate batch, cek terminal backend. Akan ada log:
```
INFO: 📤 FULL REQUEST PAYLOAD ke Fal.ai:
INFO:    {
INFO:      "prompt": "...",
INFO:      "image_urls": ["https://..."],
INFO:      "num_inference_steps": 7,
INFO:      "guidance_scale": 3.5,
INFO:      "strength": 0.65
INFO:    }
```

### 2. **Via Browser Dev Tools:**
1. Buka browser Dev Tools (F12)
2. Tab **Network**
3. Filter: `generate-image`
4. Klik request yang baru
5. Tab **Response**
6. Lihat `debug_info` - ada `image_urls` di sana

### 3. **Via Debug Endpoint:**
```bash
GET /api/debug/last-prompt
```
Response akan berisi:
```json
{
  "fal_request": {
    "model": "fal-ai/flux-2/lora/edit",
    "prompt": "...",
    "image_urls": ["https://..."],
    "num_inference_steps": 7,
    "guidance_scale": 3.5,
    "strength": 0.65
  }
}
```

## ✅ Checklist

- [x] Model endpoint: `fal-ai/flux-2/lora/edit` untuk image-to-image
- [x] Parameter: `image_urls` (array) bukan `image_url` (singular)
- [x] Logging payload lengkap
- [x] Debug info di response
- [x] Backward compatible untuk text-to-image

## 🎯 Expected Result

Setelah update:
- ✅ Fal.ai akan menerima `image_urls` dengan URL dari Supabase Storage
- ✅ Model `flux-2/lora/edit` akan melihat pixel gambar user langsung
- ✅ Hasil generate seharusnya lebih sesuai dengan foto upload
- ✅ Wajah, pose, dan style direferensikan dari foto user

## 📝 Catatan Model `fal-ai/flux-2/lora/edit`

- ✅ Support `image_urls` (array) - bisa multiple images
- ✅ Support `strength` parameter (0.6-0.7) untuk control seberapa kuat init image
- ✅ Support `prompt` untuk guidance tambahan
- ✅ Optimized untuk image editing dan image-to-image generation
- ✅ Lebih baik dalam mempertahankan detail dari init image

## 🧪 Testing

Setelah restart backend, test dengan:
1. Upload gambar (face/product/background)
2. Generate batch
3. Cek log backend - seharusnya ada `image_urls` di payload
4. Cek hasil - seharusnya lebih sesuai dengan foto upload

---

**Status**: ✅ **UPDATE SELESAI** - Model `fal-ai/flux-2/lora/edit` sudah diimplementasikan

Silakan restart backend dan test lagi!
