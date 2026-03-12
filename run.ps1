# 3D AI Organizers Quick Start Script

Write-Host "--- Stabilizing Environment ---" -ForegroundColor Cyan

# 1. Kill processes on transition ports to avoid EADDRINUSE
$ports = @(5173, 17831)
foreach ($port in $ports) {
    $proc = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($proc) {
        Write-Host "Cleaning up port $port..." -ForegroundColor Yellow
        Stop-Process -Id $proc.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}

# 2. Safety check for Node modules
if (-not (Test-Path "ui/electron-app/node_modules")) {
    Write-Host "Installing UI dependencies..." -ForegroundColor Cyan
    Set-Location "ui/electron-app"
    powershell -ExecutionPolicy Bypass -Command "npm install"
    Set-Location "../.."
}

# 3. Safety check for Python dependencies
Write-Host "Verifying Python dependencies..." -ForegroundColor Cyan
pip install -r backend/requirements.txt --quiet

# 4. Handle Electron/Vite ESM conflict fixes if reverted
$pkgJsonPath = "ui/electron-app/package.json"
$pkgJson = Get-Content $pkgJsonPath | ConvertFrom-Json
if ($pkgJson.PSObject.Properties.Name -contains "type") {
    Write-Host "Applying ESM fix to package.json..." -ForegroundColor Yellow
    $pkgJson.PSObject.Properties.Remove("type")
    $pkgJson | ConvertTo-Json -Depth 10 | Set-Content $pkgJsonPath
}

# 5. Launch
Write-Host "--- Launching App ---" -ForegroundColor Green
node dev.js
