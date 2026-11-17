# PowerShell script to run Docker directly on this folder
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "  Khoi dong Docker Website Ban Giay                " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

$composeCmd = $null
if (Get-Command "docker-compose" -ErrorAction SilentlyContinue) {
    $composeCmd = "docker-compose"
} else {
    $versionOutput = & docker compose version 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0 -and $versionOutput -notmatch "unknown command") {
        $composeCmd = "docker compose"
    }
}

if (-not $composeCmd) {
    Write-Host "[LOI] Khong tim thay Docker Compose. Vui long bat Docker Desktop!" -ForegroundColor Red
    exit 1
}

Write-Host "Su dung lenh: $composeCmd" -ForegroundColor Yellow
Write-Host "Dang dung container cu (neu co)..." -ForegroundColor Gray
if ($composeCmd -eq "docker-compose") {
    & docker-compose down *>$null
} else {
    & docker compose down *>$null
}

Write-Host "Dang build va khoi chay website trong container..." -ForegroundColor Yellow
if ($composeCmd -eq "docker-compose") {
    & docker-compose up -d --build --remove-orphans
} else {
    & docker compose up -d --build --remove-orphans
}

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "====================================================" -ForegroundColor Green
    Write-Host "  Website ban giay da khoi dong thanh cong!" -ForegroundColor Green
    Write-Host "  Dang tu dong mo trinh duyet: http://localhost:5000 ..." -ForegroundColor Green
    Write-Host "====================================================" -ForegroundColor Green
    
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:5000"
} else {
    Write-Host "[LOI] Khoi dong Docker that bai. Kiem tra xem Docker Desktop da bat chua." -ForegroundColor Red
}
