# Diagnosis Error: generate_images() got an unexpected keyword argument 'num_images'

## Error yang Terjadi

### Frontend Error:
```
SERVER ERROR: GENERATE_IMAGES() GOT AN UNEXPECTED KEYWORD ARGUMENT 'NUM_IMAGES'.
SILAKAN COBA LAGI NANTI.
```

### Backend Error:
```
TypeError: generate_images() got an unexpected keyword argument 'num_images'
File "C:\project-gemini-ai\backend\main.py", line 1256
image_urls = await generate_images(request.prompt, num_images=2)
```

## Diagnosis

### Masalah: Name Conflict

Ada **2 fungsi dengan nama `generate_images`** yang berbeda signature:

1. **Di `fal_service.py` (line 27):**
   ```python
   async def generate_images(prompt: str, num_images: int = 2) -> List[str]:
   ```
   ✅ **Ini yang benar** - menerima `num_images` parameter

2. **Di `main.py` (line 1003):**
   ```python
   async def generate_images(request: GenerateRequest):
   ```
   ❌ **Ini endpoint function** - tidak menerima `num_images`

### Root Cause:

Di `main.py` line 18, ada import:
```python
from fal_service import generate_images, generate_video as fal_generate_video
```

Tapi kemudian di `main.py` line 1003, ada definisi fungsi dengan nama yang sama:
```python
async def generate_images(request: GenerateRequest):
```

**Python menggunakan fungsi yang terakhir didefinisikan** (local scope), jadi ketika memanggil `generate_images(request.prompt, num_images=2)` di line 1256, Python menggunakan fungsi endpoint di `main.py` yang tidak menerima `num_images`.

## Solusi yang Sudah Diterapkan

### 1. Rename Import dari fal_service

**Sebelum:**
```python
from fal_service import generate_images, generate_video as fal_generate_video
```

**Sesudah:**
```python
from fal_service import generate_images as fal_generate_images, generate_video as fal_generate_video
```

### 2. Update Pemanggilan Fungsi

**Sebelum:**
```python
image_urls = await generate_images(request.prompt, num_images=2)
```

**Sesudah:**
```python
image_urls = await fal_generate_images(request.prompt, num_images=2)
```

## Verifikasi

Setelah perbaikan:

1. **Restart backend server:**
   ```bash
   cd backend
   python main.py
   ```

2. **Test Generate Batch di frontend:**
   - Klik "Generate Batch (3)"
   - Tidak boleh ada error "unexpected keyword argument 'num_images'"
   - Request harus berhasil

3. **Cek log backend:**
   - Tidak ada TypeError
   - Harus ada log: "Successfully generated 2/2 images from Fal.ai"

## Struktur Fungsi Setelah Perbaikan

### fal_service.py:
```python
async def generate_images(prompt: str, num_images: int = 2) -> List[str]:
    # Generate images using Fal.ai
    ...
```

### main.py:
```python
# Import dengan alias
from fal_service import generate_images as fal_generate_images

# Endpoint function (tetap dengan nama generate_images)
@app.post("/api/generate")
async def generate_images(request: GenerateRequest):
    # Legacy endpoint
    ...

# SaaS endpoint menggunakan fal_generate_images
@app.post("/api/generate-image")
async def generate_image_saas(...):
    # Menggunakan fal_generate_images dari fal_service
    image_urls = await fal_generate_images(request.prompt, num_images=2)
    ...
```

## Checklist

- [x] ✅ Import dari `fal_service` sudah di-rename menjadi `fal_generate_images`
- [x] ✅ Pemanggilan di `/api/generate-image` sudah di-update
- [ ] ⏳ Backend server sudah di-restart
- [ ] ⏳ Test Generate Batch berhasil (tidak ada error)
- [ ] ⏳ Images berhasil di-generate

## Catatan

- **Name conflict** adalah masalah umum di Python ketika ada fungsi dengan nama sama di scope yang berbeda
- **Best practice**: Gunakan alias untuk import jika ada kemungkinan name conflict
- **Endpoint function** di `main.py` tetap bisa menggunakan nama `generate_images` karena itu adalah route handler, bukan utility function
