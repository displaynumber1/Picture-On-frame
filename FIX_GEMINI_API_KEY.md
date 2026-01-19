# Fix: GEMINI_API_KEY Tidak Ditemukan

## 🔴 ROOT CAUSE: GEMINI_API_KEY TIDAK DITEMUKAN

### ❌ Masalah dari Log:

```
ERROR:gemini_service:Error extracting description from product image 1: GEMINI_API_KEY tidak ditemukan
ERROR:gemini_service:Error extracting description from product image 2: GEMINI_API_KEY tidak ditemukan
ERROR:gemini_service:Error extracting description from product image 3: GEMINI_API_KEY tidak ditemukan
ERROR:gemini_service:Error extracting description from product image 4: GEMINI_API_KEY tidak ditemukan
ERROR:gemini_service:Error extracting description from face/reference model: GEMINI_API_KEY tidak ditemukan
ERROR:gemini_service:Error extracting description from background/environment: GEMINI_API_KEY tidak ditemukan
```

### 📊 Konsekuensi:

1. **Gemini Vision GAGAL** extract descriptions dari semua images
2. **Enhanced Prompt TIDAK berubah** (tetap sama dengan original):
   ```
   Original prompt: 200 chars
   Enhanced prompt: 200 chars (TIDAK BERTAMBAH!)
   ```
3. **Prompt yang dikirim ke Fal.ai TIDAK mengandung deskripsi produk:**
   ```
   Prompt: A Woman model, for Fashion, in Casual selfie using front camera pose...
   (GENERIC - TIDAK ADA DESKRIPSI PRODUK!)
   ```
4. **Hasil generate tidak sesuai foto** karena Fal.ai tidak tahu produk apa yang harus di-generate

## ✅ Solusi: Tambahkan GEMINI_API_KEY

### Step 1: Dapatkan Gemini API Key

1. Buka Google AI Studio: https://aistudio.google.com/app/apikey
2. Login dengan Google account
3. Create new API key atau gunakan existing key
4. Copy API key

### Step 2: Tambahkan ke config.env

**File**: `config.env` (di root project)

**Tambahkan:**
```
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

**Format lengkap config.env:**
```
# Fal.ai API Key for image and video generation
FAL_KEY=fb2e630a-8d36-4641-a4cc-804997d229fe:55f0fbbd1e990396fcef92ce958b4cdc

# Gemini API Key for image description extraction (required for prompt enhancement)
GEMINI_API_KEY=your_actual_gemini_api_key_here

