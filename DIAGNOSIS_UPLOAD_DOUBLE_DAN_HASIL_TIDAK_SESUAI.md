# Diagnosis: Upload Double & Hasil Foto Tidak Sama

## 🔍 Masalah yang Ditemukan

1. **Upload Double/Duplikasi di Supabase Storage**
   - Semua file ter-upload 2x (double)
   - File duplikat di folder yang sama

2. **Hasil Foto Tidak Sama dengan Lampiran**
   - Generated images tidak sesuai dengan gambar yang dikirim
   - Hasil berbeda dari input image

## 📊 Analisa Masalah 1: Upload Double

### Kemungkinan Penyebab:

1. **Loop Upload yang Duplikat**
   - Ada kemungkinan upload dipanggil 2x
   - Atau ada retry logic yang tidak di-handle

2. **Multiple Image Processing**
   - Product images di-loop dan di-upload
   - Mungkin ada upload yang terjadi di tempat berbeda

3. **Async/Await Issue**
   - Mungkin ada race condition
   - Atau await yang tidak benar

### Cek Code Upload:

**File:** `backend/main.py`

#### JSON Request (Line 1398-1477):
- Face image upload (line 1406-1425)
- Product images loop upload (line 1427-1453)
- Background image upload (line 1455-1475)

**Perlu Verifikasi:**
- Apakah ada duplicate call?
- Apakah ada retry logic?
- Apakah file path benar-benar unique (UUID)?

## 📊 Analisa Masalah 2: Hasil Foto Tidak Sama

### Parameter Image-to-Image yang Mempengaruhi:

1. **image_strength: 0.5** (FIXED)
   - Range: 0.0 - 1.0
   - 0.5 = Balanced (50% reference, 50% prompt)
   - **Jika terlalu rendah (0.3-0.4)**: Hasil lebih kreatif, kurang mirip reference
   - **Jika terlalu tinggi (0.6-0.8)**: Hasil lebih mirip reference, kurang kreatif

2. **guidance_scale: 3.5** (FIXED)
   - Range: 1.0 - 20.0
   - 3.5 = Medium-low (lebih natural, kurang strict prompt adherence)
   - **Jika terlalu rendah (1-2)**: Hasil lebih kreatif, kurang mengikuti prompt
   - **Jika terlalu tinggi (5-7)**: Hasil lebih strict mengikuti prompt, tapi bisa distort faces

3. **num_inference_steps: 7** (FIXED)
   - Range: 1 - 50
   - 7 = Fast generation (trade-off quality vs speed)
   - **Jika terlalu rendah (4-5)**: Quality lebih rendah
   - **Jika terlalu tinggi (10-15)**: Quality lebih tinggi, tapi lebih lama

### Kemungkinan Penyebab Hasil Tidak Sama:

1. **image_strength Terlalu Rendah**
   - 0.5 mungkin terlalu rendah untuk hasil yang sangat mirip
   - Perlu dinaikkan ke 0.6-0.7 untuk lebih mirip reference

2. **Prompt Interference**
   - Prompt dari frontend mungkin terlalu kuat
   - Guidance scale 3.5 mungkin terlalu rendah

3. **Model Limitation**
   - `fal-ai/flux-general/image-to-image` mungkin tidak optimal untuk exact matching
   - Perlu model yang lebih cocok untuk face/product preservation

## 🔧 Solusi yang Disarankan

### Solusi 1: Fix Upload Double (PRIORITY)

**Perlu Investigasi:**
1. Check apakah ada retry logic
2. Check apakah file path benar-benar unique (UUID)
3. Check apakah ada multiple calls ke upload function
4. Check logs untuk melihat berapa kali upload dipanggil

**Action Items:**
- [ ] Review upload logic di `backend/main.py`
- [ ] Check apakah UUID benar-benar unique
- [ ] Check logs untuk duplicate upload
- [ ] Verify file path structure

### Solusi 2: Improve Image Similarity

**Option A: Increase image_strength**

**Current:**
```python
FAL_IMAGE_STRENGTH = 0.5  # Balanced
```

**Suggested:**
```python
FAL_IMAGE_STRENGTH = 0.65  # More similar to reference (65% reference, 35% prompt)
```

**Trade-off:**
- ✅ Hasil lebih mirip reference image
- ❌ Kurang kreatif, kurang mengikuti prompt

**Option B: Increase guidance_scale**

**Current:**
```python
FAL_GUIDANCE_SCALE = 3.5  # Medium-low
```

**Suggested:**
```python
FAL_GUIDANCE_SCALE = 4.5  # Medium (more prompt adherence)
```

**Trade-off:**
- ✅ Lebih mengikuti prompt
- ⚠️ Bisa distort faces jika terlalu tinggi

**Option C: Increase num_inference_steps**

**Current:**
```python
FAL_NUM_INFERENCE_STEPS = 7  # Fast
```

**Suggested:**
```python
FAL_NUM_INFERENCE_STEPS = 10  # Better quality
```

**Trade-off:**
- ✅ Quality lebih tinggi
- ❌ Lebih lama, lebih mahal

**Option D: Kombinasi (RECOMMENDED)**

```python
FAL_IMAGE_STRENGTH = 0.65  # More similar to reference
FAL_GUIDANCE_SCALE = 4.0   # Balanced prompt adherence
FAL_NUM_INFERENCE_STEPS = 10  # Better quality
```

## 📋 Checklist Investigasi

### Upload Double:
- [ ] Check backend logs untuk duplicate upload calls
- [ ] Check file path di Supabase Storage (apakah UUID unique?)
- [ ] Check apakah ada retry logic
- [ ] Check apakah ada multiple requests dari frontend
- [ ] Check file size dan timestamp (apakah benar-benar duplicate?)

### Hasil Tidak Sama:
- [ ] Check prompt yang dikirim ke fal
- [ ] Check image_url yang dikirim ke fal
- [ ] Test dengan image_strength lebih tinggi (0.65-0.7)
- [ ] Test dengan guidance_scale lebih tinggi (4.0-4.5)
- [ ] Test dengan num_inference_steps lebih tinggi (10-12)
- [ ] Compare hasil dengan parameter berbeda

## 🎯 Recommended Actions

1. **Immediate (Upload Double):**
   - Investigate upload logic
   - Check logs untuk duplicate calls
   - Verify UUID uniqueness

2. **Immediate (Hasil Tidak Sama):**
   - Test dengan image_strength = 0.65
   - Test dengan guidance_scale = 4.0
   - Compare hasil

3. **Long-term:**
   - Consider tuning parameters berdasarkan use case
   - Consider model alternatives jika perlu exact matching
   - Add parameter configuration options

---

**Next Step: Investigate upload double issue dan test parameter tuning untuk hasil yang lebih mirip.**
