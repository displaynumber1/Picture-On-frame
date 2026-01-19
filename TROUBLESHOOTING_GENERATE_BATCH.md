# Troubleshooting: Error "FAILED TO FETCH" pada Generate Batch

## Masalah
Ketika klik tombol "Generate Batch (3)", muncul error **"FAILED TO FETCH"**.

## Penyebab
Backend server tidak berjalan di port 8000. Frontend tidak dapat terhubung ke backend API.

## Solusi

### 1. Jalankan Backend Server

Pastikan backend server berjalan sebelum menggunakan frontend:

```bash
# Masuk ke direktori backend
cd backend

# Aktifkan virtual environment (jika menggunakan venv)
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Jalankan server
python main.py
```

Atau menggunakan uvicorn langsung:

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Verifikasi Backend Berjalan

Buka browser dan akses:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/

Jika backend berjalan dengan benar, Anda akan melihat dokumentasi API Swagger di `/docs`.

### 3. Periksa Konfigurasi Environment

Pastikan file `frontend/.env.local` memiliki konfigurasi yang benar:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Jika backend berjalan di port lain, sesuaikan URL tersebut.

### 4. Periksa CORS Configuration

Backend sudah dikonfigurasi untuk mengizinkan CORS dari:
- `http://localhost:3000`
- `http://localhost:3001`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:3001`

Pastikan frontend berjalan di salah satu port tersebut.

### 5. Restart Frontend Dev Server

Setelah backend berjalan, restart frontend:

```bash
cd frontend
npm run dev
```

## Error Handling yang Sudah Diperbaiki

Error handling di frontend sudah diperbaiki untuk memberikan pesan error yang lebih jelas:

1. **Network Error**: "Tidak dapat terhubung ke server backend. Pastikan backend server berjalan di http://localhost:8000."
2. **401 Unauthorized**: "Sesi Anda telah berakhir. Silakan login ulang."
3. **403 Forbidden**: "Quota Anda telah habis. Silakan top up untuk melanjutkan."
4. **404 Not Found**: "Endpoint API tidak ditemukan. Pastikan backend server berjalan dan menggunakan versi terbaru."
5. **500 Server Error**: "Server error. Silakan coba lagi nanti."

## Checklist Troubleshooting

- [ ] Backend server berjalan di port 8000
- [ ] Frontend `.env.local` berisi `NEXT_PUBLIC_API_URL=http://localhost:8000`
- [ ] Frontend dev server berjalan di port 3000 atau 3001
- [ ] Tidak ada firewall yang memblokir koneksi ke port 8000
- [ ] User sudah login (token authentication valid)
- [ ] User memiliki quota yang cukup (untuk generate image)

## Test Koneksi Backend

Untuk test apakah backend berjalan, buka terminal dan jalankan:

```bash
# Windows PowerShell
curl http://localhost:8000/docs

# Atau menggunakan browser
# Buka: http://localhost:8000/docs
```

Jika mendapatkan response HTML (Swagger UI), berarti backend berjalan dengan benar.

## Jika Masalah Masih Berlanjut

1. Periksa log backend di terminal untuk melihat error detail
2. Periksa browser console (F12) untuk melihat error network
3. Pastikan tidak ada aplikasi lain yang menggunakan port 8000
4. Pastikan semua dependencies backend sudah terinstall:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
