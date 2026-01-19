# Cara Melihat Log Prompt yang Dikirim ke Fal.ai

## ✅ Status: LOGGING DAN DEBUG ENDPOINT SUDAH DITAMBAHKAN

### 3 Cara untuk Melihat Prompt yang Dikirim ke Fal.ai:

## 🔍 Method 1: Lihat di Browser Dev Tools (Termudah) ✅

### Step 1: Buka Browser Dev Tools
- Tekan `F12` atau `Ctrl+Shift+I` di browser
- Buka tab **Network**

### Step 2: Generate Batch di Frontend
- Upload produk dan face image
- Klik "Generate Batch (3)"

### Step 3: Check Network Tab
- Cari request: `generate-image` atau `api/generate-image`
- Klik request tersebut
- Buka tab **Response** atau **Preview**
- Scroll ke bawah, cari field `debug_info`

**Akan muncul:**
```json
{
  "images": ["url1", "url2"],
  "remaining_coins": 99,
  "debug_info": {
    "prompt_sent": "A Woman model for Fashion in Standing pose. IMPORTANT REFERENCE DETAILS: Product 1: brown leather bucket bag... [FULL PROMPT]",
    "prompt_length": 850,
    "model": "fal-ai/flux/schnell",
    "num_inference_steps": 7,
    "guidance_scale": 3.5,
    "has_product_images": true,
    "num_product_images": 4,
    "has_face_image": true,
    "has_background_image": false,
    "original_prompt": "A Woman model for Fashion in Standing pose..."
  }
}
```

**Field `prompt_sent` berisi FULL PROMPT yang dikirim ke Fal.ai!**

---

## 🔍 Method 2: Check Backend Terminal Logs ✅

### Step 1: Buka Terminal Backend
- Pastikan backend server sedang running
- Terminal akan menampilkan log real-time

### Step 2: Generate Batch di Frontend
- Upload produk dan face image
- Klik "Generate Batch (3)"

### Step 3: Check Terminal Backend

**Akan muncul logging lengkap seperti ini:**

```
INFO: Enhancing prompt with images using Gemini Vision for user abc123
INFO:   - Product images: 4
INFO:   - Face image: Yes
INFO:   - Background image: No
INFO: ✅ Enhanced prompt with 5 image description(s)
INFO:    Original prompt: A Woman model for Fashion in Standing pose...
INFO:    Combined descriptions: Product 1: brown leather bucket bag with drawstring closure... | Product 2: light blue straight-leg jeans... | Face/Model reference: young woman with pink hijab...
INFO: ✅ Prompt enhanced. Original length: 150, Enhanced length: 850
INFO:    === PROMPT YANG AKAN DIKIRIM KE FAL.AI ===
INFO:    A Woman model for Fashion in Standing pose. IMPORTANT REFERENCE DETAILS: Product 1: brown leather bucket bag with drawstring closure and long strap. Colors: brown leather. Materials: leather. Design: bucket bag style with drawstring closure. Key details: long strap, bucket shape. Product 2: light blue straight-leg jeans. Colors: light blue denim. Materials: denim. Design: straight-leg fit. Product 3: beige peplum blouse with ruffles. Colors: beige/cream. Materials: cotton or knit. Design: peplum hem with ruffles. Product 4: beige open-back flat shoes with square toe. Colors: beige. Materials: leather or synthetic. Design: open-back mules with square toe. Face/Model reference: young woman with pink hijab, medium-length wavy brown hair, dark eyes, light skin tone, gentle smile, wearing dark ribbed top. Generate images that ACCURATELY match the products, model face, and background from the reference images. The generated images must show the EXACT products from the reference images with accurate colors, materials, and design details. The model's face should match the reference face features. The background should match the reference background style and environment.
INFO:    === END PROMPT ===
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
INFO: 💾 Prompt saved to debug_prompt_log.json for debugging
```

**Copy log dari terminal untuk analisa!**

---

## 🔍 Method 3: Check File Log (prompt_log.json) ✅

### Step 1: Generate Batch
- Pastikan sudah generate batch setidaknya 1 kali setelah restart backend
- File `prompt_log.json` akan dibuat di folder `backend/`

### Step 2: Buka File Log
```bash
cd backend
cat prompt_log.json  # Linux/Mac
# atau
type prompt_log.json  # Windows CMD
# atau
Get-Content prompt_log.json  # Windows PowerShell
```

### Step 3: Atau Check via Python
```bash
cd backend
python -c "from debug_prompt_log import get_latest_prompt_log; import json; log = get_latest_prompt_log(); print(json.dumps(log, indent=2, ensure_ascii=False)) if log else print('No log found')"
```

