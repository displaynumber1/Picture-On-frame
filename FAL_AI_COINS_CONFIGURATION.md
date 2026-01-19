# Konfigurasi Fal.ai dan Pengurangan Coins

## ✅ Konfigurasi yang Sudah Diterapkan

### 1. Endpoint Fal.ai yang Digunakan

**File**: `backend/fal_service.py` (line 51)

```python
# Endpoint yang digunakan:
f"{FAL_API_BASE}/fal-ai/flux/schnell"
# Full URL: https://fal.run/fal-ai/flux/schnell
```

**Status**: ✅ **SUDAH BENAR** - Menggunakan `fal-ai/flux/schnell` sebagai default

### 2. Pengurangan Coins Setelah Generate Berhasil

**File**: `backend/main.py` (line 1229-1270)

**Endpoint**: `/api/generate-image`

**Alur:**
1. ✅ Check `coins_balance` user (minimal 1 coin)
2. ✅ Generate images menggunakan Fal.ai flux/schnell
3. ✅ **HANYA** setelah generate berhasil, kurangi `coins_balance` sebanyak **1 koin**
4. ✅ Return `remaining_coins` di response

**Kode:**
```python
@app.post("/api/generate-image")
async def generate_image_saas(...):
    # 1. Check coins balance
    coins = profile.get("coins_balance", 0)
    if coins < 1:
        raise HTTPException(status_code=403, detail="Insufficient coins...")
    
    # 2. Generate images (endpoint: https://fal.run/fal-ai/flux/schnell)
    image_urls = await fal_generate_images(request.prompt, num_images=2)
    
    # 3. Reduce coins by 1 AFTER successful generation
    updated_profile = update_user_coins(user_id, -1)
    remaining_coins = updated_profile.get("coins_balance", 0)
    
    return {
        "images": image_urls,
        "remaining_coins": remaining_coins
    }
```

### 3. Fungsi Update Coins

**File**: `backend/supabase_service.py` (line 106-138)

```python
def update_user_coins(user_id: str, coins_change: int) -> Dict[str, Any]:
    """
    Update user's coins_balance
    Reduces coins_balance by coins_change (negative value decreases)
    """
    # Get current balance
    profile = get_user_profile(user_id)
    new_balance = max(0, profile.get("coins_balance", 0) + coins_change)
    
    # Update in Supabase
    response = supabase.table("profiles").update({
        "coins_balance": new_balance
    }).eq("user_id", user_id).execute()
    
    return response.data[0]
```

## ✅ Verifikasi

### Checklist Konfigurasi:

- [x] ✅ Endpoint Fal.ai: `https://fal.run/fal-ai/flux/schnell` (SUDAH BENAR)
- [x] ✅ Check coins_balance sebelum generate (SUDAH DIPERBAIKI)
- [x] ✅ Kurangi coins_balance sebanyak 1 koin setelah generate berhasil (SUDAH DIPERBAIKI)
- [x] ✅ Pengurangan hanya terjadi jika generate berhasil (SUDAH BENAR - setelah await)
- [x] ✅ Return remaining_coins di response (SUDAH DITAMBAHKAN)
- [x] ✅ Logging untuk tracking (SUDAH DITAMBAHKAN)

## 🔄 Alur Generate Batch

1. **User klik "Generate Batch (3)"** di frontend
2. **Frontend call** `/api/generate-image` dengan prompt
3. **Backend:**
   - ✅ Check `coins_balance >= 1`
   - ✅ Generate 2 images menggunakan `https://fal.run/fal-ai/flux/schnell`
   - ✅ **Jika berhasil**: Kurangi `coins_balance` sebanyak 1 koin
   - ✅ Return images dan `remaining_coins`
4. **Frontend** menampilkan images dan update UI dengan `remaining_coins`

## 📊 Database Schema

**Tabel**: `profiles`

**Kolom yang digunakan**:
- `coins_balance` (INTEGER) - Saldo koin user
- `free_image_quota` (INTEGER) - Quota gratis (tidak digunakan untuk generate batch)

**Pengurangan coins**:
- Setiap 1 generate batch (2 images) = -1 coin
- Hanya dikurangi setelah generate **berhasil**
- Jika generate gagal (error), coins **TIDAK dikurangi**

## 🧪 Test

### Test Manual:

1. **Check coins balance sebelum generate:**
   ```sql
   SELECT user_id, coins_balance FROM profiles WHERE user_id = 'YOUR_USER_ID';
   ```

2. **Generate batch** via frontend

3. **Check coins balance setelah generate:**
   ```sql
   SELECT user_id, coins_balance FROM profiles WHERE user_id = 'YOUR_USER_ID';
   ```
   - Should decrease by 1

4. **Check log backend:**
   ```
   Generating images for user {user_id} using Fal.ai flux/schnell. Current coins: X
   Images generated successfully. Reducing coins by 1 for user {user_id}
   Coins deducted. Remaining coins for user {user_id}: X-1
   ```

## ⚠️ Catatan Penting

1. **Endpoint Fal.ai sudah benar**: `https://fal.run/fal-ai/flux/schnell`
2. **Pengurangan coins hanya terjadi setelah generate berhasil** (setelah await, jika error tidak dikurangi)
3. **Check coins dilakukan sebelum generate** (jika < 1, raise 403 error)
4. **1 generate batch = 1 coin** (bukan per image, tapi per batch request)

## 📝 Summary Perubahan

**Sebelum:**
- Menggunakan `free_image_quota`
- Mengurangi quota sebelum generate

**Sesudah:**
- ✅ Menggunakan `coins_balance`
- ✅ Mengurangi coins **setelah** generate berhasil
- ✅ Endpoint tetap: `https://fal.run/fal-ai/flux/schnell`
- ✅ Return `remaining_coins` di response
