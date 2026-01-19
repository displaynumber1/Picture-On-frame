# Script untuk menjalankan backend dengan virtual environment
# Usage: .\run.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Backend Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please run: python -m venv venv" -ForegroundColor Yellow
    Write-Host "Then install dependencies: .\venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# Check if main.py exists
if (-not (Test-Path ".\main.py")) {
    Write-Host "ERROR: main.py not found!" -ForegroundColor Red
    Write-Host "Please make sure you're in the backend directory" -ForegroundColor Yellow
    exit 1
}

# Display Python version
$pythonVersion = & ".\venv\Scripts\python.exe" --version
Write-Host "Python: $pythonVersion" -ForegroundColor Green

# Check if required modules are installed
Write-Host "Checking dependencies..." -ForegroundColor Yellow
try {
    & ".\venv\Scripts\python.exe" -c "import fastapi, mediapipe, cv2; print('All dependencies OK')" 2>&1 | Out-Null
    Write-Host "Dependencies: OK" -ForegroundColor Green
} catch {
    Write-Host "WARNING: Some dependencies may be missing" -ForegroundColor Yellow
    Write-Host "Run: .\venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting server on http://localhost:8000" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Run the backend
& ".\venv\Scripts\python.exe" main.py
