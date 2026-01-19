# Environment Variables Setup untuk SaaS AI Image & Video Generator

## Backend (.env atau config.env)

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key

# Fal.ai
FAL_KEY=your-fal-ai-api-key

# Midtrans
MIDTRANS_SERVER_KEY=your-midtrans-server-key
MIDTRANS_CLIENT_KEY=your-midtrans-client-key
MIDTRANS_IS_PRODUCTION=false  # Set to 'true' for production

# API URL (optional, defaults to http://127.0.0.1:8000)
API_URL=http://127.0.0.1:8000
```

## Frontend (.env.local)

```env
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# Backend API
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000

# Midtrans
NEXT_PUBLIC_MIDTRANS_CLIENT_KEY=your-midtrans-client-key
```

## Setup Instructions

1. **Supabase Setup:**
   - Buat project di [Supabase](https://supabase.com)
   - Enable Google OAuth provider di Authentication > Providers
   - Jalankan `setup.sql` di SQL Editor untuk membuat tabel dan trigger
   - Copy URL dan keys dari Project Settings > API

2. **Fal.ai Setup:**
   - Daftar di [Fal.ai](https://fal.ai)
   - Dapatkan API key dari dashboard
   - Pastikan memiliki kredit yang cukup

3. **Midtrans Setup:**
   - Daftar di [Midtrans](https://midtrans.com)
   - Dapatkan Server Key dan Client Key
   - Untuk development, gunakan Sandbox keys
   - Konfigurasi webhook URL di dashboard: `https://your-domain.com/api/webhook/midtrans`

4. **Database Setup:**
   - Buka Supabase SQL Editor
   - Jalankan script dari `setup.sql`
   - Pastikan trigger berjalan dengan baik

## Testing

1. Start backend: `cd backend && python -m uvicorn main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Akses `http://localhost:3000/generator`
4. Login dengan Google OAuth
5. Test generate image dan video

