# Fix: Upload Multiple Images ke Supabase Storage

## 🔍 Masalah yang Ditemukan

Backend hanya mengupload **SATU gambar** ke Supabase Storage dengan prioritas:
1. `face_image` (jika ada)
2. `product_images[0]` (jika ada)
3. `background_image` (jika ada)

Ini berarti:
- ❌ Jika user upload multiple product images, hanya yang pertama yang diupload
- ❌ Jika user upload face_image + product_images, hanya face_image yang diupload
- ❌ Background image hanya diupload jika tidak ada face_image dan product_images
- ❌ User kehilangan images lainnya yang tidak terupload

## ✅ Solusi yang Diterapkan

### 1. Upload ALL Images ke Supabase Storage

**Sebelum:**
```python
# Hanya upload satu image (prioritas pertama)
if face_image:
    # Upload face_image only
elif product_images:
    # Upload product_images[0] only
elif background_image:
    # Upload background_image only
```

**Sesudah:**
```python
# Upload ALL images to Supabase Storage
uploaded_images = []  # Store all uploaded image URLs

# 1. Upload face_image if provided
if face_image:
    public_url = upload_image_to_supabase_storage(...)
    uploaded_images.append({"type": "face_image", "url": public_url})

# 2. Upload ALL product_images if provided
if product_images:
    for idx, img in enumerate(product_images):
        if img:
            public_url = upload_image_to_supabase_storage(...)
            uploaded_images.append({"type": f"product_image_{idx}", "url": public_url})

# 3. Upload background_image if provided
if background_image:
    public_url = upload_image_to_supabase_storage(...)
    uploaded_images.append({"type": "background_image", "url": public_url})
```

### 2. Gunakan Priority untuk fal Generation

**Primary Image untuk fal** (prioritas tetap sama):
1. `face_image` (jika ada) - **Primary untuk generation**
2. `product_images[0]` (jika tidak ada face_image) - **Primary untuk generation**
3. `background_image` (jika tidak ada face_image dan product_images) - **Primary untuk generation**

**Semua images diupload ke Supabase Storage**, tapi hanya **satu primary image** yang digunakan untuk fal generation (sesuai API limitation).

## 📋 Perilaku Baru

### Scenario 1: User Upload face_image + 4 product_images + background_image

**Yang Terjadi:**
1. ✅ **Semua 6 images diupload** ke Supabase Storage:
   - `face_image_userid.jpg`
   - `product_image_0_userid.jpg`
   - `product_image_1_userid.jpg`
   - `product_image_2_userid.jpg`
   - `product_image_3_userid.jpg`
   - `background_image_userid.jpg`

2. ✅ **Primary image untuk fal:** `face_image` (karena prioritas tertinggi)

3. ✅ **Log:**
   ```
   INFO: ✅ Total 6 image(s) uploaded to Supabase Storage
   INFO:    Primary image for fal generation: face_image (https://...)
   ```

### Scenario 2: User Upload 4 product_images saja (tanpa face_image)

**Yang Terjadi:**
1. ✅ **Semua 4 product images diupload** ke Supabase Storage:
   - `product_image_0_userid.jpg`
   - `product_image_1_userid.jpg`
   - `product_image_2_userid.jpg`
   - `product_image_3_userid.jpg`

2. ✅ **Primary image untuk fal:** `product_image_0` (yang pertama)

3. ✅ **Log:**
   ```
   INFO: ✅ Total 4 image(s) uploaded to Supabase Storage
   INFO:    Primary image for fal generation: product_image_0 (https://...)
   ```

### Scenario 3: User Upload background_image saja

**Yang Terjadi:**
1. ✅ **background_image diupload** ke Supabase Storage:
   - `background_image_userid.jpg`

2. ✅ **Primary image untuk fal:** `background_image`

3. ✅ **Log:**
   ```
   INFO: ✅ Total 1 image(s) uploaded to Supabase Storage
   INFO:    Primary image for fal generation: background_image (https://...)
   ```

## 📊 Perubahan File

### `backend/main.py`

1. **Upload ALL images ke Supabase Storage:**
   - Upload face_image (jika ada)
   - Upload semua product_images (jika ada)
   - Upload background_image (jika ada)

