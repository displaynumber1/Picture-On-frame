# Quick Start Guide - SaaS AI Image & Video Generator

## Error: "supabaseUrl is required"

Error ini muncul karena environment variables belum dikonfigurasi. Ikuti langkah berikut:

## 1. Setup Supabase

1. Buat project di [Supabase](https://supabase.com)
2. Buka **Project Settings > API**
3. Copy **Project URL** dan **anon/public key**

## 2. Setup Environment Variables

### Frontend (`.env.local`)

Buat file `.env.local` di folder `frontend/` dengan isi:

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key-here
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_MIDTRANS_CLIENT_KEY=your-midtrans-client-key
```

**Cara:**
1. Copy file `.env.local.example` ke `.env.local`
2. Isi dengan nilai yang sebenarnya dari Supabase dashboard

### Backend (`config.env`)

Tambahkan ke file `config.env` di root project:

```env
# Supabase
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key

# fal
FAL_KEY=your-fal-ai-api-key

# Midtrans
MIDTRANS_SERVER_KEY=your-midtrans-server-key
MIDTRANS_CLIENT_KEY=your-midtrans-client-key
MIDTRANS_IS_PRODUCTION=false
```

## 3. Setup Database

1. Buka Supabase Dashboard > **SQL Editor**
2. Jalankan script dari file `setup.sql`
3. Pastikan trigger `on_auth_user_created` berhasil dibuat

## 4. Enable Google OAuth

1. Buka Supabase Dashboard > **Authentication > Providers**
2. Enable **Google** provider
3. Masukkan Google OAuth credentials (Client ID & Secret)

## 5. Restart Development Server

Setelah mengisi environment variables:

```bash
# Stop server (Ctrl+C)
# Restart frontend
cd frontend
npm run dev

# Restart backend (di terminal lain)
cd backend
python -m uvicorn main:app --reload
```

## 6. Test

1. Buka `http://localhost:3000`
2. Klik "Get Started" untuk login dengan Google
3. Setelah login, akan redirect ke `/generator`

## Troubleshooting

### Masih error "supabaseUrl is required"?

1. Pastikan file `.env.local` ada di folder `frontend/`
2. Pastikan nama variable benar: `NEXT_PUBLIC_SUPABASE_URL` (dengan prefix `NEXT_PUBLIC_`)
3. Restart Next.js dev server (Next.js hanya load env vars saat startup)
4. Cek console browser untuk melihat nilai env vars yang ter-load

### Cara cek env vars ter-load:

Tambahkan di `frontend/app/page.tsx` (temporary untuk debug):

```typescript
console.log('Supabase URL:', process.env.NEXT_PUBLIC_SUPABASE_URL);
```

**Jangan commit ini ke production!**

## Next Steps

Setelah setup berhasil:
1. Test generate image
2. Test generate video (butuh coins)
3. Test payment flow dengan Midtrans

Lihat `README_SAAS.md` untuk dokumentasi lengkap.

