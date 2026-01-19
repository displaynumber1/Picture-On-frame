-- ============================================
-- Script Verifikasi Setup Supabase Profiles
-- Jalankan di Supabase SQL Editor
-- ============================================

-- 1. Verifikasi tabel profiles ada
SELECT 
    table_name,
    table_schema
FROM information_schema.tables 
WHERE table_name = 'profiles' 
AND table_schema = 'public';

-- 2. Verifikasi struktur tabel profiles
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'profiles' 
AND table_schema = 'public'
ORDER BY ordinal_position;

-- 3. Verifikasi RLS sudah enabled
SELECT 
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename = 'profiles';

-- 4. Verifikasi semua policies yang ada
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies 
WHERE tablename = 'profiles'
ORDER BY policyname;

-- 5. Verifikasi trigger untuk auto-create profile
SELECT 
    trigger_name,
    event_manipulation,
    event_object_table,
    action_statement
FROM information_schema.triggers 
WHERE event_object_table = 'profiles'
OR trigger_name = 'on_auth_user_created';

-- 6. Verifikasi function handle_new_user ada
SELECT 
    routine_name,
    routine_type
FROM information_schema.routines 
WHERE routine_name = 'handle_new_user'
AND routine_schema = 'public';

-- 7. Test: Cek apakah ada data di profiles
SELECT 
    COUNT(*) as total_profiles,
    COUNT(DISTINCT user_id) as unique_users,
    SUM(free_image_quota) as total_quota,
    SUM(coins_balance) as total_coins
FROM public.profiles;

-- 8. Test: Lihat sample data (jika ada)
SELECT 
    id,
    user_id,
    free_image_quota,
    coins_balance,
    created_at,
    updated_at
FROM public.profiles
LIMIT 5;

-- ============================================
-- Test Manual UPDATE (jika ada data)
-- ============================================
-- UNCOMMENT baris di bawah jika ingin test UPDATE manual
-- Ganti USER_ID_HERE dengan actual user_id dari query di atas

-- BEGIN;
-- UPDATE public.profiles 
-- SET free_image_quota = free_image_quota 
-- WHERE user_id = 'USER_ID_HERE';
-- ROLLBACK;  -- Rollback untuk test, jangan commit!

-- ============================================
-- Verifikasi Schema Cache Status
-- ============================================
-- Catatan: Schema cache tidak bisa di-refresh langsung via SQL
-- Tapi bisa force reload dengan NOTIFY (jika memiliki permission)

-- NOTIFY pgrst, 'reload schema';
-- (Ini mungkin tidak bekerja tanpa superuser permission)

-- ============================================
-- Checklist Hasil
-- ============================================
-- ✅ Query 1: Tabel profiles harus ada
-- ✅ Query 2: Harus ada 7 kolom (id, user_id, free_image_quota, coins_balance, created_at, updated_at, dll)
-- ✅ Query 3: RLS enabled = true
-- ✅ Query 4: Harus ada minimal 3 policies:
--    - "Users can view own profile" (SELECT)
--    - "Users can update own profile" (UPDATE)  
--    - "Service role can do everything" (ALL)
-- ✅ Query 5: Trigger on_auth_user_created harus ada
-- ✅ Query 6: Function handle_new_user harus ada
-- ✅ Query 7 & 8: Cek data (bisa kosong jika belum ada user)
