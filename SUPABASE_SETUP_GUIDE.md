# Supabase Setup Guide - Fix Error 500: Table 'profiles' Not Found

## Error yang Terjadi
```
Error 500: Could not find the table 'public.profiles' in the schema cache (PGRST205)
```

## Penyebab
Tabel `profiles` belum dibuat di database Supabase, atau schema cache Supabase belum di-refresh.

## Solusi

### Langkah 1: Akses Supabase Dashboard

1. Buka https://supabase.com/dashboard
2. Login ke akun Supabase Anda
3. Pilih project yang sesuai (dari URL di `config.env`: `https://your-project.supabase.co`)

### Langkah 2: Jalankan SQL Setup

1. Di Supabase Dashboard, buka **SQL Editor** (di sidebar kiri)
2. Klik **New Query**
3. Copy seluruh isi dari file `setup.sql` di root project
4. Paste ke SQL Editor
5. Klik **Run** atau tekan `Ctrl+Enter` (Windows) / `Cmd+Enter` (Mac)

### Langkah 3: Verifikasi Tabel Dibuat

1. Di Supabase Dashboard, buka **Table Editor** (di sidebar kiri)
2. Anda seharusnya melihat tabel `profiles` di daftar tabel
3. Klik tabel `profiles` untuk melihat strukturnya:
   - `id` (UUID, Primary Key)
   - `user_id` (UUID, Foreign Key ke auth.users)
   - `free_image_quota` (INTEGER, default: 5)
   - `coins_balance` (INTEGER, default: 0)
   - `created_at` (TIMESTAMP)
   - `updated_at` (TIMESTAMP)

### Langkah 4: Refresh Schema Cache (Jika Perlu)

Jika error masih muncul setelah membuat tabel:

1. Di Supabase Dashboard, buka **Database** > **Replication**
2. Cari opsi **Refresh Schema Cache** atau **Reload Schema**
3. Klik untuk refresh cache
4. Atau tunggu 1-2 menit untuk cache refresh otomatis

### Langkah 5: Verifikasi RLS (Row Level Security)

1. Di **Table Editor**, klik tabel `profiles`
2. Pastikan **RLS Enabled** (Row Level Security) sudah aktif
3. Di tab **Policies**, pastikan policies berikut ada:
   - "Users can view own profile" (SELECT)
   - "Users can update own profile" (UPDATE)
   - "Service role can do everything" (ALL)

### Langkah 6: Test Koneksi

Setelah setup selesai, test dengan menjalankan backend:

```bash
cd backend
python main.py
```

Kemudian coba generate batch lagi di frontend.

## Jika Masih Error

### Checklist Troubleshooting

- [ ] File `setup.sql` sudah dijalankan di Supabase SQL Editor
- [ ] Tabel `profiles` sudah muncul di Table Editor
- [ ] Schema cache sudah di-refresh (tunggu 1-2 menit atau refresh manual)
- [ ] RLS sudah enabled untuk tabel `profiles`
- [ ] Policies sudah dibuat untuk service role
- [ ] `SUPABASE_URL` dan `SUPABASE_SERVICE_KEY` di `config.env` sudah benar
- [ ] Service key yang digunakan adalah **service_role key** (bukan anon key)

### Verifikasi Service Key

Pastikan Anda menggunakan **service_role key** (bukan anon/public key) di `config.env`:

1. Di Supabase Dashboard, buka **Settings** > **API**
2. Di bagian **Project API keys**, copy **service_role** key (secret, merah)
3. Pastikan ini yang digunakan di `config.env` sebagai `SUPABASE_SERVICE_KEY`

**⚠️ PENTING:** Jangan pernah commit service_role key ke Git! Key ini harus tetap secret.

### Manual Create Profile (Alternatif)

Jika trigger tidak bekerja, Anda bisa manually create profile untuk user yang sudah ada:

```sql
-- Ganti USER_ID_HERE dengan actual user ID dari auth.users
INSERT INTO public.profiles (user_id, free_image_quota, coins_balance)
VALUES ('USER_ID_HERE', 7, 0)
ON CONFLICT (user_id) DO NOTHING;
```

Untuk mendapatkan user_id:
1. Buka **Authentication** > **Users** di Supabase Dashboard
2. Copy UUID dari user yang ingin dibuat profilnya

## SQL Script (setup.sql)

Jika file `setup.sql` tidak ada atau hilang, gunakan SQL berikut:

```sql
-- 1. Buat tabel profiles
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    free_image_quota INTEGER NOT NULL DEFAULT 5,
    coins_balance INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- 2. Create index
CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON public.profiles(user_id);

-- 3. Create trigger function untuk update updated_at
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 4. Create trigger
DROP TRIGGER IF EXISTS update_profiles_updated_at ON public.profiles;
CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- 5. Create function untuk auto-create profile saat signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (user_id, free_image_quota, coins_balance)
    VALUES (NEW.id, 7, 0);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 6. Create trigger untuk auto-create profile
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- 7. Enable RLS
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- 8. Create policies
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
CREATE POLICY "Users can view own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Service role can do everything" ON public.profiles;
CREATE POLICY "Service role can do everything"
    ON public.profiles FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');
```

## Setelah Setup Berhasil

Setelah tabel dibuat dan cache di-refresh:

1. Restart backend server
2. Test dengan membuat generate batch
3. Jika masih error, periksa log backend untuk detail error
4. Pastikan user sudah login dan memiliki profile

## Catatan

- Tabel `profiles` harus berada di schema `public` (bukan schema lain)
- Service role key diperlukan untuk backend mengakses semua data
- RLS policies memastikan user hanya bisa akses data mereka sendiri
- Trigger akan otomatis membuat profile baru saat user mendaftar
