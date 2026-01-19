# Fix: Upload File Stream Handling dan Logging

## 🔍 Masalah yang Ditemukan

Upload gagal dengan error terkait Supabase Storage bucket. User meminta untuk:
1. Pastikan `file.file.seek(0)` sebelum upload
2. Filename unik (UUID) - sudah ada
3. upsert=False - sudah ada
4. Tambahkan logging ukuran file dan response Supabase
5. Jika upload gagal, lempar exception dan hentikan proses
6. Fokus pada perbaikan loop upload dan file stream handling

## ✅ Perbaikan yang Diterapkan

### 1. File Stream Handling untuk Multipart Upload

**Sebelum:**
```python
file_content = await image_file.read()
# No seek(0) before read
```

**Sesudah:**
```python
# Reset file pointer to beginning (in case it was read before)
if hasattr(image_file, 'file') and hasattr(image_file.file, 'seek'):
    image_file.file.seek(0)

file_content = await image_file.read()
# Validate file size
if file_size == 0:
    raise HTTPException(status_code=422, detail="Empty file uploaded...")
```

### 2. Enhanced Logging di Upload Function

**Sebelum:**
```python
logger.info(f"📤 Uploading image to Supabase Storage: bucket={bucket_name}, path={file_path}, size={len(file_content)} bytes")
# ... upload ...
logger.info(f"✅ Image uploaded successfully")
```

**Sesudah:**
```python
# Log file details before upload
file_size_bytes = len(file_content)
file_size_mb = file_size_bytes / (1024 * 1024)
logger.info(f"📤 Uploading image to Supabase Storage:")
logger.info(f"   Bucket: {bucket_name}")
logger.info(f"   Path: {file_path}")
logger.info(f"   File size: {file_size_bytes} bytes ({file_size_mb:.2f} MB)")
logger.info(f"   File extension: {file_ext}")
logger.info(f"   UUID: {unique_filename}")

# ... upload with try-catch ...
logger.info(f"   Supabase upload response: {response}")
logger.debug(f"   Response type: {type(response)}")
logger.debug(f"   Response content: {str(response)[:500]}")

# ... after upload ...
logger.info(f"✅ Image uploaded successfully")
logger.info(f"   Public URL: {public_url}")
logger.info(f"   File path: {file_path}")
logger.info(f"   File size: {file_size_bytes} bytes ({file_size_mb:.2f} MB)")
```

### 3. Improved Exception Handling

**Sebelum:**
```python
except Exception as e:
    error_msg = str(e)
    logger.error(f"Error uploading image: {error_msg}", exc_info=True)
    # Check bucket error and suggest create bucket
    if "Bucket not found" in error_msg:
        raise ValueError("...Silakan buat bucket...")
    raise ValueError(f"Failed to upload: {error_msg}")
```

**Sesudah:**
```python
except Exception as upload_error:
    error_msg = str(upload_error)
    logger.error(f"❌ Supabase upload failed:")
    logger.error(f"   Bucket: {bucket_name}")
    logger.error(f"   Path: {file_path}")
    logger.error(f"   File size: {file_size_bytes} bytes")
    logger.error(f"   Error: {error_msg}")
    logger.error(f"   Error type: {type(upload_error).__name__}")
    raise  # Re-raise to be caught by outer handler

# Outer handler:
except ValueError:
    raise  # Re-raise ValueError as-is
except Exception as e:
    error_msg = str(e)
    logger.error(f"❌ Error uploading image to Supabase Storage:")
    logger.error(f"   Error: {error_msg}")
    logger.error(f"   Error type: {type(e).__name__}")
    logger.error(f"   Bucket: {bucket_name}")
    logger.error(f"   File size: {len(file_content)} bytes")
    logger.error(f"   Full traceback:", exc_info=True)
    raise ValueError(f"Failed to upload image to Supabase Storage: {error_msg}")
```

### 4. Loop Upload dengan Error Handling

**Sebelum:**
```python
for idx, img in enumerate(product_images):
    if img:
        image_bytes, file_ext = convert_base64_to_image_bytes(img)
        public_url = upload_image_to_supabase_storage(...)
        # Continue even if one fails
```

