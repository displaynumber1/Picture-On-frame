# Langkah Selanjutnya Setelah Policy Dibuat

## Status Saat Ini ✅

Berdasarkan screenshot yang Anda tunjukkan:
- ✅ Policy "Service role can do everything" **BERHASIL DIBUAT**
- ✅ Hasil: "Success. No rows returned" (normal untuk CREATE POLICY)

## Langkah Verifikasi Selanjutnya

### 1. Verifikasi Setup Lengkap dengan SQL

Jalankan script verifikasi di Supabase SQL Editor:

1. **Buka Supabase SQL Editor**
2. **Buka file `VERIFY_SUPABASE_SETUP.sql`** (di root project)
3. **Copy seluruh isi SQL**
4. **Paste ke SQL Editor dan Run**
5. **Periksa hasil setiap query:**

   **Query 1 - Tabel profiles harus ada:**
   ```
   ✅ Harus return: table_name='profiles', table_schema='public'
   ```

   **Query 2 - Struktur tabel harus lengkap:**
   ```
   ✅ Harus ada 7 kolom:
   - id (uuid)
   - user_id (uuid)
   - free_image_quota (integer)
   - coins_balance (integer)
   - created_at (timestamp)
   - updated_at (timestamp)
   ```

   **Query 3 - RLS harus enabled:**
   ```
   ✅ rls_enabled harus = true
   ```

   **Query 4 - Policies harus ada:**
   ```
   ✅ Harus ada minimal 3 policies:
   - "Users can view own profile" (SELECT)
   - "Users can update own profile" (UPDATE)
   - "Service role can do everything" (ALL) ← Yang baru dibuat
   ```

   **Query 5 - Trigger harus ada:**
   ```
   ✅ Harus ada trigger: on_auth_user_created
   ```

   **Query 6 - Function harus ada:**
   ```
   ✅ Harus ada function: handle_new_user
   ```

### 2. Refresh Schema Cache (PENTING!)

**Ini adalah langkah terpenting!** Meskipun policy sudah dibuat, Supabase PostgREST schema cache mungkin belum update.

#### Cara 1: Via Supabase Dashboard (Recommended)
1. Buka **Supabase Dashboard**
2. Pilih project Anda
3. Buka **Database** > **Replication** (atau **Settings** > **Database**)
4. Cari opsi **"Reload Schema"** atau **"Refresh Schema Cache"**
5. **Klik untuk refresh**
6. **Tunggu 1-2 menit** untuk proses selesai

#### Cara 2: Via SQL (Jika memiliki permission)
```sql
-- Jalankan di SQL Editor
NOTIFY pgrst, 'reload schema';
```
*Note: Ini mungkin tidak bekerja tanpa superuser permission*

#### Cara 3: Auto-refresh (Wait)
- Schema cache biasanya auto-refresh setiap **2-3 menit**
- Tunggu 2-3 menit setelah membuat policy

### 3. Verifikasi Service Role Key

Pastikan `SUPABASE_SERVICE_KEY` di `config.env` adalah **service_role key** yang benar:

1. **Buka Supabase Dashboard > Settings > API**
2. **Di bagian "Project API keys":**
   - **anon/public key**: Pendek, aman untuk frontend (❌ Bukan ini!)
   - **service_role key**: Panjang, merah, secret (✅ Ini yang digunakan!)

3. **Copy service_role key** (yang merah, secret)
4. **Update `config.env`:**
   ```env
   SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # Service role key yang panjang
   ```

### 4. Test Manual UPDATE (Optional)

Test apakah UPDATE benar-benar bekerja:

```sql
-- Di Supabase SQL Editor
-- Ganti USER_ID_HERE dengan actual user_id dari query sebelumnya

-- Cek data existing
SELECT * FROM public.profiles 
WHERE user_id = 'USER_ID_HERE';

-- Test UPDATE (dengan rollback untuk safety)
BEGIN;
UPDATE public.profiles 
SET free_image_quota = free_image_quota  -- Set ke nilai yang sama
WHERE user_id = 'USER_ID_HERE';
ROLLBACK;  -- Jangan commit, hanya test!
```

**Jika UPDATE berhasil:**
- ✅ Schema cache sudah refresh
- ✅ Policy bekerja dengan benar

**Jika UPDATE gagal dengan PGRST205:**
- ❌ Schema cache belum refresh
- 💡 Tunggu 2-3 menit atau refresh manual

### 5. Restart Backend Server

Setelah refresh schema cache:

```bash
# Stop backend server (Ctrl+C di terminal)
cd backend
python main.py  # Start ulang
```

### 6. Test di Frontend

1. **Hard refresh browser:** `Ctrl + Shift + R` (Windows) / `Cmd + Shift + R` (Mac)
2. **Login ulang** jika perlu
3. **Upload produk** (jika belum)
4. **Klik "Generate Batch (3)"**
5. **Hasil yang diharapkan:**
   - ✅ Tidak ada error 500
   - ✅ Tidak ada error 404
   - ✅ Request berhasil (200 OK)
   - ✅ Gambar berhasil di-generate

## Troubleshooting

### Jika Masih Error 500 (PGRST205)

1. **Tunggu 2-3 menit** setelah refresh schema cache
2. **Restart backend server** setelah refresh
3. **Verifikasi service_role key** di config.env benar
4. **Cek log backend** untuk detail error
5. **Test manual UPDATE** di SQL Editor (lihat Step 4)

### Jika Masih Error 404

1. **Pastikan backend server berjalan** di port 8000
2. **Cek endpoint** di http://localhost:8000/docs
3. **Verifikasi route** `/api/generate-image` ada di backend
4. **Restart backend server**

### Jika UPDATE Manual Gagal

1. **Cek RLS policies** dengan query 4 di VERIFY_SUPABASE_SETUP.sql
2. **Pastikan policy "Service role can do everything"** ada dan benar
3. **Periksa apakah service_role key** digunakan (bukan anon key)
4. **Coba drop dan recreate policy:**
   ```sql
   DROP POLICY IF EXISTS "Service role can do everything" ON public.profiles;
   CREATE POLICY "Service role can do everything"
       ON public.profiles FOR ALL
       USING (auth.jwt()->>'role' = 'service_role')
       WITH CHECK (auth.jwt()->>'role' = 'service_role');
   ```

## Checklist Final

Sebelum test di frontend, pastikan:

- [ ] ✅ Policy "Service role can do everything" sudah dibuat (CONFIRMED dari screenshot)
- [ ] ✅ VERIFY_SUPABASE_SETUP.sql sudah dijalankan dan semua query return hasil yang benar
- [ ] ✅ Schema cache sudah di-refresh (tunggu 2-3 menit)
- [ ] ✅ Service role key di config.env benar (bukan anon key)
- [ ] ✅ Backend server sudah di-restart setelah refresh cache
- [ ] ✅ Test manual UPDATE di SQL Editor berhasil (optional)
- [ ] ✅ Backend server berjalan tanpa error

## Expected Result

Setelah semua langkah di atas:

✅ **Generate Batch berhasil**
✅ **Tidak ada error 500 atau 404**
✅ **Gambar berhasil di-generate**
✅ **Quota berkurang sesuai (1 per generate)**

---

**Catatan Penting:**
- Schema cache refresh adalah langkah **KRITIS** setelah membuat policy
- Biasanya auto-refresh dalam 2-3 menit, tapi bisa di-force refresh manual
- Service role key **HARUS** digunakan untuk backend (bukan anon key)
- Setelah refresh cache, **HARUS** restart backend server
