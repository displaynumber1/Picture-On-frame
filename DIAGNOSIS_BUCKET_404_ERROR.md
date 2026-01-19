# Diagnosis: Bucket Not Found Error (404)

## 🔍 Error yang Ditemukan

```
ValueError: Failed to upload image to Supabase Storage: {'statusCode': 404, 'error': 'Bucket not found', 'message': 'Bucket not found'}
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
- **Bucket Name**: `public` (default)

### Root Cause:
Supabase Storage bucket `'public'` tidak ditemukan di Supabase project Anda.

Error response dari Supabase Storage API:
```python
{
    'statusCode': 404,
    'error': 'Bucket not found',
    'message': 'Bucket not found'
}
```

## ✅ Solusi

### Option 1: Create Bucket 'public' di Supabase Dashboard (RECOMMENDED)

1. **Login ke Supabase Dashboard**
   - Buka https://supabase.com/dashboard
   - Login dengan akun Anda
   - Pilih project yang sesuai (`vmbzsnkkgxchzfviqcux`)

2. **Navigasi ke Storage**
   - Di sidebar kiri, klik menu **Storage**
   - Klik tab **Buckets**

3. **Create Bucket**
   - Klik tombol **"New bucket"** atau **"Create bucket"**
   - **Name**: `public` (harus lowercase, exact match)
   - **Public bucket**: ✅ **Enabled** (untuk public access)
   - **File size limit**: Sesuaikan (default biasanya 50MB, bisa diubah)
   - **Allowed MIME types**: Leave empty atau `image/*`
   - Klik **"Create bucket"** atau **"Save"**

4. **Verify Bucket Created**
   - Pastikan bucket `public` muncul di list buckets
   - Status: **Active** / **Public**
   - Icon: Globe (🌐) untuk public bucket

### Option 2: Gunakan Bucket yang Sudah Ada

Jika bucket sudah ada dengan nama berbeda:

1. **Cek nama bucket yang ada**
   - Buka Supabase Dashboard > Storage > Buckets
   - Lihat nama bucket yang tersedia (misalnya: `images`, `uploads`, dll)

2. **Update code untuk menggunakan bucket yang ada**
   - Update semua `bucket_name="public"` menjadi nama bucket yang benar
   - Atau update default parameter di function

**Tidak disarankan** karena akan mengubah banyak kode.

## ⚠️ Important Notes

1. **Bucket Name Case-Sensitive**
   - `public` ≠ `Public` ≠ `PUBLIC`
   - Default di code: `"public"` (lowercase)
   - Harus EXACT match

2. **Public vs Private Bucket**
   - **Public bucket**: Files bisa diakses via public URL tanpa authentication
   - **Private bucket**: Files memerlukan signed URL atau authentication
   - Untuk image generation pipeline, **wajib menggunakan public bucket**

3. **Service Role Key**
   - Pastikan `SUPABASE_SERVICE_KEY` di `config.env` adalah **service role key**
   - Bukan anon key
   - Format: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (JWT token)
   - Service role key memiliki full access ke Storage API

4. **Project URL**
   - Pastikan `SUPABASE_URL` di `config.env` benar
   - Format: `https://[project-ref].supabase.co`
   - Dari config.env: `https://vmbzsnkkgxchzfviqcux.supabase.co` ✅

## 🔍 Verification Steps

### Step 1: Cek Supabase Dashboard
```
1. Login ke https://supabase.com/dashboard
2. Pilih project: vmbzsnkkgxchzfviqcux
3. Storage > Buckets
4. Cek apakah bucket 'public' ada
```

### Step 2: Cek config.env
```env
SUPABASE_URL=https://vmbzsnkkgxchzfviqcux.supabase.co  ✅
SUPABASE_SERVICE_KEY=sb_secret_LwXdhKwIQljiOK0YcEPkCQ_KvbR7Pj8  ⚠️ Cek apakah service role key
```

### Step 3: Restart Backend
```bash
# Stop backend (Ctrl+C)
# Start backend lagi
cd backend
python main.py
```

### Step 4: Test Upload
Setelah bucket dibuat, test upload image lagi.

## 📋 Checklist

- [ ] Login ke Supabase Dashboard
- [ ] Navigasi ke Storage > Buckets
- [ ] Cek apakah bucket 'public' ada
- [ ] Jika TIDAK ada: Create bucket 'public' (Public bucket: Enabled)
- [ ] Verify bucket status: Active/Public
- [ ] Verify SUPABASE_SERVICE_KEY adalah service role key
- [ ] Restart backend server
- [ ] Test upload image lagi

## 🎯 Expected Behavior Setelah Fix

Setelah bucket `public` dibuat:

1. **Upload berhasil**:
   ```
   INFO: 📤 Uploading image to Supabase Storage:
   INFO:    Bucket: public
   INFO:    Path: {user_id}/face/{uuid}.jpg
   INFO:    File size: 245760 bytes (0.23 MB)
   INFO: ✅ Image uploaded successfully to Supabase Storage
   INFO:    Public URL: https://vmbzsnkkgxchzfviqcux.supabase.co/storage/v1/object/public/public/{user_id}/face/{uuid}.jpg
   ```

2. **Tidak ada error 404**:
   - Request berhasil (HTTP 200)
   - Image tersimpan di Supabase Storage
   - Public URL bisa diakses

3. **Response API berhasil**:
   ```json
   {
     "images": ["https://...supabase.co/..."],
     "remaining_coins": 99
   }
   ```

## 🔗 Links

- Supabase Dashboard: https://supabase.com/dashboard
- Supabase Storage Docs: https://supabase.com/docs/guides/storage
- Supabase Storage API: https://supabase.com/docs/reference/javascript/storage-from

## 📝 Catatan Tambahan

### Jika Bucket Sudah Ada tapi Masih Error 404

1. **Cek permissions bucket**
   - Bucket harus **public** (bukan private)
   - Service role key harus punya akses

2. **Cek project URL**
   - Pastikan `SUPABASE_URL` sesuai dengan project
   - Pastikan project aktif (tidak suspended)

3. **Cek service role key**
   - Pastikan key valid (tidak expired)
   - Pastikan menggunakan service role key (bukan anon key)
   - Format: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (JWT)

---

**Kesimpulan: Bucket 'public' harus dibuat di Supabase Dashboard > Storage > Buckets (Public bucket: Enabled)**
