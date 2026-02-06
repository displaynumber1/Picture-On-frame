# Implementasi: Support Image Upload untuk fal

## ✅ Status: SUDAH DIIMPLEMENTASI

### Implementasi: Scenario 1 (Hybrid dengan Gemini Vision)

**Alasan**: Tetap menggunakan `flux/schnell` yang cepat (< 2 detik) dan murah, sambil support image reference via prompt enhancement.

## 📋 Perubahan yang Dilakukan

### 1. Update Request Model ✅

**File**: `backend/main.py` (line 1192-1194)

```python
class GenerateImageRequest(BaseModel):
    prompt: str
    reference_image: Optional[str] = None  # ✅ SUDAH DITAMBAHKAN
    # Base64 image atau data URL (optional)
```

### 2. Function Baru: Enhance Prompt dengan Gemini Vision ✅

**File**: `backend/gemini_service.py` (line 75-155)

```python
async def enhance_prompt_with_image(prompt: str, image_base64: str) -> str:
    """
    Enhance prompt with image description using Gemini Vision API
    
    Args:
        prompt: Original text prompt
        image_base64: Base64 image string (can be data URL or pure base64)
    
    Returns:
        Enhanced prompt with image description
    """
    # 1. Extract pure base64 and mime type
    # 2. Call Gemini Vision API (gemini-2.0-flash-exp)
    # 3. Extract image description from response
    # 4. Enhance original prompt with image description
    # 5. Return enhanced prompt
```

**Model yang digunakan**: `gemini-2.0-flash-exp` (Fast model with vision support)

### 3. Update Endpoint: Enhance Prompt jika Ada Reference Image ✅

**File**: `backend/main.py` (line 1257-1272)

```python
# Enhance prompt with reference image if provided (using Gemini Vision)
prompt_to_use = request.prompt
if request.reference_image:
    try:
        from gemini_service import enhance_prompt_with_image
        logger.info(f"Enhancing prompt with reference image using Gemini Vision for user {user_id}")
        prompt_to_use = await enhance_prompt_with_image(request.prompt, request.reference_image)
        logger.info(f"✅ Prompt enhanced. Original length: {len(request.prompt)}, Enhanced length: {len(prompt_to_use)}")
    except Exception as e:
        logger.warning(f"Failed to enhance prompt with Gemini Vision: {str(e)}. Using original prompt.")
        prompt_to_use = request.prompt

# Generate dengan fal menggunakan enhanced prompt
image_urls = await fal_generate_images(prompt_to_use, num_images=2)
```

## 🔄 Alur Generate dengan Image Reference

### Flow Lengkap:

1. **Frontend**: User upload produk di STEP 1 → Klik "Generate Batch"
2. **Frontend Service**: Call `/api/generate-image` dengan:
   ```json
   {
     "prompt": "A Woman model for Fashion...",
     "reference_image": "data:image/jpeg;base64,/9j/4AAQ..." // ✅ OPTIONAL
   }
   ```
3. **Backend API** (`/api/generate-image`):
   - ✅ Check coins balance
   - ✅ **Jika ada `reference_image`**: 
     - Call Gemini Vision API (`gemini-2.0-flash-exp`)
     - Extract deskripsi dari image
     - Enhance prompt dengan deskripsi
   - ✅ Generate dengan fal menggunakan enhanced prompt
   - ✅ Kurangi coins 1
   - ✅ Return images dan remaining_coins

4. **fal** (`flux/schnell`):
   - ✅ Receive enhanced prompt (dengan deskripsi image)
   - ✅ Generate images berdasarkan enhanced prompt
   - ✅ Return image URLs

5. **Frontend**: Display images

## ✅ Keuntungan Implementasi Ini

### 1. Tetap Cepat dan Murah ✅
- ✅ Masih menggunakan `flux/schnell` (< 2 detik)
- ✅ Biaya minimal (1 coin per batch)
- ✅ Gemini Vision call cepat (gemini-2.0-flash-exp)

### 2. Support Image Reference ✅
- ✅ Bisa upload image produk sebagai reference
- ✅ Gemini Vision extract deskripsi dari image
- ✅ Prompt di-enhance dengan deskripsi
- ✅ Generate images sesuai reference

