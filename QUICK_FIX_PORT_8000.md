# Quick Fix: Port 8000 Conflict - RESOLVED ✅

## Diagnosis Error

### Error yang Terjadi:
- **Frontend**: "ENDPOINT API TIDAK DITEMUKAN"
- **Backend**: `ERROR: [Errno 10048] Port 8000 already in use`
- **Penyebab**: Process dengan PID 27732 menggunakan port 8000

### Status Sekarang:
✅ **Process PID 27732 sudah dihentikan**
✅ **Port 8000 sudah bebas**

## Langkah Selanjutnya

### 1. Start Backend Server

Buka terminal baru dan jalankan:

```bash
cd c:\project-gemini-ai\backend
python main.py
```

**Atau dengan uvicorn:**
```bash
cd c:\project-gemini-ai\backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Verifikasi Backend Running

Backend server harus start dengan sukses. Anda akan melihat:

```
INFO: Database initialized at: ...
INFO: Started server process [XXXXX]
INFO: Waiting for application startup.
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**TIDAK boleh ada error:**
- ❌ `[Errno 10048] Port already in use` ← Ini sudah diperbaiki
- ✅ Harus ada: `Uvicorn running on http://0.0.0.0:8000`

### 3. Test Backend di Browser

Buka browser dan akses:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/

Jika muncul **Swagger UI** → Backend berjalan dengan benar ✅

### 4. Test di Frontend

1. **Refresh browser** (hard refresh: `Ctrl + Shift + R`)
2. **Login ulang** jika perlu
3. **Klik "Generate Batch (3)"**
4. **Hasil yang diharapkan:**
   - ✅ Tidak ada error "ENDPOINT API TIDAK DITEMUKAN"
   - ✅ Request berhasil
   - ✅ Gambar berhasil di-generate (atau minimal error yang berbeda, bukan 404)

## Jika Masih Error

### Masih Error 404 di Frontend:

1. **Pastikan backend benar-benar running:**
   ```bash
   # Cek di terminal backend
   # Harus ada: "Uvicorn running on http://0.0.0.0:8000"
   ```

2. **Test endpoint langsung:**
   ```bash
   curl http://localhost:8000/docs
   # Atau buka di browser: http://localhost:8000/docs
   ```

3. **Cek frontend config:**
   - Pastikan `frontend/.env.local` memiliki:
     ```
     NEXT_PUBLIC_API_URL=http://localhost:8000
     ```
   - Restart frontend dev server:
     ```bash
     cd frontend
     npm run dev
     ```

### Masih Error Port Conflict:

1. **Check lagi apakah ada process lain:**
   ```powershell
   Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess
   ```

2. **Kill semua Python processes** (HATI-HATI!):
   ```powershell
   Get-Process python | Stop-Process -Force
   ```

3. **Atau gunakan port lain:**
   ```bash
   # Backend
   uvicorn main:app --host 0.0.0.0 --port 8001 --reload
   
   # Frontend .env.local
   NEXT_PUBLIC_API_URL=http://localhost:8001
   ```

## Script Auto-Fix (Untuk Future)

Jika masalah ini terjadi lagi di masa depan, jalankan:

```powershell
cd c:\project-gemini-ai
.\fix_port_8000.ps1
```

Script ini akan:
- ✅ Mencari process yang menggunakan port 8000
- ✅ Stop process tersebut
- ✅ Verify port sudah bebas
- ✅ Berikan instruksi next steps

## Prevention

Untuk menghindari masalah ini di masa depan:

1. **Always check port sebelum start:**
   ```powershell
   Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
   ```

2. **Stop backend dengan benar:**
   - Gunakan `Ctrl+C` di terminal backend
   - Jangan force quit terminal
   - Tunggu server shutdown complete

3. **Tutup semua terminal yang menjalankan backend:**
   - Pastikan hanya satu instance backend running
   - Check task manager jika perlu

4. **Use different ports untuk dev/prod:**
   - Dev: 8000
   - Prod: 8001 atau port lain

## Checklist Final

- [x] ✅ Process PID 27732 sudah dihentikan
- [x] ✅ Port 8000 sudah bebas
- [ ] ⏳ Backend server sudah di-start
- [ ] ⏳ Backend accessible di http://localhost:8000/docs
- [ ] ⏳ Frontend bisa connect ke backend
- [ ] ⏳ Generate Batch berhasil (tidak ada error 404)

---

**Next Action:** Start backend server sekarang dan test Generate Batch!