**File akan berisi:**
```json
[
  {
    "timestamp": "2024-01-10T18:30:00.123456",
    "request": {
      "has_product_images": true,
      "num_product_images": 4,
      "has_face_image": true,
      "has_background_image": false,
      "original_prompt": "A Woman model for Fashion in Standing pose..."
    },
    "enhanced_prompt": "A Woman model for Fashion... IMPORTANT REFERENCE DETAILS: Product 1: brown leather bucket bag... [FULL PROMPT]",
    "fal_request": {
      "model": "fal-ai/flux/schnell",
      "prompt": "[FULL PROMPT]",
      "image_size": "square_hd",
      "num_inference_steps": 7,
      "guidance_scale": 3.5
    },
    "prompt_length": 850
  }
]
```

---

## 🔍 Method 4: Check via Debug API Endpoint ✅

### Step 1: Pastikan Sudah Generate Batch
- Generate batch setidaknya 1 kali

### Step 2: Call Debug Endpoint
```bash
# Via curl (ganti TOKEN dengan token Anda)
curl -X GET "http://localhost:8000/api/debug/last-prompt" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Atau via browser (jika sudah login):
# http://localhost:8000/api/debug/last-prompt
```

### Step 3: Response akan berisi:
```json
{
  "timestamp": "2024-01-10T18:30:00.123456",
  "request": {
    "has_product_images": true,
    "num_product_images": 4,
    "has_face_image": true,
    "has_background_image": false,
    "original_prompt": "A Woman model for Fashion..."
  },
  "enhanced_prompt": "[FULL PROMPT YANG DIKIRIM KE FAL.AI]",
  "fal_request": {
    "model": "fal-ai/flux/schnell",
    "prompt": "[FULL PROMPT]",
    "image_size": "square_hd",
    "num_inference_steps": 7,
    "guidance_scale": 3.5
  },
  "prompt_length": 850
}
```

---

## 📋 Informasi yang Bisa Dilihat dari Log:

### 1. Original Prompt (dari buildPromptFromOptions)
```
original_prompt: "A Woman model for Fashion in Standing pose, with Studio background..."
```

### 2. Gemini Vision Descriptions
```
Combined descriptions: Product 1: brown leather bucket bag... | Product 2: light blue jeans... | Face/Model reference: young woman with pink hijab...
```

### 3. Enhanced Prompt (Final yang dikirim ke Fal.ai)
```
enhanced_prompt: "A Woman model for Fashion... IMPORTANT REFERENCE DETAILS: Product 1: ... Product 2: ... Face/Model reference: ... Generate images that ACCURATELY match..."
```

### 4. Request Payload ke Fal.ai
```json
{
  "prompt": "[FULL ENHANCED PROMPT]",
  "image_size": "square_hd",
  "num_inference_steps": 7,
  "guidance_scale": 3.5
}
```

### 5. Image Info
```
num_product_images: 4
has_face_image: true
has_background_image: false
```

---

## 🔍 Checklist untuk Analisa:

1. ✅ **Check Original Prompt**
   - Apakah original prompt sudah spesifik?
   - Atau masih terlalu generic seperti "A Woman model for Fashion..."?

2. ✅ **Check Gemini Vision Descriptions**
   - Apakah Gemini Vision berhasil extract descriptions?
   - Apakah descriptions cukup detail dan akurat?
   - Contoh: "brown leather bucket bag with drawstring closure" vs "bag"

3. ✅ **Check Enhanced Prompt**
   - Apakah enhanced prompt menggabungkan semua descriptions?
   - Apakah emphasis "EXACT products" sudah ada?
   - Apakah panjang prompt cukup (tidak terlalu pendek)?

4. ✅ **Check Request Payload**
   - Apakah num_inference_steps = 7? ✅
   - Apakah guidance_scale = 3.5? (mungkin perlu dinaikkan untuk lebih strict)

5. ✅ **Compare dengan Foto Upload**
   - Apakah semua produk dideskripsikan dengan benar?
   - Apakah detail produk (colors, materials, design) akurat?
   - Apakah face reference dideskripsikan dengan benar?

---

## ✅ Recommended Method:

**Untuk Analisa Cepat:**
- ✅ **Method 1: Browser Dev Tools** (Termudah - tidak perlu copy-paste)

**Untuk Analisa Detail:**
- ✅ **Method 2: Terminal Backend** (Full logging dengan context)

**Untuk Document/Share:**
- ✅ **Method 3: File Log** (JSON format, mudah dibaca dan di-share)

**Untuk API Integration:**
- ✅ **Method 4: Debug Endpoint** (Bisa diintegrasikan dengan tool lain)

---

**Status**: ✅ **SEMUA METHOD SUDAH SIAP**

Silakan:
1. **Restart backend server** untuk apply changes
2. **Generate batch lagi** dengan foto yang sama
3. **Pilih method** yang paling mudah untuk Anda (recommended: Method 1 - Browser Dev Tools)
4. **Share log/prompt** yang Anda lihat untuk saya analisa lebih lanjut
