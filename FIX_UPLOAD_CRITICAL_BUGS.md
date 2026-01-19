# Fix: Critical Bugs di upload_image_to_supabase_storage

## 🔍 Bugs Kritis yang Ditemukan

1. **upsert sebagai STRING bukan BOOLEAN**
   - ❌ SALAH: `"upsert": "false"` (string)
   - ✅ BENAR: `"upsert": False` (boolean)

2. **Upload bytes mentah tanpa BytesIO**
   - ❌ SALAH: `file=file_content` (raw bytes)
   - ✅ BENAR: `file=BytesIO(file_content)` dengan `seek(0)`

3. **Content-type mapping tidak eksplisit**
   - ❌ SALAH: `f"image/{file_ext[1:]}"` (bisa salah untuk .jpg vs .jpeg)
   - ✅ BENAR: Explicit MIME type mapping

4. **Path tidak selalu unik**
   - ❌ SALAH: Fallback path tanpa UUID atau category
   - ✅ BENAR: Path SELALU `{user_id}/{category}/{uuid}.{ext}`

## ✅ Perbaikan yang Diterapkan

### 1. Upsert sebagai Boolean

**Sebelum:**
```python
file_options={
    "content-type": "...",
    "upsert": "false"  # ❌ STRING
}
```

**Sesudah:**
```python
file_options={
    "content-type": content_type,
    "upsert": False  # ✅ BOOLEAN
}
```

### 2. BytesIO Wrapper dengan seek(0)

**Sebelum:**
```python
response = supabase.storage.from_(bucket_name).upload(
    path=file_path,
    file=file_content,  # ❌ Raw bytes
    file_options={...}
)
```

**Sesudah:**
```python
from io import BytesIO

# Wrap bytes in BytesIO and reset pointer
file_stream = BytesIO(file_content)
file_stream.seek(0)  # ✅ Reset to beginning

response = supabase.storage.from_(bucket_name).upload(
    path=file_path,
    file=file_stream,  # ✅ BytesIO stream
    file_options={...}
)
```

### 3. Explicit MIME Type Mapping

**Sebelum:**
```python
"content-type": f"image/{file_ext[1:]}" if file_ext[1:] in ["jpg", "jpeg", "png", "webp"] else "image/jpeg"
# ❌ .jpg dan .jpeg bisa jadi "image/jpg" atau "image/jpeg" (inconsistent)
```

**Sesudah:**
```python
# MIME type mapping (explicit mapping for content-type)
mime_type_map = {
    "jpg": "image/jpeg",   # ✅ .jpg → image/jpeg
    "jpeg": "image/jpeg",  # ✅ .jpeg → image/jpeg
    "png": "image/png",
    "webp": "image/webp",
    "gif": "image/gif"
}
ext_lower = file_ext.lower().lstrip('.')
content_type = mime_type_map.get(ext_lower, "image/jpeg")  # Default to image/jpeg
```

### 4. Path SELALU Unik dengan Validasi

**Sebelum:**
```python
if user_id and category:
    file_path = f"{user_id}/{category}/{unique_filename}"
elif user_id:
    file_path = f"{user_id}/{unique_filename}"  # ❌ Bisa tanpa category
else:
    file_path = unique_filename  # ❌ Bisa tanpa user_id
```

**Sesudah:**
```python
# Path MUST always be unique (UUID ensures uniqueness)
if not user_id:
    raise ValueError("user_id is required for upload path structure")
if not category:
    raise ValueError("category is required for upload path structure")

file_path = f"{user_id}/{category}/{unique_filename}"  # ✅ SELALU format ini
```

## 📋 Perubahan Detail

### Function Signature (Tidak Berubah):
```python
def upload_image_to_supabase_storage(
    file_content: bytes,
    file_name: str,
    bucket_name: str = "public",
    user_id: Optional[str] = None,
    category: Optional[str] = None
) -> str:
```

### Key Changes:

1. **Import BytesIO:**
   ```python
   from io import BytesIO
   ```

2. **Extension Normalization:**
   ```python
   ext_lower = file_ext.lower().lstrip('.')
   ```

