# Cara Menjalankan Backend

## Quick Start

### Windows PowerShell:
```powershell
cd C:\project-gemini-ai\backend
.\run.ps1
```

Atau menggunakan alias pendek:
```powershell
.\start.ps1
```

## Manual (Jika Script Tidak Berfungsi)

### 1. Menggunakan Path Lengkap:
```powershell
cd C:\project-gemini-ai\backend
.\venv\Scripts\python.exe main.py
```

### 2. Aktifkan Virtual Environment Terlebih Dahulu:
```powershell
cd C:\project-gemini-ai\backend
.\venv\Scripts\Activate.ps1
python main.py
```

## Troubleshooting

### Error: "Virtual environment not found"
```powershell
# Buat virtual environment
python -m venv venv

# Install dependencies
.\venv\Scripts\pip install -r requirements.txt
```

### Error: "ModuleNotFoundError: No module named 'mediapipe'"
Pastikan menggunakan Python dari virtual environment:
```powershell
.\venv\Scripts\python.exe main.py
```

### Error: "Port 8000 already in use"
```powershell
# Cari process yang menggunakan port 8000
netstat -ano | findstr :8000

# Kill process (ganti PID dengan nomor yang ditemukan)
taskkill /PID <PID> /F
```

## Server URL

Setelah berhasil menjalankan, server akan tersedia di:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
