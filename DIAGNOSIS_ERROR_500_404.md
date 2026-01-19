# Diagnosis Error 500 & 404 - Generate Batch

## Error yang Terjadi

### 1. Error 500 (PGRST205)
```
POST /api/generate-image HTTP/1.1" 500 Internal Server Error
'code': 'PGRST205'
Could not find the table 'public.profiles' in the schema cache
```

### 2. Error 404
```
POST /api/generate-image HTTP/1.1" 404 Not Found
ENDPOINT API TIDAK DITEMUKAN. PASTIKAN BACKEND SERVER BERJALAN DAN MENGGUNAKAN VERSI TERBARU.
```

## Analisis Log Terminal

### Yang Berhasil ✅
- GET request ke Supabase profiles: `HTTP/2 200 OK`
- Query: `/rest/v1/profiles?select=%2A&user_id=eq.13ab4cf1-8587-4685-874b-c2d37beeab38`
- **Kesimpulan**: Tabel `profiles` sudah ada dan bisa dibaca!

### Yang Error ❌
- Error 500 dengan PGRST205 saat operasi UPDATE/INSERT
- Error 404 setelah error 500 (server mungkin restart atau crash)

## Penyebab Masalah

### 1. Schema Cache Issue (PGRST205)
Meskipun tabel sudah ada dan bisa dibaca, Supabase PostgREST schema cache belum di-refresh untuk operasi UPDATE/INSERT. Ini adalah masalah **cache**, bukan tabel yang tidak ada.

**Gejala:**
- SELECT (GET) berhasil ✅
- UPDATE/INSERT gagal ❌ dengan PGRST205

### 2. RLS (Row Level Security) Policy Issue
Kemungkinan service_role key tidak memiliki permission yang benar, atau RLS policies tidak mengizinkan UPDATE operation.

### 3. Server Restart/Crash
Error 404 setelah error 500 menunjukkan server mungkin crash atau restart, menyebabkan endpoint tidak tersedia sementara.

## Solusi

### Solusi 1: Refresh Schema Cache (PRIORITAS TINGGI)

1. **Buka Supabase Dashboard:**
   - https://supabase.com/dashboard
   - Pilih project Anda

2. **Refresh Schema Cache:**
   - Buka **Database** > **Replication**
   - Cari opsi **"Reload Schema"** atau **"Refresh Schema Cache"**
   - Klik untuk refresh
   - Atau tunggu 2-3 menit untuk auto-refresh

3. **Alternatif - Via SQL:**
   ```sql
   -- Force schema cache refresh
   NOTIFY pgrst, 'reload schema';
   ```

### Solusi 2: Verifikasi RLS Policies

Pastikan policy untuk service_role ada dan benar:

```sql
-- Periksa policies yang ada
SELECT * FROM pg_policies WHERE tablename = 'profiles';

-- Jika policy untuk service_role tidak ada, buat:
DROP POLICY IF EXISTS "Service role can do everything" ON public.profiles;
CREATE POLICY "Service role can do everything"
    ON public.profiles FOR ALL
    USING (auth.jwt()->>'role' = 'service_role')
    WITH CHECK (auth.jwt()->>'role' = 'service_role');
```

### Solusi 3: Verifikasi Service Key

1. **Buka Supabase Dashboard > Settings > API**
2. **Pastikan menggunakan SERVICE_ROLE key** (bukan anon key):
   - Service role key: **panjang, merah, secret**
   - Anon key: **biasanya lebih pendek, aman untuk frontend**

3. **Update config.env:**
   ```env
   SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  # SERVICE_ROLE key yang benar
   ```

### Solusi 4: Test Tabel Langsung

Test apakah tabel benar-benar bisa diakses:

```sql
-- Di Supabase SQL Editor
SELECT * FROM public.profiles LIMIT 5;

-- Test UPDATE (dengan service role)
UPDATE public.profiles 
SET free_image_quota = 5 
WHERE user_id = '13ab4cf1-8587-4685-874b-c2d37beeab38';
```

### Solusi 5: Restart Backend Server

Setelah melakukan refresh schema cache:

```bash
# Stop backend server (Ctrl+C)
# Start ulang
cd backend
python main.py
```

## Checklist Troubleshooting

