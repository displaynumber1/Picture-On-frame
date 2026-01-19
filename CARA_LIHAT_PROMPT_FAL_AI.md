# Cara Melihat Prompt yang Dikirim ke Fal.ai

## ✅ Status: LOGGING SUDAH DITAMBAHKAN

### Cara 1: Check Backend Terminal Logs ✅ (Recommended)

**Saat generate batch, cek terminal backend, akan muncul logging lengkap:**

```
INFO: Enhancing prompt with images using Gemini Vision for user abc123
INFO:   - Product images: 4
INFO:   - Face image: Yes
INFO:   - Background image: No
INFO: ✅ Enhanced prompt with 5 image description(s)
INFO:    Original prompt: A Woman model for Fashion in Standing pose, with Studio background...
INFO:    Combined descriptions: Product 1: brown leather bucket bag with drawstring closure... | Product 2: light blue straight-leg jeans... | Face/Model reference: young woman with pink hijab...
INFO: ✅ Prompt enhanced. Original length: 150, Enhanced length: 850
INFO:    Original prompt: A Woman model for Fashion in Standing pose...
INFO:    Enhanced prompt: A Woman model for Fashion in Standing pose. IMPORTANT REFERENCE DETAILS: Product 1: brown leather bucket bag with drawstring closure and long strap. Colors: brown leather. Materials: leather. Design: bucket bag style... | Product 2: light blue straight-leg jeans... | Face/Model reference: young woman with pink hijab, medium-length wavy brown hair...
INFO:    === PROMPT YANG AKAN DIKIRIM KE FAL.AI ===
INFO:    A Woman model for Fashion in Standing pose. IMPORTANT REFERENCE DETAILS: Product 1: brown leather bucket bag with drawstring closure and long strap. Colors: brown leather. Materials: leather. Design: bucket bag style with drawstring closure. Key details: long strap, bucket shape. Product 2: light blue straight-leg jeans. Colors: light blue denim. Materials: denim. Design: straight-leg fit. Product 3: beige peplum blouse with ruffles. Colors: beige/cream. Materials: cotton or knit. Design: peplum hem with ruffles. Product 4: beige open-back flat shoes with square toe. Colors: beige. Materials: leather or synthetic. Design: open-back mules with square toe. Face/Model reference: young woman with pink hijab, medium-length wavy brown hair, dark eyes, light skin tone, gentle smile, wearing dark ribbed top. Generate images that ACCURATELY match the products, model face, and background from the reference images. The generated images must show the EXACT products from the reference images with accurate colors, materials, and design details. The model's face should match the reference face features. The background should match the reference background style and environment.
INFO:    === END PROMPT ===
INFO: Generating images for user abc123 using Fal.ai flux/schnell. Current coins: 100
INFO: 📝 FINAL PROMPT YANG DIKIRIM KE FAL.AI:
INFO:    Model: fal-ai/flux/schnell
INFO:    Steps: 7, CFG: 3.5
INFO:    Prompt: [FULL PROMPT TEXT]
INFO:    Prompt length: 850 chars
INFO:    ==========================================
INFO: 📤 Sending request to Fal.ai for image 1/2
INFO:    Model: fal-ai/flux/schnell
INFO:    Prompt length: 850 chars
INFO:    Prompt preview: A Woman model for Fashion in Standing pose. IMPORTANT REFERENCE DETAILS: Product 1: brown leather bucket bag...
INFO: DEBUG: Full prompt: [FULL PROMPT]
INFO: DEBUG: Request payload: {
  "prompt": "[FULL PROMPT TEXT]",
  "image_size": "square_hd",
  "num_inference_steps": 7,
  "guidance_scale": 3.5
}
```

## 📋 Informasi yang Bisa Dilihat dari Log:

### 1. Original Prompt (dari buildPromptFromOptions)
```
Original prompt: A Woman model for Fashion in Standing pose, with Studio background...
```

### 2. Gemini Vision Descriptions
```
Combined descriptions: Product 1: brown leather bucket bag... | Product 2: light blue jeans... | Face/Model reference: young woman with pink hijab...
```

### 3. Enhanced Prompt (Final)
```
Enhanced prompt: A Woman model for Fashion... IMPORTANT REFERENCE DETAILS: Product 1: ... Product 2: ... Face/Model reference: ...
```

### 4. Request Payload ke Fal.ai
```
{
  "prompt": "[FULL ENHANCED PROMPT]",
  "image_size": "square_hd",
  "num_inference_steps": 7,
  "guidance_scale": 3.5
}
```

## 🔍 Diagnosis: Kenapa Hasil Tidak Sesuai?

### Checklist untuk Debug:

1. ✅ **Check Original Prompt**
   - Apakah original prompt sudah spesifik?
   - Atau masih terlalu generic?

2. ✅ **Check Gemini Vision Descriptions**
   - Apakah Gemini Vision berhasil extract descriptions?
   - Apakah descriptions cukup detail dan akurat?
   - Apakah semua produk dideskripsikan dengan benar?

3. ✅ **Check Enhanced Prompt**
   - Apakah enhanced prompt menggabungkan semua descriptions dengan benar?
   - Apakah emphasis "EXACT products" sudah ada?
   - Apakah panjang prompt tidak terlalu panjang atau terlalu pendek?

4. ✅ **Check Request Payload**
   - Apakah num_inference_steps = 7? (sudah benar)
   - Apakah guidance_scale = 3.5? (mungkin perlu dinaikkan untuk lebih strict)

### Possible Issues:

1. **Gemini Vision Description Kurang Detail** ⚠️
   - **Problem**: Deskripsi terlalu generic
   - **Fix**: ✅ Sudah diperbaiki dengan prompt yang lebih detail

2. **Enhanced Prompt Tidak Cukup Kuat** ⚠️
   - **Problem**: Reference details tidak prominent
   - **Fix**: ✅ Sudah diperbaiki dengan "IMPORTANT REFERENCE DETAILS" dan "EXACT products"

3. **CFG Terlalu Rendah** ⚠️
   - **Current**: CFG = 3.5
   - **Note**: CFG 3.5 baik untuk fast generation, tapi mungkin kurang strict
   - **Option**: Coba naikkan ke 5.0 - 7.0 untuk lebih match prompt

4. **Model Limitation** ⚠️
   - **Problem**: Model `flux/schnell` dengan 7 steps mungkin masih ada limitation
   - **Note**: Text-to-image dengan enhanced prompt, bukan image-to-image
   - **Option**: Jika masih tidak sesuai, pertimbangkan ganti ke model image-to-image

## 🎯 Cara Test:

1. **Restart backend server**
2. **Generate batch dengan foto yang sama**
3. **Copy full prompt dari log backend**
4. **Compare prompt dengan foto upload:**
   - Apakah semua produk dideskripsikan dengan benar?
   - Apakah detail produk (colors, materials, design) akurat?
   - Apakah face reference dideskripsikan dengan benar?
5. **Jika prompt sudah benar tapi hasil masih tidak sesuai:**
   - Pertimbangkan naikkan CFG (guidance_scale) ke 5.0 - 7.0
   - Atau pertimbangkan ganti ke model image-to-image

---

**Status**: ✅ **LOGGING SUDAH DITAMBAHKAN - PROMPT BISA DILIHAT DI BACKEND LOG**

Silakan:
1. Restart backend server
2. Generate batch lagi
3. Check terminal backend untuk melihat prompt lengkap yang dikirim ke Fal.ai
4. Share log tersebut untuk saya analisa lebih lanjut
