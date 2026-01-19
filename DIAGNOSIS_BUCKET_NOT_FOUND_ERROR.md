# Diagnosis: Bucket Not Found Error (404)

## 🔍 Error yang Ditemukan

```
ValueError: Failed to upload image to Supabase Storage: {'statusCode': 404, 'error': Bucket not found, 'message': Bucket not found}
File: backend/supabase_service.py, line 286
POST /api/generate-image HTTP/1.1 500 Internal Server Error
```

## 📊 Analisa Error

### Error Details:
- **Error Type**: `ValueError`
- **Status Code**: 404 (Not Found)
- **Error Message**: "Bucket not found"
- **Location**: `backend/supabase_service.py`, line 286
- **HTTP Response**: 500 Internal Server Error

### Root Cause:
Supabase Storage bucket `'public'` tidak ditemukan di Supabase project user.

Error response dari Supabase Storage API:
```python
{
    'statusCode': 404,
    'error': 'Bucket not found',
    'message': 'Bucket not found'
}
```

## 🔧 Solusi yang Diperlukan

### Option 1: Create Bucket di Supabase Dashboard (RECOMMENDED)

1. **Login ke Supabase Dashboard**
   - Buka https://supabase.com/dashboard
   - Pilih project yang sesuai

2. **Navigasi ke Storage**
   - Klik menu **Storage** di sidebar kiri
   - Klik **Buckets** tab

3. **Create Bucket**
   - Klik tombol **"New bucket"** atau **"Create bucket"**
   - Nama bucket: `public`
   - Settings:
     - **Public bucket**: ✅ Enabled (untuk public access)
     - **File size limit**: Sesuaikan kebutuhan (default biasanya 50MB)
     - **Allowed MIME types**: `image/*` atau leave empty untuk semua types
   - Klik **"Create bucket"**

4. **Verify Bucket Created**
   - Pastikan bucket `public` muncul di list
   - Status: Active/Public

### Option 2: Gunakan Bucket yang Sudah Ada

Jika bucket sudah ada dengan nama berbeda:

1. **Cek nama bucket yang ada**
   - Buka Supabase Dashboard > Storage > Buckets
   - Lihat nama bucket yang tersedia

2. **Update code untuk menggunakan bucket yang ada**
   - Update `bucket_name` parameter di `upload_image_to_supabase_storage` calls
   - Atau update default `bucket_name="public"` ke nama bucket yang benar

### Option 3: Cek Supabase Project Configuration

1. **Verify Supabase URL dan Keys**
   - Pastikan `SUPABASE_URL` di `config.env` benar
   - Pastikan `SUPABASE_SERVICE_KEY` adalah service role key (bukan anon key)

2. **Cek Permissions**
   - Service role key harus punya akses ke Storage API
   - Pastikan key belum expired

## ⚠️ Important Notes

1. **Bucket Name**: Nama bucket harus EXACT match (case-sensitive)
   - `public` ≠ `Public` ≠ `PUBLIC`
   - Default bucket name di code: `"public"` (lowercase)

2. **Public vs Private Bucket**:
   - **Public bucket**: Files bisa diakses via public URL tanpa authentication
   - **Private bucket**: Files memerlukan signed URL atau authentication
   - Untuk image generation pipeline, biasanya menggunakan **public bucket**

3. **Service Role Key**:
   - Harus menggunakan **service role key** (bukan anon key)
   - Service role key memiliki full access ke Storage API
   - Format: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (JWT token)

## 🔍 Verification Steps

### Step 1: Cek Supabase Dashboard
```
1. Login ke Supabase Dashboard
2. Storage > Buckets
3. Cek apakah bucket 'public' ada
```

### Step 2: Cek config.env
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Step 3: Test Upload (Optional)
Setelah bucket dibuat, test upload:
```python
# Test script
from supabase_service import upload_image_to_supabase_storage
test_bytes = b"test image content"
url = upload_image_to_supabase_storage(
    file_content=test_bytes,
    file_name="test.jpg",
    bucket_name="public",
    user_id="test-user-id",
    category="test"
)
print(f"Upload success: {url}")
```

## 📋 Checklist

- [ ] Login ke Supabase Dashboard
- [ ] Navigasi ke Storage > Buckets
- [ ] Cek apakah bucket 'public' ada
- [ ] Jika tidak ada: Create bucket 'public' (Public bucket, enabled)
- [ ] Verify bucket status: Active/Public
- [ ] Restart backend server
- [ ] Test upload image lagi

## 🎯 Expected Behavior Setelah Fix

Setelah bucket `public` dibuat:

1. **Upload berhasil**:
   ```
   INFO: ✅ Image uploaded successfully to Supabase Storage
   INFO:    Public URL: https://...supabase.co/storage/v1/object/public/public/{user_id}/face/{uuid}.jpg
   ```

2. **Tidak ada error 404**:
   - Request berhasil (HTTP 200)
   - Image tersimpan di Supabase Storage
   - Public URL bisa diakses

## 🔗 Links

- Supabase Storage Docs: https://supabase.com/docs/guides/storage
- Supabase Storage API: https://supabase.com/docs/reference/javascript/storage-from
- Supabase Dashboard: https://supabase.com/dashboard

---

**Solusi utama: Create bucket 'public' di Supabase Dashboard > Storage > Buckets**