3. **MIME Type Mapping:**
   ```python
   mime_type_map = {
       "jpg": "image/jpeg",
       "jpeg": "image/jpeg",
       "png": "image/png",
       "webp": "image/webp",
       "gif": "image/gif"
   }
   content_type = mime_type_map.get(ext_lower, "image/jpeg")
   ```

4. **Path Validation:**
   ```python
   if not user_id:
       raise ValueError("user_id is required for upload path structure")
   if not category:
       raise ValueError("category is required for upload path structure")
   ```

5. **BytesIO Wrapper:**
   ```python
   file_stream = BytesIO(file_content)
   file_stream.seek(0)
   ```

6. **Boolean upsert:**
   ```python
   "upsert": False  # Boolean, not string
   ```

## ✅ Benefits

1. ✅ **Tidak ada overwrite** - `upsert=False` (boolean) + UUID memastikan keunikan
2. ✅ **File stream handling** - BytesIO dengan seek(0) memastikan file pointer benar
3. ✅ **Content-type konsisten** - .jpg dan .jpeg selalu `image/jpeg`
4. ✅ **Path selalu unik** - Validasi user_id dan category, struktur path konsisten
5. ✅ **Tidak ada silent failure** - Validasi strict, error handling jelas
6. ✅ **Upload stabil** - Deterministik dengan UUID dan path structure

## 🎯 Expected Behavior

### Upload Request:
```python
upload_image_to_supabase_storage(
    file_content=b"image bytes...",
    file_name="photo.jpg",
    bucket_name="public",
    user_id="user-123",
    category="face"
)
```

### Process:
1. ✅ Generate UUID: `a1b2c3d4-e5f6-7890-abcd-ef1234567890`
2. ✅ Extract extension: `.jpg`
3. ✅ Normalize: `jpg` → `image/jpeg`
4. ✅ Build path: `user-123/face/a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg`
5. ✅ Wrap in BytesIO: `BytesIO(file_content)` + `seek(0)`
6. ✅ Upload with `upsert=False` (boolean)
7. ✅ Return public URL

### Result:
- ✅ File tersimpan di path unik
- ✅ Tidak ada overwrite
- ✅ Content-type benar (`image/jpeg`)
- ✅ Public URL bisa diakses

## ⚠️ Breaking Changes

1. **user_id dan category sekarang REQUIRED**
   - Sebelum: Optional (dengan fallback)
   - Sesudah: Required (raise ValueError jika tidak ada)
   - **Impact**: Semua pemanggilan fungsi harus provide user_id dan category

2. **Path structure strict**
   - Sebelum: Bisa `{user_id}/{uuid}` atau `{uuid}` (fallback)
   - Sesudah: SELALU `{user_id}/{category}/{uuid}.{ext}`
   - **Impact**: Path structure lebih konsisten dan predictable

## 🔧 Files Modified

1. **backend/supabase_service.py**
   - Updated `upload_image_to_supabase_storage` function
   - Added BytesIO wrapper
   - Added explicit MIME type mapping
   - Added path validation
   - Changed upsert to boolean

## 📊 Before vs After

### Before (Buggy):
```python
# Upsert as string
"upsert": "false"  # ❌

# Raw bytes
file=file_content  # ❌

# Inconsistent content-type
"content-type": f"image/{file_ext[1:]}"  # ❌ .jpg bisa jadi "image/jpg"

# Path bisa tanpa category
file_path = f"{user_id}/{unique_filename}"  # ❌
```

### After (Fixed):
```python
# Upsert as boolean
"upsert": False  # ✅

# BytesIO with seek(0)
file_stream = BytesIO(file_content)
file_stream.seek(0)
file=file_stream  # ✅

# Explicit MIME mapping
content_type = mime_type_map.get(ext_lower, "image/jpeg")  # ✅ .jpg → image/jpeg

# Path always with category
file_path = f"{user_id}/{category}/{unique_filename}"  # ✅
```

---

**Upload sekarang stabil, deterministik, dan tidak ada overwrite!**
