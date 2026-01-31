# Premium AI Studio - Next.js + FastAPI

Aplikasi Premium AI Studio dengan Next.js (React) untuk frontend dan FastAPI untuk backend.

## Struktur Project 

```
project-gemini-ai/
├── backend/           # FastAPI backend
│   ├── main.py       # API endpoints
│   └── requirements.txt
├── frontend/          # Next.js frontend
│   ├── app/          # Next.js app directory
│   │   ├── page.tsx  # Main page component
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── components/   # React components
│   ├── services/     # API services
│   │   └── geminiService.ts
│   ├── types/        # TypeScript types
│   └── constants/    # Constants
└── config.env        # Environment variables
```

## Setup (Quick Start)

### Backend (FastAPI)

1. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

2. Setup environment (template):
```bash
cp backend/config.env.example config.env
```

Isi `config.env`:
```
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
GOOGLE_CLIENT_ID=your_google_client_id
GEMINI_API_KEY=your_gemini_api_key

# Bootstrap admin (optional)
BOOTSTRAP_ADMIN_ENABLED=true
BOOTSTRAP_ADMIN_EMAILS=admin1@email.com,admin2@email.com
```

3. Run server:
```bash
python main.py
# atau
uvicorn main:app --reload --port 8000
```

Backend akan berjalan di `http://localhost:8000`

### Frontend (Next.js)

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Setup environment (create file `frontend/.env.local`):
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id
```

3. Run development server:
```bash
npm run dev
```

Frontend akan berjalan di `http://localhost:3000`

## Features

- ✅ Upload hingga 4 product images (Main, Opt 2, Opt 3, Opt 4)
- ✅ Upload face reference untuk model
- ✅ Upload custom background
- ✅ Content Type selection (Model / Non Model)
- ✅ Dynamic pose options berdasarkan category dan content type
- ✅ Dynamic background options
- ✅ Generate batch 4 variasi images dengan Gemini API
- ✅ Generate 2 video prompts (Version A & B) untuk Grok
- ✅ Generate video (placeholder - coming soon)
- ✅ Download images dan videos
- ✅ Copy video prompts
- ✅ Responsive design dengan Tailwind CSS
- ✅ Modern UI dengan glass morphism effects

## API Endpoints

- `GET /api/constants` - Get all constants
- `POST /api/pose-options` - Get dynamic pose options
- `POST /api/background-options` - Get dynamic background options
- `POST /api/generate` - Generate 4 studio images (legacy)
- `POST /api/generate-photo` - Generate single photo with 2 video prompts
- `POST /api/generate-video` - Generate video from image (placeholder)

## Tech Stack

**Backend:**
- FastAPI
- Google Generative AI (Gemini)
- Python 3.8+

**Frontend:**
- Next.js 14
- React 18
- TypeScript
- Tailwind CSS
- Lucide React (Icons)

## Notes

- Video generation endpoint (`/api/generate-video`) saat ini masih placeholder. Untuk production, perlu integrasi dengan video generation API (seperti Grok, Runway, dll).
- Window.aistudio interface adalah optional untuk integrasi dengan extension/plugin tertentu.
- Pastikan `SUPABASE_URL` dan `SUPABASE_SERVICE_KEY` sudah di-set sebelum menjalankan backend.

## Deploy (Vercel + Railway)

### Backend (Railway)
1. Buat project baru di Railway → Deploy from GitHub.
2. Pilih repo ini dan set Root Directory ke `backend`.
3. Set Environment Variables:
```
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
GOOGLE_CLIENT_ID=your_google_client_id
GEMINI_API_KEY=your_gemini_api_key
BOOTSTRAP_ADMIN_ENABLED=true
BOOTSTRAP_ADMIN_EMAILS=admin1@email.com,admin2@email.com
```
4. Set Start Command:
```
uvicorn main:app --host 0.0.0.0 --port $PORT
```
5. Deploy dan catat URL backend (HTTPS).

### Frontend (Vercel)
1. Import repo di Vercel dan set Root Directory ke `frontend`.
2. Set Environment Variables:
```
NEXT_PUBLIC_API_URL=https://your-railway-backend-url
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id
```
3. Build & Deploy.



