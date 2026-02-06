# Konfigurasi Terkunci: fal Model dan Parameter

## 🔒 Konfigurasi yang Dikunci

### Model: `fal-ai/flux/schnell` (LOCKED)
- **Endpoint**: `https://fal.run/fal-ai/flux/schnell`
- **Alasan**: Sangat cepat (< 2 detik), sangat hemat biaya
- **Status**: ✅ **TERKUNCI** - Tidak boleh diubah

### Parameter: `num_inference_steps = 4` (LOCKED)
- **Value**: `4` (minimum)
- **Alasan**: Untuk kecepatan maksimal dan biaya minimal
- **Status**: ✅ **TERKUNCI** - Harus selalu 4

## 📍 Lokasi Konfigurasi

### File: `backend/fal_service.py`

**Konstanta yang Dikunci** (line 24-31):
```python
# LOCKED CONFIGURATION: Model dan parameter untuk optimasi biaya dan kecepatan
FAL_MODEL_ENDPOINT = "fal-ai/flux/schnell"  # LOCKED: Hanya gunakan model ini
FAL_NUM_INFERENCE_STEPS = 4  # LOCKED: Harus 4 untuk kecepatan maksimal dan biaya minimal
FAL_GUIDANCE_SCALE = 3.5  # Optimal untuk flux/schnell dengan 4 steps
FAL_IMAGE_SIZE = "square_hd"  # Standard size untuk konsistensi
```

**Validasi di Function** (line 42-46):
```python
# Validate locked configuration
if FAL_MODEL_ENDPOINT != "fal-ai/flux/schnell":
    raise ValueError(f"Model endpoint is locked to 'fal-ai/flux/schnell'. Current: {FAL_MODEL_ENDPOINT}")
if FAL_NUM_INFERENCE_STEPS != 4:
    raise ValueError(f"num_inference_steps is locked to 4 for cost optimization. Current: {FAL_NUM_INFERENCE_STEPS}")
```

**Penggunaan di Request** (line 57-63):
```python
response = await client.post(
    f"{FAL_API_BASE}/{FAL_MODEL_ENDPOINT}",  # Menggunakan konstanta
    ...
    json={
        "prompt": prompt,
        "image_size": FAL_IMAGE_SIZE,
        "num_inference_steps": FAL_NUM_INFERENCE_STEPS,  # LOCKED: 4
        "guidance_scale": FAL_GUIDANCE_SCALE
    }
)
```

## ✅ Keuntungan Konfigurasi Ini

### 1. Kecepatan
- **< 2 detik** per generate
- Model `flux/schnell` adalah fastest model di fal
- `num_inference_steps: 4` adalah minimum untuk hasil cepat

### 2. Biaya
- **Sangat murah** per generate
- `num_inference_steps: 4` = biaya minimal
- Model `flux/schnell` lebih murah daripada `flux` atau `flux-pro`

### 3. Konsistensi
- Semua generate menggunakan konfigurasi yang sama
- Tidak ada variasi yang bisa meningkatkan biaya
- Predictable cost per generate

## 🚫 Yang TIDAK BOLEH Diubah

### ❌ Jangan Ubah Model Endpoint
```python
# ❌ SALAH - Jangan lakukan ini:
FAL_MODEL_ENDPOINT = "fal-ai/flux"  # Bukan schnell, lebih lambat dan lebih mahal
FAL_MODEL_ENDPOINT = "fal-ai/flux-pro"  # Premium, sangat mahal
```

### ❌ Jangan Ubah num_inference_steps
```python
# ❌ SALAH - Jangan lakukan ini:
FAL_NUM_INFERENCE_STEPS = 28  # Standard flux, lebih lambat dan lebih mahal
FAL_NUM_INFERENCE_STEPS = 50  # High quality, sangat lambat dan sangat mahal
```

### ❌ Jangan Hardcode di Function
```python
# ❌ SALAH - Jangan hardcode:
json={
    "num_inference_steps": 28,  # Jangan hardcode, gunakan konstanta
    ...
}

# ✅ BENAR - Gunakan konstanta:
json={
    "num_inference_steps": FAL_NUM_INFERENCE_STEPS,  # Gunakan konstanta
    ...
}
```

## 🔍 Verifikasi

### Test 1: Cek Konstanta
```python
# Di Python console atau test script
from backend.fal_service import FAL_MODEL_ENDPOINT, FAL_NUM_INFERENCE_STEPS

assert FAL_MODEL_ENDPOINT == "fal-ai/flux/schnell", "Model endpoint harus fal-ai/flux/schnell"
assert FAL_NUM_INFERENCE_STEPS == 4, "num_inference_steps harus 4"
print("✅ Konfigurasi terkunci dengan benar")
```

### Test 2: Cek Request yang Dikirim
Setelah generate, cek log backend harus menunjukkan:
```
INFO: Generating images using fal flux/schnell
INFO: Request payload: {"prompt": "...", "num_inference_steps": 4, ...}
```

### Test 3: Cek Response Time
Generate batch harus selesai dalam **< 2 detik** per image.

## 📊 Perbandingan Biaya dan Kecepatan

| Model | num_inference_steps | Speed | Cost | Status |
|-------|---------------------|-------|------|--------|
| **flux/schnell** | **4** | **< 2s** | **$0.001** | ✅ **LOCKED** |
| flux/schnell | 8 | ~3s | $0.002 | ❌ Lebih mahal |
| flux | 4 | ~5s | $0.003 | ❌ Lebih lambat & mahal |
| flux | 28 | ~15s | $0.010 | ❌ Sangat lambat & mahal |
| flux-pro | 28 | ~20s | $0.025 | ❌ Premium, sangat mahal |

**Kesimpulan**: Konfigurasi terkunci (`flux/schnell` + `4 steps`) adalah **paling cepat dan paling murah**.

## 🛡️ Proteksi

### 1. Konstanta Terkunci
- Semua parameter menggunakan konstanta
- Tidak ada hardcode di function

### 2. Validasi Runtime
- Function `generate_images()` memvalidasi konstanta saat runtime
- Jika konstanta diubah, akan raise ValueError

### 3. Dokumentasi
- Komentar jelas di setiap konstanta
- Dokumentasi lengkap di function docstring

## 📝 Catatan Penting

1. **Jangan ubah konstanta** tanpa alasan yang sangat kuat
2. **Jika perlu ubah**, pastikan:
   - Ada alasan bisnis yang jelas
   - Memahami impact pada biaya dan kecepatan
   - Update dokumentasi
   - Test thoroughly

3. **Konfigurasi saat ini optimal untuk**:
   - Cost efficiency (biaya minimal)
   - Speed (kecepatan maksimal)
   - User experience (generate cepat)

## ✅ Checklist

- [x] ✅ Model endpoint: `fal-ai/flux/schnell` (LOCKED)
- [x] ✅ num_inference_steps: `4` (LOCKED)
- [x] ✅ Konstanta didefinisikan di top level
- [x] ✅ Validasi runtime untuk memastikan konstanta tidak diubah
- [x] ✅ Semua request menggunakan konstanta (tidak hardcode)
- [x] ✅ Dokumentasi lengkap dengan alasan
- [x] ✅ Komentar jelas di setiap konstanta

---

**Status**: ✅ **KONFIGURASI TERKUNCI**
**Model**: `fal-ai/flux/schnell`
**num_inference_steps**: `4`
**Tujuan**: Kecepatan maksimal (< 2s) dan biaya minimal
