# Implementation Summary: Image Upload ke Supabase Storage + Image-to-Image fal

## ✅ Perubahan yang Telah Dilakukan

### 1. **Upload Image ke Supabase Storage** (`backend/supabase_service.py`)
- ✅ Fungsi `upload_image_to_supabase_storage()` untuk upload file ke bucket "public"
- ✅ Generate unique filename dengan UUID
- ✅ Organize file per user (prefix dengan user_id)
- ✅ Return public URL dari Supabase Storage
- ✅ Logging lengkap: upload progress, public URL, file path

### 2. **Endpoint Support File Upload** (`backend/main.py`)
- ✅ **Endpoint**: `/api/generate-image`
- ✅ **Method**: POST dengan `multipart/form-data`
- ✅ **Parameters**:
  - `prompt`: str (required, via Form)
  - `image`: UploadFile (optional, via File)
- ✅ Jika image diupload → Upload ke Supabase Storage → Ambil public URL → Gunakan untuk image-to-image
- ✅ Jika tidak ada image → Text-to-image (flow lama)

### 3. **Image-to-Image dengan fal** (`backend/fal_service.py`)
- ✅ Model: `fal-ai/flux/schnell` (sama untuk text-to-image dan image-to-image)
- ✅ **Parameter FIXED**:
  - `steps`: 7
  - `guidance_scale` (CFG): 3.5
  - `strength`: 0.65 (untuk image-to-image, range 0.6-0.7)
- ✅ **Payload untuk image-to-image**:
  ```json
  {
    "prompt": "...",
    "image_url": "https://...supabase.co/storage/v1/object/public/public/...",
    "num_inference_steps": 7,
    "guidance_scale": 3.5,
    "strength": 0.65
  }
  ```
- ✅ **Payload untuk text-to-image** (jika tidak ada image):
  ```json
  {
    "prompt": "...",
    "image_size": "square_hd",
    "num_inference_steps": 7,
    "guidance_scale": 3.5
  }
  ```

### 4. **Skip Gemini Vision**
- ✅ **TIDAK menggunakan Gemini Vision sama sekali**
- ✅ **TIDAK extract image description**
- ✅ **TIDAK enhance prompt dengan AI lain**
- ✅ Langsung image-to-image jika ada image, atau text-to-image jika tidak ada

### 5. **Logging yang Jelas**
- ✅ Log ketika image diupload ke Supabase Storage
- ✅ Log public image URL dari Supabase
- ✅ Log apakah request ke fal menggunakan image-to-image atau text-only
- ✅ Log semua parameter yang dikirim ke fal
- ✅ Debug info di response (bisa dilihat di browser Dev Tools)

### 6. **Environment Variables**
- ✅ Menggunakan env variable yang sudah ada: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `FAL_KEY`
- ✅ Tidak hardcode API key

### 7. **Response API Tetap Sama**
- ✅ Tetap return: `{"images": [...], "remaining_coins": ...}`
- ✅ Debug info di response (optional, untuk debugging)

## 🔄 Flow Baru

### Dengan Image Upload (Image-to-Image):
```
1. User upload gambar via multipart/form-data → Backend
2. Backend upload file ke Supabase Storage (bucket: "public")
3. Ambil public URL dari Supabase Storage
4. Kirim ke fal dengan parameter:
   - prompt: (dari user)
   - image_url: (public URL dari Supabase)
   - steps: 7
   - guidance_scale: 3.5
   - strength: 0.65
5. fal generate image berdasarkan prompt + image reference
6. Return image URLs ke frontend
```

### Tanpa Image Upload (Text-to-Image):
```
1. User kirim prompt saja → Backend
2. Backend kirim ke fal dengan parameter:
   - prompt: (dari user)
   - image_size: "square_hd"
   - steps: 7
   - guidance_scale: 3.5
3. fal generate image berdasarkan prompt saja
4. Return image URLs ke frontend
```

## 📋 Setup Requirements

### Supabase Storage Bucket:
1. Buka Supabase Dashboard → Storage
2. Buat bucket baru dengan nama: **`public`**
3. Set bucket sebagai **Public** (agar URL bisa diakses)
4. Pastikan RLS policy memungkinkan upload dari backend (service role key)

### Environment Variables (sudah ada):
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_role_key
FAL_KEY=your_fal_key
```

## 🧪 Testing

### Test Image-to-Image:
```bash
curl -X POST http://localhost:8000/api/generate-image \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "prompt=A Woman model, for Fashion, in Casual selfie..." \
  -F "image=@/path/to/image.jpg"
```

### Test Text-to-Image (tanpa image):
```bash
curl -X POST http://localhost:8000/api/generate-image \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "prompt=A Woman model, for Fashion, in Casual selfie..."
```

## 📝 Expected Logs

### Image Upload Success:
```
INFO: 📤 Received image file upload: image.jpg (123456 bytes)
INFO: 📤 Uploading image to Supabase Storage: bucket=public, path=user_id/uuid.jpg, size=123456 bytes
INFO: ✅ Image uploaded successfully to Supabase Storage
INFO:    Public URL: https://...supabase.co/storage/v1/object/public/public/user_id/uuid.jpg
INFO:    File path: user_id/uuid.jpg
INFO: ✅ Image uploaded to Supabase Storage successfully
INFO:    ⚠️  SKIPPED Gemini Vision - langsung image-to-image
```

### fal Request (Image-to-Image):
```
INFO: Generating images for user ... using fal fal-ai/flux/schnell (image-to-image mode)
INFO: 📝 FINAL PROMPT YANG DIKIRIM KE FAL.AI:
INFO:    Model: fal-ai/flux/schnell
INFO:    Mode: image-to-image
INFO:    Steps: 7, CFG: 3.5
INFO:    Strength: 0.65 (FIXED: 0.6-0.7)
INFO:    Image URL: https://...supabase.co/storage/v1/object/public/public/...
INFO: 📤 Sending image-to-image request to fal for image 1/2
INFO:    ✅ Image-to-image: Using image_url from Supabase Storage (strength: 0.65)
```

## ✅ Checklist

- [x] Backend menerima file upload (multipart/form-data)
- [x] Upload file ke Supabase Storage (bucket "public")
- [x] Ambil public URL dari Supabase Storage
- [x] Modifikasi request ke fal untuk image-to-image dengan `image_url`
- [x] Support text-to-image jika tidak ada image
- [x] Skip Gemini Vision
- [x] Logging lengkap
- [x] Tidak hardcode API key
- [x] Response API tetap sama

## ⚠️ Catatan

1. **Supabase Storage Bucket**: Pastikan bucket "public" sudah dibuat dan set sebagai public
2. **RLS Policy**: Pastikan service role key bisa upload ke bucket
3. **File Size**: Perhatikan limit file size (default Supabase: 50MB)
4. **Error Handling**: Jika upload ke Supabase gagal, akan return 500 error dengan detail message

## 🎯 Hasil Akhir

- ✅ Backend bisa generate image berbasis prompt + gambar referensi (image-to-image)
- ✅ Jika ada image → hasil harus jelas mereferensi image tersebut
- ✅ Jika tidak ada image → sistem tetap berjalan normal (text-to-image)
- ✅ Tidak menggunakan Gemini Vision sama sekali
- ✅ Clean implementation dengan minimal changes
