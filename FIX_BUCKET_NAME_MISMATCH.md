# Fix: Bucket Name Mismatch

## 🔍 Masalah yang Ditemukan

**Bucket di Supabase:** `IMAGES_UPLOAD` (uppercase)
**Bucket di Code:** `"public"` (lowercase)

Bucket name **case-sensitive**, jadi tidak match → Error 404 (Bucket not found)

## ✅ Solusi: 2 Options

### Option 1: Create Bucket Baru "public" (RECOMMENDED)

**Kenapa RECOMMENDED:**
- ✅ Mengikuti default naming convention
- ✅ Tidak perlu ubah code
- ✅ Konsisten dengan standard practice
- ✅ Nama "public" lebih generic untuk berbagai use case

**Langkah-langkah:**

1. **Supabase Dashboard > Storage > Buckets**
2. **Klik "New bucket" atau "Create bucket"**
3. **Name:** `public` (lowercase, exact match dengan code)
4. **Public bucket:** ✅ **Enable** (Toggle ON)
5. **File size limit:** Sesuaikan (default 50MB)
6. **Allowed MIME types:** Leave empty atau `image/*`
7. **Klik "Create bucket"**

**Result:**
- ✅ Bucket `public` (lowercase) dibuat
- ✅ Code langsung bekerja tanpa perubahan
- ✅ Bucket `IMAGES_UPLOAD` tetap ada (bisa digunakan untuk lain)

### Option 2: Update Code untuk Menggunakan "IMAGES_UPLOAD"

**Kenapa Option 2:**
- ✅ Gunakan bucket yang sudah ada
- ✅ Tidak perlu create bucket baru
- ❌ Perlu ubah code di beberapa tempat

**Langkah-langkah:**

1. **Update semua `bucket_name="public"` menjadi `bucket_name="IMAGES_UPLOAD"`**

**Files yang perlu diubah:**
- `backend/main.py` (4 places)
- `backend/supabase_service.py` (default parameter)

**Changes:**

```python
# backend/supabase_service.py
def upload_image_to_supabase_storage(
    file_content: bytes,
    file_name: str,
    bucket_name: str = "IMAGES_UPLOAD",  # Changed from "public"
    user_id: Optional[str] = None,
    category: Optional[str] = None
) -> str:
    # ... rest of code ...
```

```python
# backend/main.py
# Line ~1350
public_url = upload_image_to_supabase_storage(
    file_content=file_content,
    file_name=file_name,
    bucket_name="IMAGES_UPLOAD",  # Changed from "public"
    user_id=user_id,
    category=category
)

# Line ~1413
public_url = upload_image_to_supabase_storage(
    file_content=image_bytes,
    file_name=f"face_image{file_ext}",
    bucket_name="IMAGES_UPLOAD",  # Changed from "public"
    user_id=user_id,
    category="face"
)

# Line ~1441
public_url = upload_image_to_supabase_storage(
    file_content=image_bytes,
    file_name=f"product_image{file_ext}",
    bucket_name="IMAGES_UPLOAD",  # Changed from "public"
    user_id=user_id,
    category="product"
)

# Line ~1465
public_url = upload_image_to_supabase_storage(
    file_content=image_bytes,
    file_name=f"background_image{file_ext}",
    bucket_name="IMAGES_UPLOAD",  # Changed from "public"
    user_id=user_id,
    category="background"
)
```

**Result:**
- ✅ Code menggunakan bucket `IMAGES_UPLOAD` yang sudah ada
- ✅ Tidak perlu create bucket baru
- ❌ Perlu ubah code di 5 places

## 📊 Comparison

| Aspect | Option 1: Create "public" | Option 2: Use "IMAGES_UPLOAD" |
|--------|---------------------------|-------------------------------|
| **Code Changes** | ✅ Tidak perlu | ❌ Perlu ubah 5 places |
| **Bucket Creation** | ❌ Perlu create baru | ✅ Sudah ada |
| **Naming Convention** | ✅ Standard "public" | ⚠️ Custom name |
| **Flexibility** | ✅ Generic untuk berbagai use case | ⚠️ Specific untuk images |
| **Recommended** | ✅ **YES** | ⚠️ Only if you prefer existing bucket |

## ✅ Recommendation

**RECOMMENDED: Option 1 - Create Bucket "public"**

**Reasoning:**
1. ✅ Tidak perlu ubah code
2. ✅ Nama "public" lebih standard
3. ✅ Bucket `IMAGES_UPLOAD` tetap ada untuk use case lain
4. ✅ Lebih mudah maintenance
5. ✅ Konsisten dengan default naming

**Jika memilih Option 2:**
- Pastikan bucket `IMAGES_UPLOAD` adalah PUBLIC (bukan private)
- Update semua `bucket_name="public"` menjadi `bucket_name="IMAGES_UPLOAD"`
- Test semua upload paths

## 📋 Checklist

### Option 1 (RECOMMENDED):
- [ ] Supabase Dashboard > Storage > Buckets
- [ ] Klik "New bucket"
- [ ] Name: `public` (lowercase)
- [ ] Public bucket: ✅ Enable
- [ ] Create bucket
- [ ] Verify bucket `public` muncul (status: PUBLIC)
- [ ] Restart backend
- [ ] Test upload

### Option 2:
- [ ] Verify bucket `IMAGES_UPLOAD` adalah PUBLIC
- [ ] Update `backend/supabase_service.py` (default parameter)
- [ ] Update `backend/main.py` (4 places)
- [ ] Restart backend
- [ ] Test upload

## 🎯 Expected Behavior Setelah Fix

Setelah bucket name match:

1. **Upload berhasil:**
   ```
   INFO: ✅ Image uploaded successfully to Supabase Storage
   INFO:    Bucket: public  # atau IMAGES_UPLOAD jika Option 2
   INFO:    Public URL: https://...supabase.co/storage/v1/object/public/public/{user_id}/face/{uuid}.jpg
   ```

2. **Tidak ada error 404:**
   - Request berhasil (HTTP 200)
   - Image tersimpan di Supabase Storage
   - Public URL bisa diakses

3. **Frontend tidak error:**
   - Upload image berhasil
   - Generate batch berhasil
   - Images muncul di hasil

## ⚠️ Important Notes

1. **Bucket Name Case-Sensitive:**
   - `public` ≠ `Public` ≠ `PUBLIC` ≠ `IMAGES_UPLOAD`
   - Harus exact match (case-sensitive)

2. **Public Bucket Required:**
   - Bucket harus PUBLIC (bukan private)
   - Public bucket: Files bisa diakses via public URL
   - Private bucket: Files butuh signed URL (tidak cocok untuk pipeline ini)

3. **Bucket Status:**
   - Pastikan bucket status: **Active** / **Public**
   - Label "PUBLIC" harus terlihat di bucket list

---

**RECOMMENDED: Option 1 - Create bucket "public" (lowercase) di Supabase Dashboard**
