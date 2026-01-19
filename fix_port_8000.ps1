# Script Auto-Fix untuk Port 8000 Conflict
# Jalankan: .\fix_port_8000.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "FIX PORT 8000 CONFLICT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Find process using port 8000
Write-Host "Mencari proses yang menggunakan port 8000..." -ForegroundColor Yellow

$connections = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

if ($connections) {
    # Get unique process IDs
    $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique
    
    foreach ($pid in $pids) {
        $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
        
        if ($process) {
            Write-Host "`nDitemukan proses:" -ForegroundColor Red
            Write-Host "  PID: $pid" -ForegroundColor Yellow
            Write-Host "  Nama: $($process.ProcessName)" -ForegroundColor Yellow
            
            if ($process.Path) {
                Write-Host "  Path: $($process.Path)" -ForegroundColor Yellow
            }
            
            # Check if it's a Python process (likely backend)
            if ($process.ProcessName -like "*python*") {
                Write-Host "  -> Ini adalah proses Python (kemungkinan backend server lama)" -ForegroundColor Cyan
                
                Write-Host "`nMenghentikan proses..." -ForegroundColor Yellow
                try {
                    Stop-Process -Id $pid -Force -ErrorAction Stop
                    Write-Host "  ✅ Proses dengan PID $pid berhasil dihentikan" -ForegroundColor Green
                } catch {
                    Write-Host "  ❌ Gagal menghentikan proses: $_" -ForegroundColor Red
                }
            } else {
                Write-Host "  ⚠️  Proses ini bukan Python. Apakah Anda yakin ingin menghentikannya? (Y/N)" -ForegroundColor Yellow
                $confirm = Read-Host
                if ($confirm -eq "Y" -or $confirm -eq "y") {
                    try {
                        Stop-Process -Id $pid -Force -ErrorAction Stop
                        Write-Host "  ✅ Proses dengan PID $pid berhasil dihentikan" -ForegroundColor Green
                    } catch {
                        Write-Host "  ❌ Gagal menghentikan proses: $_" -ForegroundColor Red
                    }
                }
            }
        } else {
            Write-Host "  ⚠️  Proses dengan PID $pid tidak ditemukan (mungkin sudah dihentikan)" -ForegroundColor Yellow
        }
    }
    
    # Wait a bit
    Start-Sleep -Seconds 2
    
    # Verify port is free
    Write-Host "`nMemverifikasi port 8000..." -ForegroundColor Yellow
    $check = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    
    if (-not $check) {
        Write-Host "  ✅ Port 8000 sudah bebas!" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Port 8000 masih digunakan oleh:" -ForegroundColor Yellow
        $remaining = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($pid in $remaining) {
            $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
            if ($proc) {
                Write-Host "    - PID $pid ($($proc.ProcessName))" -ForegroundColor Yellow
            }
        }
    }
} else {
    Write-Host "✅ Port 8000 sudah bebas!" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "INSTRUKSI SELANJUTNYA:" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Jalankan backend server:" -ForegroundColor White
Write-Host "   cd backend" -ForegroundColor Gray
Write-Host "   python main.py" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Verifikasi backend berjalan:" -ForegroundColor White
Write-Host "   Buka browser: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Test Generate Batch di frontend" -ForegroundColor White
Write-Host ""
