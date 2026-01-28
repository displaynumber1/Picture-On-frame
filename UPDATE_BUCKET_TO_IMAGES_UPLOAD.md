# Update: Bucket Name ke IMAGES_UPLOAD

## ✅ Perubahan yang Diterapkan

Mengupdate bucket name dari `"public"` ke `"IMAGES_UPLOAD"` di semua tempat.

### Files Modified:

1. **backend/supabase_service.py**
   - Default parameter: `bucket_name: str = "public"` → `"IMAGES_UPLOAD"`

2. **backend/main.py**
   - 4 tempat dengan `bucket_name="public"` → `"IMAGES_UPLOAD"`
   - Line ~1350: multipart upload
   - Line ~1413: face_image upload
   - Line ~1441: product_image upload
   - Line ~1465: background_image upload

## 📋 Changes Detail

### 1. backend/supabase_service.py

**Before:**
```python
def upload_image_to_supabase_storage(
    file_content: bytes,
    file_name: str,
    bucket_name: str = "public",  # ❌ Old
    user_id: Optional[str] = None,
    category: Optional[str] = None
) -> str:
```

**After:**
```python
def upload_image_to_supabase_storage(
    file_content: bytes,
    file_name: str,
    bucket_name: str = "IMAGES_UPLOAD",  # ✅ New
    user_id: Optional[str] = None,
    category: Optional[str] = None
) -> str:
```

### 2. backend/main.py (4 places)

**Before:**
```python
bucket_name="public"  # ❌ Old
```

**After:**
```python
bucket_name="IMAGES_UPLOAD"  # ✅ New
```

**Locations:**
1. Multipart upload (line ~1350)
2. Face image upload (line ~1413)
3. Product image upload (line ~1441)
4. Background image upload (line ~1465)

## ✅ Verification

### Checklist:
- [x] Updated `backend/supabase_service.py` (default parameter)
- [x] Updated `backend/main.py` (4 places)
- [x] No linter errors
- [x] All `bucket_name="public"` replaced with `"IMAGES_UPLOAD"`

### Verify Bucket in Supabase:
- [ ] Bucket `IMAGES_UPLOAD` exists
- [ ] Bucket `IMAGES_UPLOAD` is PUBLIC (not private)
- [ ] Bucket status: Active / Public

## 🎯 Expected Behavior

Setelah update:

1. **Upload berhasil:**
   ```
   INFO: 📤 Uploading image to Supabase Storage:
   INFO:    Bucket: IMAGES_UPLOAD
   INFO:    Path: {user_id}/face/{uuid}.jpg
   INFO: ✅ Image uploaded successfully to Supabase Storage
   INFO:    Public URL: https://your-project.supabase.co/storage/v1/object/public/IMAGES_UPLOAD/{user_id}/face/{uuid}.jpg
   ```

2. **Tidak ada error 404:**
   - Request berhasil (HTTP 200)
   - Image tersimpan di bucket `IMAGES_UPLOAD`
   - Public URL bisa diakses

3. **Frontend tidak error:**
   - Upload image berhasil
   - Generate batch berhasil
   - Images muncul di hasil

## ⚠️ Important Notes

1. **Bucket Name Case-Sensitive:**
   - `IMAGES_UPLOAD` (uppercase) - exact match
   - Harus sesuai dengan bucket name di Supabase Dashboard

2. **Public Bucket Required:**
   - Bucket `IMAGES_UPLOAD` harus PUBLIC (bukan private)
   - Public bucket: Files bisa diakses via public URL
   - Private bucket: Files butuh signed URL (tidak cocok untuk pipeline ini)

3. **Bucket Status:**
   - Pastikan bucket status: **Active** / **Public**
   - Label "PUBLIC" harus terlihat di bucket list

## 🔧 Next Steps

1. **Restart Backend:**
   ```bash
   # Stop backend (Ctrl+C)
   # Start lagi
   cd backend
   python main.py
   ```

2. **Test Upload:**
   - Buka frontend
   - Upload image
   - Generate batch
   - Verify tidak ada error 404

3. **Verify Files in Supabase:**
   - Supabase Dashboard > Storage > Buckets > IMAGES_UPLOAD
   - Cek apakah files ter-upload dengan path: `{user_id}/{category}/{uuid}.{ext}`

---

**Update selesai! Code sekarang menggunakan bucket `IMAGES_UPLOAD` yang sudah ada.**
