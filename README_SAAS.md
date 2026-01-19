# SaaS AI Image & Video Generator

Sistem lengkap untuk generate gambar dan video menggunakan AI dengan integrasi Supabase Auth, Fal.ai, dan Midtrans payment.

## Fitur

- ✅ **Google OAuth** via Supabase
- ✅ **Generate 2 Images** per klik menggunakan Fal.ai flux/schnell
- ✅ **Animate to Video** menggunakan Fal.ai kling-v2 (5 coins per video)
- ✅ **Payment System** dengan Midtrans Snap
- ✅ **Quota Management** (free_image_quota dan coins_balance)
- ✅ **Dark Mode UI** dengan tema purple-600
- ✅ **Loading States** yang cantik

## Struktur Project

```
project-gemini-ai/
├── backend/
│   ├── main.py                 # FastAPI main app dengan routes SaaS
│   ├── fal_service.py          # Service untuk Fal.ai integration
│   ├── supabase_service.py     # Service untuk Supabase database
│   ├── requirements.txt        # Python dependencies
│   └── ...
├── frontend/
│   ├── app/
│   │   ├── page.tsx            # Landing page dengan login
│   │   └── generator/
│   │       └── page.tsx        # Main generator page
│   ├── services/
│   │   ├── supabaseService.ts  # Supabase client
│   │   ├── generatorService.ts # API calls untuk generate
│   │   └── midtransService.ts  # Midtrans payment integration
│   └── ...
├── setup.sql                   # Database setup (Supabase)
└── ENV_SETUP_SAAS.md          # Environment variables documentation
```

## Setup

### 1. Database Setup (Supabase)

1. Buka Supabase Dashboard > SQL Editor
2. Jalankan script dari `setup.sql`
3. Pastikan trigger `on_auth_user_created` berjalan dengan baik

### 2. Environment Variables

#### Backend (`config.env` atau `.env`)

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
MIDTRANS_IS_PRODUCTION=false
```

#### Frontend (`.env.local`)

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_MIDTRANS_CLIENT_KEY=your-midtrans-client-key
```

### 3. Install Dependencies

#### Backend

```bash
cd backend
pip install -r requirements.txt
```

#### Frontend

```bash
cd frontend
npm install
```

### 4. Run Application

#### Backend

```bash
cd backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

#### Frontend

```bash
cd frontend
npm run dev
```

Akses aplikasi di `http://localhost:3000`

## API Routes

### `/api/generate-image` (POST)
Generate 2 images menggunakan Fal.ai flux/schnell
- **Auth**: Required (Bearer token)
- **Body**: `{ "prompt": "your prompt" }`
- **Response**: `{ "images": ["url1", "url2"], "remaining_quota": 6 }`
- **Logic**: Mengurangi `free_image_quota` sebanyak 1

### `/api/generate-video-saas` (POST)
Generate video menggunakan Fal.ai kling-v2
- **Auth**: Required (Bearer token)
- **Body**: `{ "prompt": "your prompt", "image_url": "optional" }`
- **Response**: `{ "video_url": "url", "remaining_coins": 95 }`
- **Logic**: Mengurangi `coins_balance` sebanyak 5

### `/api/user/profile` (GET)
Get user profile (quota dan coins)
- **Auth**: Required (Bearer token)
- **Response**: `{ "free_image_quota": 7, "coins_balance": 0 }`

### `/api/midtrans/create-transaction` (POST)
Create Midtrans Snap transaction
- **Auth**: Required (Bearer token)
- **Body**: `{ "package_id": "package-1", "order_id": "coins-userid-timestamp", "gross_amount": 50000, "user_id": "uuid" }`
- **Response**: `{ "snap_token": "token", "order_id": "..." }`

### `/api/webhook/midtrans` (POST)
Handle Midtrans payment webhook
- **Body**: Midtrans webhook payload
- **Logic**: Menambah `coins_balance` berdasarkan `gross_amount` (1 coin = 1000 IDR)

## Database Schema

### Table: `profiles`

| Column | Type | Default | Description |
|--------|------|---------|-------------|
| id | UUID | gen_random_uuid() | Primary key |
| user_id | UUID | - | Foreign key ke auth.users |
| free_image_quota | INTEGER | 5 | Quota gambar gratis |
| coins_balance | INTEGER | 0 | Saldo koin |
| created_at | TIMESTAMP | NOW() | Waktu dibuat |
| updated_at | TIMESTAMP | NOW() | Waktu diupdate |

**Trigger**: `on_auth_user_created`
- Otomatis membuat profile baru saat user mendaftar
- Set `free_image_quota = 7` dan `coins_balance = 0`

## Frontend Features

### Landing Page (`/`)
- Login dengan Google OAuth
- Auto-redirect ke `/generator` jika sudah login

### Generator Page (`/generator`)
- **Navbar**: Menampilkan coins balance dan free quota
- **Prompt Input**: Textarea untuk input prompt
- **Generate Button**: Generate 2 images (mengurangi quota 1)
- **Image Grid**: 2 kolom untuk menampilkan hasil
- **Animate to Video**: Button di bawah setiap gambar (5 coins)
- **Payment Modal**: Muncul otomatis jika quota/coins habis
- **Loading States**: Spinner dan skeleton yang cantik

## Payment Packages

| Package | Coins | Price (IDR) |
|---------|-------|-------------|
| Starter Pack | 50 | 50,000 |
| Popular Pack | 150 | 130,000 |
| Pro Pack | 300 | 250,000 |
| Mega Pack | 600 | 450,000 |

## Testing

1. **Test Generate Image**:
   - Login dengan Google
   - Input prompt
   - Klik "Generate (2 Images)"
   - Cek quota berkurang 1

2. **Test Generate Video**:
   - Pastikan memiliki minimal 5 coins
   - Klik "✨ Animate to Video (5 Coins)" di bawah gambar
   - Cek coins berkurang 5

3. **Test Payment**:
   - Habiskan coins
   - Klik "Top up" atau generate video tanpa coins
   - Pilih package
   - Complete payment di Midtrans
   - Cek coins bertambah

## Troubleshooting

### Error: "FAL_KEY is not configured"
- Pastikan `FAL_KEY` ada di `config.env` backend

### Error: "Supabase client not initialized"
- Pastikan `SUPABASE_URL` dan `SUPABASE_SERVICE_KEY` ada di `config.env`

### Error: "Profile not found"
- Pastikan trigger `on_auth_user_created` sudah dijalankan di Supabase
- Atau buat profile manual untuk user yang sudah ada

### Images tidak muncul
- Cek Fal.ai API key valid
- Cek quota masih tersedia
- Cek console untuk error details

## Production Deployment

1. Set `MIDTRANS_IS_PRODUCTION=true` di backend
2. Update `NEXT_PUBLIC_API_URL` di frontend ke production URL
3. Konfigurasi Midtrans webhook URL di dashboard
4. Enable CORS di backend untuk production domain
5. Setup Supabase RLS policies untuk production

## License

MIT