# Supabase Configuration
SUPABASE_URL=https://vmbzsnkkgxchzfviqcux.supabase.co
SUPABASE_SERVICE_KEY=sb_secret_LwXdhKwIQljiOK0YcEPkCQ_KvbR7Pj8
```

### Step 3: Verify API Key Loaded

```bash
cd backend
python -c "import os; from pathlib import Path; from dotenv import load_dotenv; env_path = Path('..') / 'config.env'; load_dotenv(env_path); key = os.getenv('GEMINI_API_KEY'); print('GEMINI_API_KEY found:', 'YES ✅' if key and key != 'YOUR_GEMINI_API_KEY_HERE' else 'NO ❌'); print('Key format:', key[:20] + '...' if key and len(key) > 20 else key if key else 'Not set')"
```

**Expected Output:**
```
GEMINI_API_KEY found: YES ✅
Key format: AIzaSyAbc123...
```

### Step 4: Restart Backend

```bash
# Stop backend (Ctrl+C)
cd backend
python main.py
```

### Step 5: Generate Batch Lagi

Setelah restart, generate batch lagi. **Expected Log:**

**Sebelum (Dengan Error):**
```
ERROR: Error extracting description from product image 1: GEMINI_API_KEY tidak ditemukan
INFO: ✅ Prompt enhanced. Original length: 200, Enhanced length: 200 (TIDAK BERUBAH!)
INFO:    Prompt: A Woman model, for Fashion... (GENERIC, TANPA DESKRIPSI PRODUK)
```

**Sesudah (Setelah Fix):**
```
INFO: ✅ Extracted description from product image 1: brown leather bucket bag with drawstring closure...
INFO: ✅ Extracted description from product image 2: light blue straight-leg jeans...
INFO: ✅ Enhanced prompt with 5 image description(s)
INFO: ✅ Prompt enhanced. Original length: 200, Enhanced length: 850 (BERTAMBAH!)
INFO:    Prompt: A Woman model, for Fashion... IMPORTANT REFERENCE DETAILS: Product 1: brown leather bucket bag... Product 2: light blue jeans... (DENGAN DESKRIPSI PRODUK!)
```

## 📋 Checklist:

- [ ] ✅ Dapatkan Gemini API Key dari Google AI Studio
- [ ] ✅ Tambahkan `GEMINI_API_KEY=your_key_here` ke `config.env`
- [ ] ✅ Verify API key loaded (command di atas)
- [ ] ✅ Restart backend server
- [ ] ✅ Generate batch lagi
- [ ] ✅ Check log - tidak ada error GEMINI_API_KEY
- [ ] ✅ Check log - prompt length bertambah (dari 200 menjadi 800-1000+ chars)
- [ ] ✅ Check log - prompt mengandung deskripsi produk
- [ ] ✅ Check hasil generate - seharusnya lebih sesuai dengan foto upload

## 🎯 Expected Result Setelah Fix:

### Prompt yang Dikirim ke Fal.ai:

**Sebelum (Tanpa GEMINI_API_KEY):**
```
A Woman model, for Fashion, in Casual selfie using front camera pose, in Studio Clean style...
(200 chars - GENERIC, TANPA DESKRIPSI PRODUK)
```

**Sesudah (Dengan GEMINI_API_KEY):**
```
A Woman model, for Fashion, in Casual selfie using front camera pose, in Studio Clean style. 
IMPORTANT REFERENCE DETAILS: 
Product 1: brown leather bucket bag with drawstring closure and long strap. Colors: brown leather. Materials: leather. Design: bucket bag style with drawstring closure. Key details: long strap, bucket shape, brown color. 
Product 2: light blue straight-leg jeans. Colors: light blue denim. Materials: denim fabric. Design: straight-leg fit, standard waist. 
Product 3: beige peplum blouse with ruffles. Colors: beige/cream. Materials: cotton or knit fabric. Design: peplum hem with ruffles, long sleeves. 
Product 4: beige open-back flat shoes with square toe. Colors: beige/tan. Materials: leather or synthetic. Design: open-back mules, square toe, flat sole. 
Face/Model reference: young woman with pink hijab, medium-length wavy brown hair, dark eyes, light skin tone, gentle smile, wearing dark ribbed top. 
Background/Environment: [deskripsi background jika ada]
Generate images that ACCURATELY match the products, model face, and background from the reference images. 
The generated images must show the EXACT products from the reference images with accurate colors, materials, and design details. 
The model's face should match the reference face features. 
The background should match the reference background style and environment.
(800-1000+ chars - DENGAN DESKRIPSI PRODUK LENGKAP!)
```

## ✅ Status:

**Root Cause**: ✅ **DITEMUKAN** - GEMINI_API_KEY tidak ditemukan
**Solusi**: ✅ **SUDAH DITAMBAHKAN TEMPLATE** di config.env
**Action Required**: ⏳ **USER PERLU TAMBAHKAN GEMINI_API_KEY NYA**

Silakan:
1. Buka Google AI Studio: https://aistudio.google.com/app/apikey
2. Dapatkan Gemini API Key
3. Tambahkan ke `config.env`:
   ```
   GEMINI_API_KEY=your_actual_key_here
   ```
4. Restart backend
5. Generate batch lagi
6. Check log - seharusnya tidak ada error dan prompt akan mengandung deskripsi produk!

---

**Status**: 🔴 **ROOT CAUSE: GEMINI_API_KEY TIDAK DITEMUKAN - PERLU DITAMBAHKAN**