**Sesudah:**
```python
valid_product_images = [img for img in product_images if img]  # Filter out None/empty
logger.info(f"📤 Uploading {len(valid_product_images)} product_image(s) to Supabase Storage")

for idx, img in enumerate(valid_product_images):
    try:
        image_bytes, file_ext = convert_base64_to_image_bytes(img)
        file_size = len(image_bytes)
        logger.info(f"📤 Uploading product_image[{idx}] (size: {file_size} bytes)")
        
        public_url = upload_image_to_supabase_storage(...)
        logger.info(f"✅ product_image[{idx}] uploaded successfully: {public_url}")
    except Exception as e:
        logger.error(f"❌ Failed to upload product_image[{idx}]: {str(e)}")
        raise  # Stop process on failure
```

### 5. Validate Empty Files

**Sebelum:**
```python
file_content = await image_file.read()
# No validation
```

**Sesudah:**
```python
file_content = await image_file.read()
file_size = len(file_content)

if file_size == 0:
    raise HTTPException(
        status_code=422,
        detail="Empty file uploaded. Please upload a valid image file."
    )
```

### 6. Public URL Error Handling

**Sebelum:**
```python
public_url = supabase.storage.from_(bucket_name).get_public_url(file_path)
# No error handling
```

**Sesudah:**
```python
try:
    public_url = supabase.storage.from_(bucket_name).get_public_url(file_path)
except Exception as url_error:
    logger.error(f"❌ Failed to get public URL: {str(url_error)}")
    raise ValueError(f"Failed to get public URL after upload: {str(url_error)}")
```

## 📋 Logging Output

### Before Upload:
```
INFO: 📤 Uploading image to Supabase Storage:
INFO:    Bucket: public
INFO:    Path: {user_id}/face/{uuid}.jpg
INFO:    File size: 245760 bytes (0.23 MB)
INFO:    File extension: .jpg
INFO:    UUID: a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg
```

### During Upload:
```
INFO:    Supabase upload response: <Response object>
DEBUG:    Response type: <class 'dict'>
DEBUG:    Response content: {...}
```

### After Upload:
```
INFO: ✅ Image uploaded successfully to Supabase Storage
INFO:    Public URL: https://...supabase.co/storage/v1/object/public/public/{user_id}/face/{uuid}.jpg
INFO:    File path: {user_id}/face/{uuid}.jpg
INFO:    File size: 245760 bytes (0.23 MB)
```

### On Error:
```
ERROR: ❌ Supabase upload failed:
ERROR:    Bucket: public
ERROR:    Path: {user_id}/face/{uuid}.jpg
ERROR:    File size: 245760 bytes
ERROR:    Error: [error message]
ERROR:    Error type: ValueError
ERROR:    Full traceback: [traceback]
```

## ✅ Benefits

1. ✅ **File stream handling** - `seek(0)` memastikan file pointer di reset
2. ✅ **Detailed logging** - File size (bytes dan MB), response Supabase, error details
3. ✅ **Error handling** - Stop process on failure, tidak continue dengan error
4. ✅ **Empty file validation** - Detect dan reject empty files
5. ✅ **Public URL error handling** - Handle error saat get public URL
6. ✅ **Better debugging** - Logging lengkap untuk troubleshooting

## 🔧 Changes Made

### Files Modified:

1. **backend/supabase_service.py**
   - Enhanced logging (file size, response, error details)
   - Improved exception handling (don't suggest create bucket)
   - Public URL error handling
   - Detailed error logging

2. **backend/main.py**
   - Added `file.file.seek(0)` for multipart uploads
   - Empty file validation
   - Enhanced logging in upload loops
   - Stop process on upload failure (raise exception)
   - Better error handling in loops

## ⚠️ Important Notes

1. **File Stream Handling**: `seek(0)` hanya dipanggil jika file object memiliki method `seek`
2. **Error Handling**: Upload failure akan stop process (raise exception), tidak continue
3. **Logging**: Logging detail membantu debugging tanpa perlu create bucket baru
4. **UUID Uniqueness**: UUID memastikan filename unik, upsert=False mencegah overwrite
5. **Public URL**: Error handling untuk get public URL setelah upload berhasil

---

**Upload handling sekarang lebih robust dengan logging detail dan error handling yang benar!**
