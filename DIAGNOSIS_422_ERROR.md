# Diagnosis Error 422 Unprocessable Entity

## 🔴 Masalah

Error **422 Unprocessable Entity** terjadi karena **mismatch format request**:

- **Frontend**: Mengirim `Content-Type: application/json` dengan body JSON
- **Backend**: Mengharapkan `multipart/form-data` dengan `Form` dan `File`

## ✅ Solusi yang Diterapkan

Endpoint `/api/generate-image` sekarang **support kedua format**:

### 1. **JSON Body** (Backward Compatible - untuk frontend yang sudah ada)
```json
{
  "prompt": "A Woman model, for Fashion...",
  "product_images": ["data:image/jpeg;base64,..."],
  "face_image": "data:image/jpeg;base64,...",
  "background_image": "data:image/jpeg;base64,..."
}
```

**Flow:**
- Backend detect `Content-Type: application/json`
- Parse JSON body
- Jika ada base64 image → Convert ke bytes → Upload ke Supabase Storage → Ambil public URL
- Gunakan public URL untuk image-to-image

### 2. **Multipart/Form-Data** (New - untuk file upload langsung)
```
Content-Type: multipart/form-data
- prompt: "A Woman model, for Fashion..."
- image: [file upload]
```

**Flow:**
- Backend detect `Content-Type: multipart/form-data`
- Parse form data
- Upload file langsung ke Supabase Storage → Ambil public URL
- Gunakan public URL untuk image-to-image

## 📋 Perubahan Kode

### Endpoint Signature:
```python
@app.post("/api/generate-image")
async def generate_image_saas(
    request: Request,  # Changed from Form/File to Request
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    # Check Content-Type
    content_type = request.headers.get("content-type", "").lower()
    
    if "multipart/form-data" in content_type:
        # Handle multipart/form-data
        form_data = await request.form()
        prompt_to_use = form_data.get("prompt")
        image_file = form_data.get("image")
        # ... upload to Supabase Storage
    else:
        # Handle JSON body (backward compatible)
        json_data = await request.json()
        prompt_to_use = json_data.get("prompt")
        # ... convert base64 to Supabase Storage
```

## ✅ Status

- ✅ **Backward Compatible**: Frontend yang mengirim JSON tetap berfungsi
- ✅ **New Feature**: Support file upload via multipart/form-data
- ✅ **Auto Convert**: Base64 images otomatis di-upload ke Supabase Storage
- ✅ **Same Flow**: Kedua format menggunakan image-to-image dengan Supabase Storage URL

## 🧪 Testing

### Test JSON (Backward Compatible):
```bash
curl -X POST http://localhost:8000/api/generate-image \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A Woman model, for Fashion...",
    "face_image": "data:image/jpeg;base64,..."
  }'
```

### Test Multipart (New):
```bash
curl -X POST http://localhost:8000/api/generate-image \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "prompt=A Woman model, for Fashion..." \
  -F "image=@/path/to/image.jpg"
```

## 📝 Expected Logs

### JSON Request:
```
INFO: 📤 Converting face_image (base64) to Supabase Storage
INFO: ✅ face_image uploaded to Supabase Storage successfully
INFO:    Public URL: https://...supabase.co/storage/v1/object/public/public/...
```

### Multipart Request:
```
INFO: 📤 Received image file upload: image.jpg (123456 bytes)
INFO: ✅ Image uploaded to Supabase Storage successfully
INFO:    Public URL: https://...supabase.co/storage/v1/object/public/public/...
```

## ✅ Checklist

- [x] Support JSON body (backward compatible)
- [x] Support multipart/form-data (new feature)
- [x] Auto convert base64 to Supabase Storage
- [x] Upload file directly to Supabase Storage
- [x] Use public URL for image-to-image
- [x] Error handling untuk kedua format

## 🎯 Hasil

**Error 422 seharusnya sudah teratasi** karena backend sekarang bisa menerima kedua format request:
- ✅ JSON body (untuk frontend yang sudah ada)
- ✅ Multipart/form-data (untuk file upload langsung)

Silakan test lagi - error 422 seharusnya sudah tidak muncul!