- [ ] Schema cache sudah di-refresh di Supabase Dashboard
- [ ] RLS policy untuk service_role sudah ada dan benar
- [ ] Service role key di `config.env` adalah key yang benar (bukan anon key)
- [ ] Tabel `profiles` bisa dibaca (SELECT) ✅ - Sudah confirmed dari log
- [ ] Tabel `profiles` bisa di-update (test manual di SQL Editor)
- [ ] Backend server sudah di-restart setelah refresh cache
- [ ] Backend server berjalan tanpa error (cek log terminal)

## Verifikasi Setelah Perbaikan

1. **Test di Backend:**
   ```bash
   # Test endpoint
   curl -X POST http://localhost:8000/api/generate-image \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{"prompt": "test"}'
   ```

2. **Cek Log Backend:**
   - Tidak ada error PGRST205
   - Request berhasil (200 OK)
   - Tidak ada error 404

3. **Test di Frontend:**
   - Klik "Generate Batch (3)"
   - Tidak ada error 500 atau 404
   - Request berhasil

## Error Handling yang Sudah Diperbaiki

Kode sudah diperbaiki untuk:
1. Memberikan pesan error yang lebih jelas
2. Menangani error PGRST205 dengan pesan spesifik
3. Menangani error schema cache dengan instruksi refresh

## Catatan Penting

- **PGRST205** adalah error schema cache, bukan error tabel tidak ada
- Jika SELECT berhasil tapi UPDATE gagal, ini biasanya masalah cache atau RLS
- Service role key HARUS digunakan untuk operasi backend (bukan anon key)
- Schema cache biasanya refresh otomatis setiap 1-2 menit, tapi bisa di-force refresh

## Verifikasi Setup (SETELAH Policy Dibuat)

Setelah policy "Service role can do everything" berhasil dibuat (seperti di screenshot), lakukan verifikasi:

### Step 1: Jalankan Script Verifikasi SQL

Jalankan file `VERIFY_SUPABASE_SETUP.sql` di Supabase SQL Editor untuk verifikasi lengkap:

1. **Buka Supabase SQL Editor**
2. **Copy seluruh isi dari `VERIFY_SUPABASE_SETUP.sql`**
3. **Paste dan Run**
4. **Periksa hasil setiap query:**
   - Query 1: Tabel `profiles` harus ada ✅
   - Query 2: Struktur tabel harus memiliki 7 kolom ✅
   - Query 3: RLS harus enabled (true) ✅
   - Query 4: Harus ada minimal 3 policies termasuk "Service role can do everything" ✅
   - Query 5: Trigger `on_auth_user_created` harus ada ✅
   - Query 6: Function `handle_new_user` harus ada ✅

### Step 2: Test Service Role Access dengan Python

Jalankan script test untuk verifikasi service_role key bisa mengakses profiles:

```bash
cd backend
python ../TEST_SERVICE_ROLE_ACCESS.py
```

Script ini akan test:
- ✅ SELECT (Read) - harus berhasil
- ✅ UPDATE (Write) - harus berhasil jika ada data
- ❌ Jika gagal, akan menunjukkan error detail

### Step 3: Refresh Schema Cache (PENTING!)

Meskipun policy sudah dibuat, **schema cache mungkin belum update**:

1. **Buka Supabase Dashboard > Database > Replication**
2. **Cari opsi "Reload Schema" atau "Refresh Schema Cache"**
3. **Klik untuk refresh**
4. **Tunggu 1-2 menit** untuk cache refresh

**Atau** tunggu 2-3 menit untuk auto-refresh.

### Step 4: Restart Backend Server

Setelah semua verifikasi dan refresh cache:

```bash
# Stop backend (Ctrl+C)
# Start ulang
cd backend
python main.py
```

### Step 5: Test di Frontend

1. Refresh browser (hard refresh: Ctrl+Shift+R)
2. Login ulang jika perlu
3. Klik "Generate Batch (3)"
4. Tidak boleh ada error 500 atau 404

## Jika Masih Error

1. **Jalankan `VERIFY_SUPABASE_SETUP.sql`** dan periksa semua query hasilnya
2. **Jalankan `TEST_SERVICE_ROLE_ACCESS.py`** untuk verifikasi service_role access
3. **Cek log backend** untuk detail error lengkap
4. **Cek browser console** (F12) untuk error network
5. **Test endpoint langsung** dengan curl atau Postman
6. **Verifikasi semua checklist** di atas
7. **Cek Supabase logs** di Dashboard > Logs untuk error database
8. **Pastikan service_role key benar** (bukan anon key) di config.env
