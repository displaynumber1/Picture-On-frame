# Setup Sistem Login Google OAuth dengan Database Whitelist

## 1. Database Setup

Jalankan script untuk membuat database dan tabel:

```bash
cd backend
python setup_db.py
```

Script ini akan:
- Membuat database SQLite `premium_studio.db`
- Membuat tabel `authorized_users` dengan kolom:
  - `id` (INTEGER PRIMARY KEY)
  - `email` (TEXT UNIQUE)
  - `role` (TEXT, default 'user')
  - `created_at` (TEXT)
- Menambahkan email `dapid.saepurohman@gmail.com` sebagai admin pertama

## 2. Backend Configuration

### Environment Variables

Tambahkan ke `config.env` di root project:

```
GEMINI_API_KEY=your_gemini_api_key
GOOGLE_CLIENT_ID=your_google_client_id
```

### Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Run Backend

```bash
python main.py
# atau
uvicorn main:app --reload --port 8000
```

## 3. Frontend Configuration

### Environment Variables

Tambahkan ke `frontend/.env.local`:

```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GOOGLE_CLIENT_ID=your_google_client_id
```

### Install Dependencies (jika belum)

```bash
cd frontend
npm install
```

### Run Frontend

```bash
npm run dev
```

## 4. Google OAuth Setup

1. Buka [Google Cloud Console](https://console.cloud.google.com/)
2. Buat project baru atau pilih project yang ada
3. Enable **Google+ API** dan **Google Identity Services**
4. Buat **OAuth 2.0 Client ID**:
   - Application type: **Web application**
   - Authorized JavaScript origins: `http://localhost:3000`
   - Authorized redirect URIs: `http://localhost:3000`
5. Copy **Client ID** ke environment variables

## 5. API Endpoints

### Verifikasi Email
```
POST /api/verify-email
Body: { "email": "user@example.com" }
Response: { "authorized": true, "email": "...", "role": "user" }
```

### Verifikasi Google Token
```
POST /api/verify-google-token
Body: { "token": "google_id_token" }
Response: { "authorized": true, "email": "...", "role": "user", "name": "...", "picture": "..." }
```

### Admin: Tambah User (Admin Only)
```
POST /admin/add-user
Headers: { "X-User-Email": "admin@example.com" }
Body: { "email": "newuser@example.com", "role": "user" }
Response: { "success": true, "message": "..." }
```

## 6. Cara Menambahkan User Baru (Admin)

### Via API:

```bash
curl -X POST http://localhost:8000/admin/add-user \
  -H "Content-Type: application/json" \
  -H "X-User-Email: dapid.saepurohman@gmail.com" \
  -d '{"email": "newuser@example.com", "role": "user"}'
```

### Via Database Langsung:

```bash
cd backend
python
```

```python
import sqlite3
from datetime import datetime

conn = sqlite3.connect('premium_studio.db')
cursor = conn.cursor()

cursor.execute('''
    INSERT INTO authorized_users (email, role, created_at)
    VALUES (?, ?, ?)
''', ('newuser@example.com', 'user', datetime.now().isoformat()))

conn.commit()
conn.close()
```

## 7. Flow Login

1. User klik "Continue with Google"
2. Google OAuth popup muncul
3. User login dengan Google account
4. Frontend mendapatkan access token dari Google
5. Frontend mendapatkan user info dari Google API
6. Frontend mengirim email ke backend `/api/verify-email`
7. Backend mengecek email di database `authorized_users`
8. Jika email terdaftar:
   - Return success dengan role
   - Frontend simpan ke localStorage
   - User diarahkan ke menu utama
9. Jika email tidak terdaftar:
   - Return 403 Forbidden
   - Tampilkan error: "Akses Ditolak: Email Anda belum terdaftar dalam sistem premium kami."

## 8. Troubleshooting

### Error: "Google Sign-In belum dikonfigurasi"
- Pastikan `NEXT_PUBLIC_GOOGLE_CLIENT_ID` sudah di-set di `.env.local`
- Restart development server setelah mengubah `.env.local`

### Error: "Akses Ditolak: Email Anda belum terdaftar"
- Email belum ada di database `authorized_users`
- Admin perlu menambahkan email via `/admin/add-user` endpoint

### Error: "Token tidak valid"
- Pastikan `GOOGLE_CLIENT_ID` di backend sama dengan di frontend
- Pastikan Google OAuth credentials sudah benar

### Database tidak ditemukan
- Jalankan `python setup_db.py` di folder `backend`
- Pastikan script berhasil membuat `premium_studio.db`

