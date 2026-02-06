# Fix: Error Port 8000 Already In Use di Backend

## ❌ Error yang Terjadi:

```
ERROR: [Errno 10048] error while attempting to bind on address ('0.0.0.0', 8000): 
only one usage of each socket address (protocol/network address/port) is normally permitted
```

## 🔍 Diagnosa:

### Masalah:
- **Port 8000 sudah digunakan** oleh process lain (PID: 5424)
- Backend server tidak bisa start karena port sudah occupied
- Process yang menggunakan port: `node.exe` atau `python.exe` (backend server lama)

### Root Cause:
Backend server sebelumnya masih berjalan dan belum dihentikan dengan benar.

## ✅ Solusi:

### 1. Kill Process yang Menggunakan Port 8000

**Cara 1: Manual (PowerShell)**
```powershell
# Cek process yang menggunakan port 8000
netstat -ano | findstr :8000

# Output: TCP    0.0.0.0:8000           0.0.0.0:0              LISTENING       5424

# Kill process
taskkill /PID 5424 /F

# Verify port bebas
netstat -ano | findstr :8000
# (Output kosong = port sudah bebas)
```

**Cara 2: Otomatis (Script)**
```powershell
# Jalankan script fix
.\fix_port_8000.ps1
```

**Cara 3: Kill Semua Python Process (Hati-hati!)**
```powershell
Get-Process | Where-Object {$_.ProcessName -eq "python"} | Stop-Process -Force
```

### 2. Verifikasi Konfigurasi

**Cek Konfigurasi fal:**
```bash
cd backend
python -c "from fal_service import FAL_NUM_INFERENCE_STEPS, FAL_GUIDANCE_SCALE; print(f'Steps: {FAL_NUM_INFERENCE_STEPS}, CFG: {FAL_GUIDANCE_SCALE}')"
```

**Expected Output:**
```
Steps: 7
CFG: 3.5
```

### 3. Start Backend Server

```bash
cd backend
python main.py
```

**Expected Output:**
```
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

## 🔧 Quick Fix Script

**File**: `fix_port_8000.ps1` (sudah ada di project root)

```powershell
# Jalankan script untuk auto-fix
.\fix_port_8000.ps1
```

Script ini akan:
1. ✅ Cari process yang menggunakan port 8000
2. ✅ Kill process tersebut (jika Python)
3. ✅ Verify port sudah bebas
4. ✅ Berikan instruksi next steps

## 📋 Checklist Fix:

- [x] ✅ Cek process yang menggunakan port 8000
- [x] ✅ Kill process (PID: 5424)
- [x] ✅ Verify port 8000 bebas
- [x] ✅ Verifikasi konfigurasi (Steps: 7, CFG: 3.5)
- [ ] ⏳ Start backend server: `cd backend; python main.py`
- [ ] ⏳ Test endpoint: http://localhost:8000/docs

## ⚠️ Catatan:

### Jika Error Masih Terjadi:

1. **Port masih digunakan:**
   ```powershell
   # Kill semua node dan python process
   Get-Process | Where-Object {$_.ProcessName -match "python|node"} | Stop-Process -Force
   ```

2. **Port digunakan oleh process lain:**
   - Cek apakah ada aplikasi lain yang menggunakan port 8000
   - Atau ganti port di `backend/main.py`:
     ```python
     uvicorn.run(app, host="0.0.0.0", port=8001)  # Ganti ke port lain
     ```

3. **Firewall/Antivirus blocking:**
   - Cek Windows Firewall
   - Cek Antivirus settings
   - Allow Python/uvicorn di firewall

## ✅ Status: ERROR SUDAH DIPERBAIKI

**Port 8000 sudah bebas. Backend server bisa dijalankan sekarang!**

Silakan jalankan:
```bash
cd backend
python main.py
```

---

**Status**: ✅ **PORT 8000 SUDAH DIBERSIHKAN - BACKEND SIAP DIJALANKAN**
