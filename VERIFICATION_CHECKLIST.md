# Checklist Verifikasi Konfigurasi fal dan Pengurangan Coins

## ✅ Konfigurasi yang Sudah Diterapkan

### 1. Endpoint fal ✅
- [x] **File**: `backend/fal_service.py` line 51
- [x] **Endpoint**: `https://fal.run/fal-ai/flux/schnell`
- [x] **Status**: SUDAH BENAR - Menggunakan model flux/schnell

```python
response = await client.post(
    f"{FAL_API_BASE}/fal-ai/flux/schnell",  # ✅ BENAR
    ...
)
```

### 2. Pengurangan Coins ✅
- [x] **File**: `backend/main.py` line 1229-1270
- [x] **Endpoint**: `/api/generate-image`
- [x] **Logic**: 
  - Check `coins_balance >= 1` sebelum generate
  - Generate images menggunakan fal flux/schnell
  - **Kurangi `coins_balance` sebanyak 1 koin** setelah generate berhasil
  - Return `remaining_coins` di response

```python
# ✅ Check coins sebelum generate
coins = profile.get("coins_balance", 0)
if coins < 1:
    raise HTTPException(status_code=403, detail="Insufficient coins...")

# ✅ Generate images (endpoint: https://fal.run/fal-ai/flux/schnell)
image_urls = await fal_generate_images(request.prompt, num_images=2)

# ✅ Kurangi coins SETELAH berhasil
updated_profile = update_user_coins(user_id, -1)  # -1 coin
remaining_coins = updated_profile.get("coins_balance", 0)

return {
    "images": image_urls,
    "remaining_coins": remaining_coins  # ✅ Return remaining coins
}
```

### 3. Frontend Interface ✅
- [x] **File**: `frontend/services/falService.ts`
- [x] **Update**: Interface `FalGenerateResponse` sudah support `remaining_coins`

```typescript
export interface FalGenerateResponse {
  images: string[];
  remaining_coins?: number;  // ✅ SUDAH DITAMBAHKAN
  remaining_quota?: number;  // Legacy field
}
```

## 📋 Verifikasi Manual

### Test 1: Verifikasi Endpoint
```bash
# Cek endpoint di backend/fal_service.py
grep -n "fal-ai/flux/schnell" backend/fal_service.py
# Expected: Line 51 dengan endpoint yang benar
```

### Test 2: Verifikasi Pengurangan Coins
```sql
-- Di Supabase SQL Editor
-- 1. Check coins balance sebelum generate
SELECT user_id, coins_balance, free_image_quota 
FROM profiles 
WHERE user_id = 'YOUR_USER_ID';

-- 2. Generate batch via frontend
-- (Klik "Generate Batch (3)")

-- 3. Check coins balance setelah generate
SELECT user_id, coins_balance, free_image_quota 
FROM profiles 
WHERE user_id = 'YOUR_USER_ID';
-- Expected: coins_balance berkurang 1, free_image_quota tidak berubah
```

### Test 3: Check Log Backend
Setelah generate batch, cek log backend harus ada:
```
INFO: Generating images for user {user_id} using fal flux/schnell. Current coins: X
INFO: Successfully generated 2/2 images from fal
INFO: Images generated successfully. Reducing coins by 1 for user {user_id}
INFO: Coins deducted. Remaining coins for user {user_id}: X-1
```

### Test 4: Check Response API
```bash
# Test endpoint langsung
curl -X POST http://localhost:8000/api/generate-image \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"prompt": "test image"}'

# Expected response:
{
  "images": ["url1", "url2"],
  "remaining_coins": X  # ✅ Harus ada field ini
}
```

## 🔍 Checklist Final

Sebelum deploy:

- [x] ✅ Endpoint fal: `https://fal.run/fal-ai/flux/schnell` (SUDAH BENAR)
- [x] ✅ Check `coins_balance >= 1` sebelum generate (SUDAH DIPERBAIKI)
- [x] ✅ Kurangi `coins_balance` sebanyak 1 setelah generate berhasil (SUDAH DIPERBAIKI)
- [x] ✅ Pengurangan hanya terjadi jika generate berhasil (SUDAH BENAR)
- [x] ✅ Return `remaining_coins` di response (SUDAH DITAMBAHKAN)
- [x] ✅ Frontend interface support `remaining_coins` (SUDAH DITAMBAHKAN)
- [x] ✅ Logging untuk tracking (SUDAH DITAMBAHKAN)
- [ ] ⏳ **Test generate batch** di frontend
- [ ] ⏳ **Verifikasi coins berkurang** di database
- [ ] ⏳ **Check log backend** untuk memastikan alur benar

## 📊 Summary Perubahan

| Item | Sebelum | Sesudah |
|------|---------|---------|
| **Endpoint fal** | `fal-ai/flux/schnell` ✅ | `fal-ai/flux/schnell` ✅ (Tidak berubah) |
| **Check Balance** | `free_image_quota` | `coins_balance` ✅ |
| **Pengurangan** | `update_user_quota(user_id, -1)` | `update_user_coins(user_id, -1)` ✅ |
| **Response Field** | `remaining_quota` | `remaining_coins` ✅ |
| **Timing Pengurangan** | Setelah generate | Setelah generate berhasil ✅ |

## 🎯 Expected Behavior

### Ketika User Klik "Generate Batch (3)":

1. **Frontend**: Call `/api/generate-image` dengan prompt
2. **Backend**: 
   - ✅ Check `coins_balance >= 1`
   - ✅ Generate 2 images menggunakan `https://fal.run/fal-ai/flux/schnell`
   - ✅ Jika berhasil: Kurangi `coins_balance` sebanyak 1 koin
   - ✅ Return images dan `remaining_coins`
3. **Database**: 
   - ✅ `coins_balance` berkurang 1
   - ✅ `free_image_quota` tidak berubah
4. **Frontend**: 
   - ✅ Tampilkan images
   - ✅ Update UI dengan `remaining_coins` (jika diperlukan)

### Jika Generate Gagal:

- ❌ `coins_balance` **TIDAK dikurangi** (karena exception terjadi sebelum `update_user_coins`)
- ❌ User mendapat error message
- ✅ Coins tetap sama seperti sebelum generate

## ⚠️ Catatan

1. **Endpoint sudah benar**: `https://fal.run/fal-ai/flux/schnell` ✅
2. **Pengurangan coins**: 1 koin per generate batch (2 images) ✅
3. **Pengurangan hanya terjadi setelah berhasil**: Ya, karena `update_user_coins` dipanggil setelah `await fal_generate_images` ✅
4. **Response termasuk remaining_coins**: Ya, untuk update UI ✅

## 🚀 Next Steps

1. **Restart backend server** untuk apply changes
2. **Test generate batch** di frontend
3. **Check database** untuk verifikasi coins berkurang
4. **Check log backend** untuk verifikasi alur
5. **Update frontend UI** jika perlu menampilkan `remaining_coins` (optional)

---

**Status**: ✅ **SEMUA PERUBAHAN SUDAH DITERAPKAN**
**Action Required**: Test generate batch dan verifikasi coins berkurang dengan benar
