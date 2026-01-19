# Solusi: Upload Double & Hasil Foto Tidak Sama

## 🔍 Analisa Masalah

### Masalah 1: Upload Double/Duplikasi

Dari screenshot Supabase Storage, terlihat struktur folder:
- `face/` (folder)
- `13ab4cf1-8587-4685-874b-...` (folder dengan UUID)
- `background/` (folder)
- `face/` (folder lagi - duplikasi?)
- `product/` (folder)
- Files dengan UUID (duplikasi?)

**Kemungkinan Penyebab:**
1. Multiple requests dari frontend (user klik 2x?)
2. UUID tidak unique (sangat tidak mungkin)
3. Struktur path yang salah (folder nested)
4. Upload dipanggil 2x di code (perlu verify)

### Masalah 2: Hasil Foto Tidak Sama

**Parameter Current:**
- `image_strength: 0.5` → Terlalu rendah untuk exact matching
- `guidance_scale: 3.5` → Medium-low (kurang strict)
- `num_inference_steps: 7` → Fast generation (quality trade-off)

**Kemungkinan Penyebab:**
- `image_strength: 0.5` terlalu rendah → hasil 50% reference, 50% prompt
- Untuk hasil yang lebih mirip, perlu `image_strength: 0.65-0.7`

## ✅ Solusi yang Disarankan

### Solusi 1: Investigate Upload Double (PRIORITY)

**Perlu Verify:**
1. Apakah UUID benar-benar unique?
2. Apakah ada multiple requests dari frontend?
3. Apakah struktur folder benar?

**Action Items:**
- [ ] Check backend logs untuk duplicate upload calls
- [ ] Check apakah user klik generate 2x (frontend issue?)
- [ ] Verify UUID uniqueness (should be unique per upload)
- [ ] Check file timestamps (apakah upload waktu yang sama?)

### Solusi 2: Improve Image Similarity (RECOMMENDED)

**Tuning Parameters untuk Hasil Lebih Mirip:**

**Option A: Increase image_strength (RECOMMENDED)**

**Current:**
```python
FAL_IMAGE_STRENGTH = 0.5  # 50% reference, 50% prompt
```

**Suggested:**
```python
FAL_IMAGE_STRENGTH = 0.65  # 65% reference, 35% prompt (lebih mirip)
```

**Trade-off:**
- ✅ Hasil lebih mirip reference image
- ✅ Face/product identity lebih preserved
- ⚠️ Kurang kreatif, kurang mengikuti prompt detail

**Option B: Kombinasi (BEST for Similarity)**

```python
FAL_IMAGE_STRENGTH = 0.65  # More similar to reference
FAL_GUIDANCE_SCALE = 4.0   # Balanced prompt adherence
FAL_NUM_INFERENCE_STEPS = 10  # Better quality
```

**Trade-off:**
- ✅ Hasil lebih mirip reference
- ✅ Quality lebih tinggi
- ✅ Balanced prompt adherence
- ❌ Lebih lama (10 steps vs 7)
- ❌ Lebih mahal (more inference steps)

## 🔧 Implementation

### Step 1: Fix Upload Double (Investigation First)

**Perlu check:**
1. Backend logs - apakah upload dipanggil 2x?
2. Frontend - apakah user klik generate 2x?
3. UUID - apakah benar-benar unique?

**Jika memang ada duplicate calls:**
- Add idempotency check
- Add request deduplication
- Add rate limiting

### Step 2: Tune Parameters untuk Similarity

**File:** `backend/fal_service.py`

**Change:**
```python
# Current
FAL_IMAGE_STRENGTH = 0.5

# Recommended
FAL_IMAGE_STRENGTH = 0.65  # More similar to reference
```

**Optional (Better Quality):**
```python
FAL_IMAGE_STRENGTH = 0.65
FAL_GUIDANCE_SCALE = 4.0
FAL_NUM_INFERENCE_STEPS = 10
```

## 📋 Checklist

### Upload Double:
- [ ] Check backend logs untuk duplicate calls
- [ ] Check frontend logs (apakah generate dipanggil 2x?)
- [ ] Verify UUID uniqueness di Supabase Storage
- [ ] Check file timestamps
- [ ] Check file sizes (apakah sama persis?)
- [ ] Verify struktur folder (apakah ada nested folder yang salah?)

### Hasil Tidak Sama:
- [ ] Update `FAL_IMAGE_STRENGTH` ke 0.65
- [ ] (Optional) Update `FAL_GUIDANCE_SCALE` ke 4.0
- [ ] (Optional) Update `FAL_NUM_INFERENCE_STEPS` ke 10
- [ ] Test dengan parameter baru
- [ ] Compare hasil dengan parameter lama vs baru
- [ ] Verify hasil lebih mirip dengan reference

## 🎯 Recommended Actions

1. **Immediate (Upload Double):**
   - Investigate penyebab duplicate upload
   - Check logs untuk duplicate calls
   - Verify UUID uniqueness

2. **Immediate (Hasil Tidak Sama):**
   - Update `FAL_IMAGE_STRENGTH` ke 0.65
   - Test dengan parameter baru
   - Compare hasil

3. **Long-term:**
   - Add idempotency check untuk upload
   - Consider parameter tuning berdasarkan use case
   - Add configuration options untuk parameter

---

**Next Step: Investigate upload double issue dan test dengan image_strength = 0.65 untuk hasil yang lebih mirip.**
