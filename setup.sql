-- Setup SQL untuk SaaS AI Image & Video Generator
-- Database: Supabase (PostgreSQL)

-- 1. Buat tabel profiles jika belum ada
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    role_user TEXT NOT NULL DEFAULT 'user',
    free_image_quota INTEGER NOT NULL DEFAULT 5,
    coins_balance INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id)
);

-- 1b. Pastikan kolom role_user tersedia untuk admin di Supabase
ALTER TABLE profiles ADD COLUMN IF NOT EXISTS role_user TEXT NOT NULL DEFAULT 'user';

-- 2. Buat index untuk performa query
CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles(user_id);

-- 3. Buat function untuk update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 4. Buat trigger untuk auto-update updated_at
DROP TRIGGER IF EXISTS update_profiles_updated_at ON profiles;
CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 5. Buat function untuk auto-create profile saat user baru mendaftar
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (user_id, free_image_quota, coins_balance)
    VALUES (NEW.id, 7, 0);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 6. Buat trigger untuk auto-create profile saat user baru dibuat di auth.users
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- 7. Enable Row Level Security (RLS) untuk profiles
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

-- 8. Buat policy untuk user hanya bisa membaca dan update profile mereka sendiri
DROP POLICY IF EXISTS "Users can view own profile" ON profiles;
CREATE POLICY "Users can view own profile"
    ON profiles FOR SELECT
    USING (auth.uid() = user_id);

-- Admin dapat melihat semua profile
DROP POLICY IF EXISTS "Admin can view all profiles" ON profiles;
CREATE POLICY "Admin can view all profiles"
    ON profiles FOR SELECT
    USING (
      EXISTS (
        SELECT 1 FROM public.profiles p
        WHERE p.user_id = auth.uid() AND p.role_user = 'admin'
      )
    );

DROP POLICY IF EXISTS "Users can update own profile" ON profiles;
CREATE POLICY "Users can update own profile"
    ON profiles FOR UPDATE
    USING (auth.uid() = user_id);

-- 9. Buat policy untuk service role (backend) bisa melakukan semua operasi
DROP POLICY IF EXISTS "Service role can do everything" ON profiles;
CREATE POLICY "Service role can do everything"
    ON profiles FOR ALL
    USING (auth.jwt()->>'role' = 'service_role');

-- Catatan:
-- - free_image_quota default di tabel adalah 5, tapi trigger set ke 7 saat signup (sesuai requirement)
-- - coins_balance default adalah 0
-- - Trigger akan otomatis membuat profile baru saat user mendaftar via Google Auth
-- - RLS memastikan user hanya bisa akses profile mereka sendiri