2. **Priority untuk fal:**
   - Gunakan `primary_image_url` sesuai prioritas
   - Simpan semua `uploaded_images` untuk logging/debugging

3. **Enhanced Logging:**
   - Log total images uploaded
   - Log primary image type dan URL
   - Log semua uploaded image URLs

4. **Enhanced Debug Info:**
   - Include `all_uploaded_images` di prompt log
   - Include `primary_image_type` di prompt log

## ✅ Benefits

1. ✅ **Tidak ada image yang hilang** - Semua images diupload ke Supabase Storage
2. ✅ **Storage/Backup** - Semua images tersimpan untuk referensi
3. ✅ **Priority tetap** - Face image tetap prioritas untuk generation
4. ✅ **Logging lengkap** - User bisa lihat semua images yang diupload
5. ✅ **Fleksibel** - Bisa digunakan untuk future features (multiple images, comparison, dll)

## ⚠️ Catatan Penting

### fal API Limitation

**fal `flux-general/image-to-image` hanya menerima SATU `image_url`:**
```json
{
  "image_url": "https://...",  // SINGULAR, not array
  "image_strength": 0.5,
  ...
}
```

**Oleh karena itu:**
- ✅ Semua images diupload ke Supabase Storage (untuk storage/backup)
- ✅ Hanya **satu primary image** yang digunakan untuk fal generation
- ✅ Priority: face_image > product_images[0] > background_image

### Future Enhancement

Jika di masa depan fal support multiple images atau kita ingin implementasi custom logic:
- ✅ Semua images sudah tersimpan di Supabase Storage
- ✅ Bisa diakses dari `uploaded_images` list
- ✅ Bisa digunakan untuk comparison, blending, atau batch processing

## 🎯 Expected Behavior

### Request dengan Multiple Images:

```json
{
  "prompt": "...",
  "product_images": [
    "data:image/jpeg;base64,/9j/4AAQ...",  // Image 1
    "data:image/jpeg;base64,/9j/4AAQ...",  // Image 2
    "data:image/jpeg;base64,/9j/4AAQ...",  // Image 3
    "data:image/jpeg;base64,/9j/4AAQ..."   // Image 4
  ],
  "face_image": "data:image/jpeg;base64,/9j/4AAQ...",
  "background_image": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

### Response Log:

```
INFO: 📤 Uploading face_image to Supabase Storage
INFO: ✅ face_image uploaded to Supabase Storage: https://...supabase.co/.../face_image_userid.jpg
INFO: 📤 Uploading product_image[0] to Supabase Storage
INFO: ✅ product_image[0] uploaded to Supabase Storage: https://...supabase.co/.../product_image_0_userid.jpg
INFO: 📤 Uploading product_image[1] to Supabase Storage
INFO: ✅ product_image[1] uploaded to Supabase Storage: https://...supabase.co/.../product_image_1_userid.jpg
INFO: 📤 Uploading product_image[2] to Supabase Storage
INFO: ✅ product_image[2] uploaded to Supabase Storage: https://...supabase.co/.../product_image_2_userid.jpg
INFO: 📤 Uploading product_image[3] to Supabase Storage
INFO: ✅ product_image[3] uploaded to Supabase Storage: https://...supabase.co/.../product_image_3_userid.jpg
INFO: 📤 Uploading background_image to Supabase Storage
INFO: ✅ background_image uploaded to Supabase Storage: https://...supabase.co/.../background_image_userid.jpg
INFO: ✅ Total 6 image(s) uploaded to Supabase Storage
INFO:    Primary image for fal generation: face_image (https://...supabase.co/.../face_image_userid.jpg)
INFO:    Image-to-image pipeline: Using face_image as reference
```

### Payload ke fal:

```json
{
  "prompt": "...",
  "image_url": "https://...supabase.co/.../face_image_userid.jpg",  // Primary image (face_image)
  "image_strength": 0.5,
  "num_inference_steps": 7,
  "guidance_scale": 3.5
}
```

---

**Sekarang SEMUA images yang dikirim user akan diupload ke Supabase Storage!**
