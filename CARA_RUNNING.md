# Cara Menjalankan Aplikasi di Browser

Panduan lengkap untuk menjalankan Premium AI Studio di browser Anda.

## Prerequisites

Pastikan Anda sudah menginstall:
- **Python 3.8+** (untuk backend)
- **Node.js 18+** (untuk frontend)
- **npm** atau **yarn** (package manager)

## Langkah 1: Setup Backend (FastAPI)

### 1.1 Install Dependencies Backend

Buka terminal/command prompt dan jalankan:

```bash
cd backend
pip install -r requirements.txt
```

Jika menggunakan virtual environment (disarankan):

```bash
# Windows
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 1.2 Setup Environment Variable

Pastikan file `config.env` ada di **root project** (bukan di folder backend) dengan isi:

```
GEMINI_API_KEY=your_gemini_api_key_here
```

**Cara mendapatkan Gemini API Key:**
1. Kunjungi https://makersuite.google.com/app/apikey
2. Login dengan Google account
3. Buat API key baru
4. Copy dan paste ke file `config.env`

### 1.3 Jalankan Backend Server

```bash
cd backend
python main.py
```

Atau menggunakan uvicorn langsung:

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Backend akan berjalan di: **http://localhost:8000**

Anda bisa test dengan membuka: http://localhost:8000 di browser (akan muncul JSON response)

---

## Langkah 2: Setup Frontend (Next.js)

### 2.1 Install Dependencies Frontend

Buka terminal/command prompt **baru** (biarkan backend tetap running) dan jalankan:

```bash
cd frontend
npm install
```

Ini akan menginstall semua dependencies termasuk:
- React
- Next.js
- TypeScript
- Tailwind CSS
- Lucide React (icons)

### 2.2 Setup Environment Variable Frontend

File `.env.local` sudah ada di folder `frontend/` dengan isi:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Jika belum ada, buat file `.env.local` di folder `frontend/` dengan isi di atas.

### 2.3 Jalankan Frontend Server

```bash
cd frontend
npm run dev
```

Frontend akan berjalan di: **http://localhost:3000**

---

## Langkah 3: Akses di Browser

1. **Buka browser** (Chrome, Firefox, Edge, dll)
2. **Kunjungi:** http://localhost:3000
3. Aplikasi akan muncul di browser!

---

## Troubleshooting

### Backend tidak bisa start

**Error: "Module not found"**
```bash
# Pastikan semua dependencies terinstall
cd backend
pip install -r requirements.txt
```

**Error: "GEMINI_API_KEY not found"**
- Pastikan file `config.env` ada di root project
- Pastikan format: `GEMINI_API_KEY=your_key_here` (tanpa spasi di sekitar `=`)

**Error: "Port 8000 already in use"**
```bash
# Ganti port di main.py atau gunakan:
uvicorn main:app --reload --port 8001
# Lalu update NEXT_PUBLIC_API_URL di frontend/.env.local
```

### Frontend tidak bisa start

**Error: "Module not found"**
```bash
# Install ulang dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Error: "Port 3000 already in use"**
```bash
# Next.js akan otomatis menggunakan port 3001, 3002, dll
# Atau set manual:
npm run dev -- -p 3001
```

**Error: "Cannot connect to API"**
- Pastikan backend sudah running di port 8000
- Cek file `frontend/.env.local` apakah `NEXT_PUBLIC_API_URL` sudah benar
- Restart frontend setelah mengubah `.env.local`

### CORS Error

Jika muncul error CORS di browser console:
- Pastikan backend `main.py` sudah mengizinkan origin `http://localhost:3000`
- Cek di `backend/main.py` line 27-33, pastikan ada:
```python
allow_origins=["http://localhost:3000", "http://localhost:3001"],
```

---

## Struktur Terminal yang Benar

Anda perlu **2 terminal** yang berjalan bersamaan:

**Terminal 1 (Backend):**
```bash
cd backend
python main.py
# Output: Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
# Output: ready - started server on 0.0.0.0:3000
```

---

## Quick Start (Ringkasan)

```bash
# Terminal 1 - Backend
cd backend
pip install -r requirements.txt
python main.py

# Terminal 2 - Frontend (buka terminal baru)
cd frontend
npm install
npm run dev

# Browser
# Buka http://localhost:3000
```

---

## Verifikasi Setup

1. ✅ Backend running: http://localhost:8000 (lihat JSON response)
2. ✅ Frontend running: http://localhost:3000 (lihat aplikasi)
3. ✅ API connection: Upload gambar dan coba generate (tidak error)

Selamat! Aplikasi Anda sudah berjalan! 🎉