### 3. Flexible dan Robust ✅
- ✅ **Optional**: Jika tidak ada reference_image, tetap bisa generate (backward compatible)
- ✅ **Error Handling**: Jika Gemini Vision gagal, tetap pakai original prompt
- ✅ **Fallback**: Selalu ada fallback jika terjadi error

## 📊 Performance Impact

### Tanpa Image Reference:
- **Kecepatan**: < 2 detik ✅
- **Biaya**: 1 coin per batch ✅
- **API Calls**: 1 (fal)

### Dengan Image Reference:
- **Kecepatan**: ~3-5 detik (Gemini Vision + fal)
- **Biaya**: 1 coin per batch ✅ (Gemini Vision gratis/digunakan di tempat lain)
- **API Calls**: 2 (Gemini Vision + fal)

## 🔧 Testing

### Test 1: Generate Tanpa Image Reference
```bash
POST /api/generate-image
{
  "prompt": "A Woman model for Fashion in Standing pose"
}
# Expected: Generate langsung dengan fal (cepat, < 2 detik)
```

### Test 2: Generate Dengan Image Reference
```bash
POST /api/generate-image
{
  "prompt": "A Woman model for Fashion in Standing pose",
  "reference_image": "data:image/jpeg;base64,/9j/4AAQ..."
}
# Expected: 
# 1. Gemini Vision extract deskripsi (~1-2 detik)
# 2. Enhance prompt dengan deskripsi
# 3. Generate dengan fal (~2 detik)
# Total: ~3-4 detik
```

### Test 3: Generate Dengan Image Reference (Gemini Vision Error)
```bash
POST /api/generate-image
{
  "prompt": "A Woman model for Fashion in Standing pose",
  "reference_image": "invalid_base64"
}
# Expected: 
# 1. Gemini Vision error
# 2. Fallback ke original prompt (log warning)
# 3. Generate dengan fal menggunakan original prompt
# Total: < 2 detik
```

## 📝 Update Frontend (Required)

### File: `frontend/services/falService.ts`

**Update Interface**:
```typescript
export interface FalGenerateRequest {
  prompt: string;
  reference_image?: string;  // ✅ OPTIONAL - Base64 image atau data URL
}
```

**Update Function**:
```typescript
export async function generateImagesWithFal(
  prompt: string,
  numImages: number = 2,
  referenceImage?: string  // ✅ OPTIONAL
): Promise<string[]> {
  // ...
  body: JSON.stringify({
    prompt: prompt,
    reference_image: referenceImage  // ✅ Include jika ada
  } as FalGenerateRequest)
  // ...
}
```

**Update App.tsx**:
```typescript
const handleGenerate = async () => {
  // ...
  const basePrompt = await buildPromptFromOptions(state.options);
  
  // Get uploaded product image from state
  const referenceImage = state.productImage;  // ✅ Get from upload
  
  // Generate dengan reference image jika ada
  const imageUrls = await generateImagesWithFal(
    basePrompt, 
    3, 
    referenceImage  // ✅ Pass reference image
  );
  // ...
};
```

## 🎯 Summary

### ✅ Yang Sudah Diimplementasi:

1. ✅ Backend support optional `reference_image` parameter
2. ✅ Function `enhance_prompt_with_image()` untuk extract deskripsi dari image
3. ✅ Integration dengan Gemini Vision API (`gemini-2.0-flash-exp`)
4. ✅ Update endpoint `/api/generate-image` untuk enhance prompt jika ada reference image
5. ✅ Error handling dan fallback yang robust
6. ✅ Tetap menggunakan `flux/schnell` (cepat, murah)

### ⏳ Yang Perlu Dilakukan:

1. ⏳ **Update Frontend**: 
   - Update interface `FalGenerateRequest` untuk support `reference_image`
   - Update function `generateImagesWithFal()` untuk accept dan pass reference image
   - Update `App.tsx` untuk pass uploaded product image

2. ⏳ **Test**: 
   - Test generate dengan image reference
   - Test generate tanpa image reference (backward compatible)
   - Test error handling

## ✅ Status: Backend Ready!

**Backend sudah siap untuk menerima image reference**. Tinggal update frontend untuk:
1. Pass uploaded product image ke API
2. Include `reference_image` di request body

---

**Status**: ✅ **BACKEND SUDAH DIIMPLEMENTASI**
**Next Step**: Update frontend untuk pass reference image
