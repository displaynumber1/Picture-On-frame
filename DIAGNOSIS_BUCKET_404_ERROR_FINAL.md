# Diagnosis: Bucket Not Found Error (404) - Final

## 🔍 Error yang Ditemukan

```
SERVER ERROR: FAILED TO UPLOAD IMAGE TO SUPABASE STORAGE: 
{'statusCode': 404, 'error': 'Bucket not found', 'message': 'Bucket not found'}
IMAGE IS REQUIRED FOR IMAGE-TO-IMAGE PIPELINE
```

## 📊 Analisa Error

### Error Details:
- **HTTP Status**: 404 (Not Found)
- **Error Type**: Bucket not found
- **Bucket Name**: `public` (default)
- **Root Cause**: Bucket `'public'` tidak ada di Supabase Storage project Anda

## ✅ Solusi: Create Bucket di Supabase Dashboard

### Step-by-Step Instructions:

#### Step 1: Login ke Supabase Dashboard
1. Buka browser
2. Navigasi ke: **https://supabase.com/dashboard**
3. Login dengan akun Supabase Anda

#### Step 2: Pilih Project
1. Dari list projects, pilih project yang sesuai
2. Project URL dari config.env: `https://vmbzsnkkgxchzfviqcux.supabase.co`
3. Pastikan project ini yang dipilih

#### Step 3: Navigasi ke Storage
1. Di sidebar kiri, klik menu **"Storage"**
2. Klik tab **"Buckets"**

#### Step 4: Check Existing Buckets
1. Lihat list buckets yang ada
2. Cek apakah ada bucket dengan nama `public` (lowercase)
3. Jika TIDAK ADA → Continue ke Step 5
4. Jika ADA tapi error → Cek bucket settings (public/private)

#### Step 5: Create New Bucket
1. Klik tombol **"New bucket"** atau **"Create bucket"** (biasanya di pojok kanan atas)
2. **Name**: Ketik `public` (harus lowercase, exact match)
3. **Public bucket**: ✅ **Enable** (Toggle ON)
   - Ini PENTING untuk public access
4. **File size limit**: Sesuaikan (default biasanya 50MB)
5. **Allowed MIME types**: 
   - Option 1: Leave empty (allow all types)
   - Option 2: `image/*` (untuk images saja)
6. Klik **"Create bucket"** atau **"Save"**

#### Step 6: Verify Bucket Created
1. Pastikan bucket `public` muncul di list buckets
2. Status: **Active** / **Public** (ada icon globe 🌐)
3. Cek settings:
   - ✅ Public bucket: Enabled
   - ✅ Status: Active

#### Step 7: Restart Backend
1. Stop backend server (Ctrl+C di terminal)
2. Start backend lagi:
   ```bash
   cd backend
   python main.py
   ```

#### Step 8: Test Upload
1. Buka frontend
2. Upload image
3. Generate batch
4. Verify tidak ada error

## 🔍 Troubleshooting

### Issue 1: Bucket Name Mismatch

**Problem:** Bucket ada tapi dengan nama berbeda (misalnya `Public`, `PUBLIC`, `images`)

**Solution:**
- Option A: Create bucket baru dengan nama `public` (lowercase) ✅ RECOMMENDED
- Option B: Update code untuk menggunakan nama bucket yang ada (tidak recommended)

### Issue 2: Bucket Private Instead of Public

**Problem:** Bucket ada tapi private (tidak public)

**Solution:**
1. Klik bucket di list
2. Cari setting "Public bucket"
3. Enable toggle "Public bucket"
4. Save changes

### Issue 3: Service Role Key Tidak Valid

**Problem:** Service role key salah atau tidak punya akses

**Solution:**
1. Supabase Dashboard > Settings > API
2. Cek "service_role" key (secret key)
3. Copy key
4. Update `SUPABASE_SERVICE_KEY` di `config.env`
5. Pastikan format: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (JWT token)

### Issue 4: Wrong Project

**Problem:** Menggunakan project yang salah

**Solution:**
1. Cek `SUPABASE_URL` di `config.env`
2. Pastikan sesuai dengan project di Supabase Dashboard
3. Dari config.env: `https://vmbzsnkkgxchzfviqcux.supabase.co`

## 📋 Checklist

- [ ] Login ke Supabase Dashboard
- [ ] Pilih project yang benar (`vmbzsnkkgxchzfviqcux`)
- [ ] Navigasi ke Storage > Buckets
- [ ] Cek apakah bucket `public` ada (lowercase)
- [ ] Jika TIDAK ADA: Create bucket `public` (Public: Enabled)
- [ ] Verify bucket status: Active/Public
- [ ] Restart backend server
- [ ] Test upload image lagi

## 🎯 Expected Behavior Setelah Fix

Setelah bucket `public` dibuat:

1. **Upload berhasil:**
   ```
   INFO: 📤 Uploading image to Supabase Storage:
   INFO:    Bucket: public
   INFO:    Path: {user_id}/face/{uuid}.jpg
   INFO: ✅ Image uploaded successfully to Supabase Storage
   INFO:    Public URL: https://vmbzsnkkgxchzfviqcux.supabase.co/storage/v1/object/public/public/{user_id}/face/{uuid}.jpg
   ```

2. **Tidak ada error 404:**
   - Request berhasil (HTTP 200)
   - Image tersimpan di Supabase Storage
   - Public URL bisa diakses

3. **Frontend tidak error:**
   - Upload image berhasil
   - Generate batch berhasil
   - Images muncul di hasil

## 🔗 Links

- Supabase Dashboard: https://supabase.com/dashboard
- Supabase Storage Docs: https://supabase.com/docs/guides/storage
- Supabase Storage API: https://supabase.com/docs/reference/javascript/storage-from

## 📝 Catatan Penting

1. **Bucket Name:**
   - Harus **exact match**: `public` (lowercase)
   - `public` ≠ `Public` ≠ `PUBLIC`
   - Default di code: `"public"` (lowercase)

2. **Public Bucket:**
   - **Wajib** enabled untuk image generation pipeline
   - Public bucket: Files bisa diakses via public URL
   - Private bucket: Files butuh signed URL (tidak cocok untuk pipeline ini)

3. **Service Role Key:**
   - Harus menggunakan **service_role** key (bukan anon key)
   - Format: JWT token panjang
   - Bisa ditemukan di Supabase Dashboard > Settings > API > service_role key

4. **Project URL:**
   - Pastikan `SUPABASE_URL` sesuai dengan project
   - Dari config.env: `https://vmbzsnkkgxchzfviqcux.supabase.co`

---

**Kesimpulan: Bucket 'public' harus dibuat di Supabase Dashboard > Storage > Buckets (Public bucket: Enabled)**
