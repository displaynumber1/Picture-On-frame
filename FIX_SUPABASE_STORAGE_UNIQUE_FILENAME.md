# Fix: Supabase Storage Unique Filename dengan Category Path

## 🔍 Masalah yang Ditemukan

Hanya 1 gambar yang tersimpan di Supabase Storage meskipun user meng-upload beberapa gambar.

**Penyebab utama:** 
- Backend meng-upload semua file ke path atau filename yang sama, sehingga file lama tertindih (overwrite)
- Struktur path tidak terorganisir dengan category
- Parameter `upsert="true"` memungkinkan overwrite (meskipun UUID seharusnya unik)

## ✅ Solusi yang Diterapkan

### 1. Struktur Path dengan Category

**Sebelum:**
```python
# Path: {user_id}/{uuid}.jpg
file_path = f"{user_id}/{unique_filename}"
```

**Sesudah:**
```python
# Path: {user_id}/{category}/{uuid}.jpg
file_path = f"{user_id}/{category}/{unique_filename}"
```

**Category:**
- `face` - untuk face_image
- `product` - untuk product_images
- `background` - untuk background_image
- `upload` - untuk multipart uploads (default)

### 2. Set upsert=False

**Sebelum:**
```python
file_options={
    "content-type": "...",
    "upsert": "true"  # Overwrite if exists
}
```

**Sesudah:**
```python
file_options={
    "content-type": "...",
    "upsert": "false"  # Do not overwrite if exists (UUID ensures uniqueness)
}
```

### 3. Update Function Signature

**Sebelum:**
```python
def upload_image_to_supabase_storage(
    file_content: bytes,
    file_name: str,
    bucket_name: str = "public",
    user_id: Optional[str] = None
) -> str:
```

**Sesudah:**
```python
def upload_image_to_supabase_storage(
    file_content: bytes,
    file_name: str,
    bucket_name: str = "public",
    user_id: Optional[str] = None,
    category: Optional[str] = None  # NEW: category for path structure
) -> str:
```

### 4. Update All Function Calls

**Sebelum:**
```python
upload_image_to_supabase_storage(
    file_content=image_bytes,
    file_name=f"face_image_{user_id}{file_ext}",
    bucket_name="public",
    user_id=user_id
)
```

**Sesudah:**
```python
upload_image_to_supabase_storage(
    file_content=image_bytes,
    file_name=f"face_image{file_ext}",  # Only for extension extraction
    bucket_name="public",
    user_id=user_id,
    category="face"  # NEW: specify category
)
```

## 📋 Struktur Path Baru

### Example Paths:

1. **Face Image:**
   - Path: `{user_id}/face/{uuid}.jpg`
   - Example: `abc123-def456-789/face/a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg`

2. **Product Images:**
   - Path: `{user_id}/product/{uuid}.jpg`
   - Example: 
     - `abc123-def456-789/product/uuid1.jpg`
     - `abc123-def456-789/product/uuid2.jpg`
     - `abc123-def456-789/product/uuid3.jpg`
     - `abc123-def456-789/product/uuid4.jpg`

3. **Background Image:**
   - Path: `{user_id}/background/{uuid}.jpg`
   - Example: `abc123-def456-789/background/uuid-background.jpg`

4. **Multipart Upload:**
   - Path: `{user_id}/upload/{uuid}.jpg`
   - Example: `abc123-def456-789/upload/uuid-upload.jpg`

## ✅ Benefits

1. ✅ **Tidak ada overwrite** - Setiap file memiliki UUID unik
2. ✅ **Organized structure** - Files terorganisir per category
3. ✅ **Easy to find** - Bisa filter berdasarkan category
4. ✅ **Scalable** - Struktur path mendukung banyak files
5. ✅ **No naming conflicts** - UUID memastikan keunikan

## 📊 Before vs After

### Before (Masalah):
```
user_id/face_image_userid.jpg  ← Overwrite jika upload lagi
user_id/product_image_0_userid.jpg  ← Overwrite jika upload lagi
user_id/background_image_userid.jpg  ← Overwrite jika upload lagi
```

### After (Fixed):
```
user_id/face/{uuid1}.jpg  ← Unique
user_id/product/{uuid2}.jpg  ← Unique
user_id/product/{uuid3}.jpg  ← Unique
user_id/product/{uuid4}.jpg  ← Unique
user_id/background/{uuid5}.jpg  ← Unique
```

## 🔧 Changes Made

### Files Modified:

1. **backend/supabase_service.py**
   - Added `category` parameter to function signature
   - Updated path structure: `{user_id}/{category}/{uuid}.jpg`
   - Changed `upsert="false"` (UUID ensures uniqueness)
   - Updated function documentation

2. **backend/main.py**
   - Updated all `upload_image_to_supabase_storage` calls to include `category`
   - Face image: `category="face"`
   - Product images: `category="product"`
   - Background image: `category="background"`
   - Multipart upload: `category="upload"`

## ⚠️ Important Notes

1. **UUID Uniqueness**: UUID memastikan setiap file memiliki nama unik, jadi tidak akan ada overwrite meskipun `upsert="false"`

2. **Category Organization**: Category membantu mengorganisir files di Supabase Storage untuk memudahkan management dan cleanup

3. **File Name Parameter**: Parameter `file_name` sekarang hanya digunakan untuk extract extension, tidak digunakan untuk path akhir

4. **Backward Compatibility**: Tidak ada backward compatibility - semua upload baru akan menggunakan struktur path baru

## 🎯 Expected Behavior

### Upload Multiple Images:

**Request:**
- 1 face_image
- 4 product_images
- 1 background_image

**Supabase Storage Structure:**
```
public/
  {user_id}/
    face/
      {uuid1}.jpg  ← Face image
    product/
      {uuid2}.jpg  ← Product image 0
      {uuid3}.jpg  ← Product image 1
      {uuid4}.jpg  ← Product image 2
      {uuid5}.jpg  ← Product image 3
    background/
      {uuid6}.jpg  ← Background image
```

**Result:**
- ✅ Semua 6 images tersimpan dengan path unik
- ✅ Tidak ada overwrite
- ✅ Files terorganisir per category
- ✅ UUID memastikan keunikan

---

**Sekarang setiap gambar memiliki filename unik dengan struktur path yang terorganisir!**
