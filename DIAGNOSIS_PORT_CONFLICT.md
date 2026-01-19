# Diagnosis Error: Port 8000 Already in Use

## Error yang Terjadi

### Frontend Error:
```
ENDPOINT API TIDAK DITEMUKAN. PASTIKAN BACKEND SERVER BERJALAN DAN MENGGUNAKAN VERSI TERBARU.
```

### Backend Terminal Error:
```
ERROR: [Errno 10048] error while attempting to bind on address ('0.0.0.0', 8000): 
only one usage of each socket address (protocol/network address/port) is normally permitted
```

## Diagnosis

### Masalah Utama:
**Port 8000 sudah digunakan oleh proses lain**, sehingga backend server tidak bisa start.

### Timeline Error:
1. ✅ Database initialized successfully
2. ✅ Server process started [27812]
3. ✅ Application startup attempted
4. ❌ **ERROR: Port 8000 already in use** ← Masalah di sini!
5. ❌ Application shutdown (karena tidak bisa bind port)

### Konsekuensi:
- Backend server **gagal start** → tidak berjalan di port 8000
- API endpoints **tidak tersedia** → frontend tidak bisa connect
- Frontend mendapatkan error **404 Not Found**

## Solusi

### Solusi 1: Cari dan Stop Proses yang Menggunakan Port 8000 (RECOMMENDED)

#### Step 1: Cari Process ID (PID) yang menggunakan port 8000

**Windows PowerShell:**
```powershell
netstat -ano | findstr :8000
```

**Atau dengan detail lebih:**
```powershell
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess, State, LocalAddress, LocalPort
```

#### Step 2: Stop Proses tersebut

Setelah mendapatkan PID (Process ID), stop proses tersebut:

**Windows PowerShell:**
```powershell
# Ganti PID dengan nomor yang ditemukan dari step 1
taskkill /PID <PID> /F
```

**Contoh:**
```powershell
# Jika PID adalah 12345
taskkill /PID 12345 /F
```

**Windows CMD:**
```cmd
taskkill /PID <PID> /F
```

#### Step 3: Verifikasi Port 8000 sudah bebas

```powershell
netstat -ano | findstr :8000
```

Jika tidak ada output → port 8000 sudah bebas ✅

#### Step 4: Start Backend Server

```bash
cd backend
python main.py
```

Atau:
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Solusi 2: Gunakan Port Lain (Alternatif)

Jika port 8000 masih diperlukan oleh aplikasi lain:

#### Step 1: Update Backend untuk menggunakan port lain

**Edit `backend/main.py`:**
```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)  # Ganti ke port 8001
```

**Atau via command line:**
```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

#### Step 2: Update Frontend Configuration

Update `frontend/.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:8001
```

#### Step 3: Update Backend Services

Update semua file yang menggunakan `API_URL`:
- `frontend/services/falService.ts`
- `frontend/services/geminiService.ts`
- `frontend/services/api.ts`
- dll

**Default sudah menggunakan environment variable, jadi cukup update `.env.local`**

### Solusi 3: Kill All Python Processes (DRASTIC - Hati-hati!)

⚠️ **HATI-HATI**: Ini akan stop SEMUA Python processes!

```powershell
# Stop semua Python processes
Get-Process python | Stop-Process -Force
Get-Process pythonw | Stop-Process -Force

# Atau lebih spesifik (jika ada virtual env)
Get-Process python | Where-Object {$_.Path -like "*backend*"} | Stop-Process -Force
```

## Script Auto-Fix (Windows PowerShell)

Buat file `fix_port_8000.ps1`:

```powershell
# Find and kill process using port 8000
Write-Host "Mencari proses yang menggunakan port 8000..." -ForegroundColor Yellow

$connection = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

if ($connection) {
    $pid = $connection.OwningProcess
    Write-Host "Ditemukan proses dengan PID: $pid" -ForegroundColor Red
    
    $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host "Nama proses: $($process.ProcessName)" -ForegroundColor Yellow
        Write-Host "Path: $($process.Path)" -ForegroundColor Yellow
        
        Write-Host "Menghentikan proses..." -ForegroundColor Yellow
        Stop-Process -Id $pid -Force
        
        Start-Sleep -Seconds 2
        
        # Verify
        $check = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
        if (-not $check) {
            Write-Host "✅ Port 8000 sudah bebas!" -ForegroundColor Green
        } else {
            Write-Host "❌ Port 8000 masih digunakan" -ForegroundColor Red
        }
    } else {
        Write-Host "❌ Tidak bisa mendapatkan informasi proses" -ForegroundColor Red
    }
} else {
    Write-Host "✅ Port 8000 sudah bebas!" -ForegroundColor Green
}

Write-Host "`nSekarang jalankan backend server:" -ForegroundColor Cyan
Write-Host "cd backend" -ForegroundColor White
Write-Host "python main.py" -ForegroundColor White
```

**Cara pakai:**
```powershell
cd c:\project-gemini-ai
.\fix_port_8000.ps1
```

## Troubleshooting

### Jika Masih Error Setelah Kill Process

1. **Restart Computer** (langkah terakhir jika semua gagal)
   - Ini akan clear semua processes dan port conflicts

2. **Check Multiple Backend Instances**
   - Pastikan tidak ada multiple terminal windows yang menjalankan backend
   - Tutup semua terminal yang menjalankan backend
   - Start hanya satu instance

3. **Check Other Applications**
   - Beberapa aplikasi mungkin menggunakan port 8000:
     - Development servers lain (Django, Flask, dll)
     - Docker containers
     - Other FastAPI/Uvicorn servers
     - Database tools
     - Proxy servers

4. **Change Port Permanently**
   - Jika port 8000 selalu conflict, gunakan port lain:
     - 8001, 8002, 3001, dll
     - Update semua konfigurasi sesuai port baru

### Verifikasi Backend Running

Setelah fix, verifikasi backend berjalan dengan benar:

```bash
# Test endpoint
curl http://localhost:8000/docs

# Atau buka di browser
# http://localhost:8000/docs
```

Jika muncul Swagger UI → Backend berjalan dengan benar ✅

## Checklist

Setelah fix port conflict:

- [ ] ✅ Process yang menggunakan port 8000 sudah di-stop
- [ ] ✅ Port 8000 sudah bebas (verifikasi dengan netstat)
- [ ] ✅ Backend server berhasil start tanpa error
- [ ] ✅ Backend accessible di http://localhost:8000/docs
- [ ] ✅ Frontend bisa connect ke backend (test Generate Batch)
- [ ] ✅ Tidak ada error 404 di frontend

## Prevention

Untuk menghindari masalah ini di masa depan:

1. **Always check port sebelum start:**
   ```powershell
   netstat -ano | findstr :8000
   ```

2. **Use port yang berbeda untuk dev/prod**

3. **Document which port digunakan di project**

4. **Kill process dengan benar** (jangan force quit terminal)

5. **Use process manager** seperti PM2 atau Supervisor untuk production
