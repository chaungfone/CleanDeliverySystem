# security_smoke.ps1 - Security smoke verification for CleanDeliverySystem (Phase 1)
# Runs backend/scripts/security_smoke.py against the app (no live DB/network required).
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$Backend = Join-Path $Root "backend"
$Py = Join-Path $Backend ".venv\Scripts\python.exe"

if (-not (Test-Path $Py)) {
    Write-Host "[ERROR] Virtualenv not found: $Py" -ForegroundColor Red
    exit 1
}

Write-Host "=== Security Smoke (Phase 1) ===" -ForegroundColor Cyan
& $Py (Join-Path $PSScriptRoot "security_smoke.py")
$code = $LASTEXITCODE

if ($code -eq 0) {
    Write-Host "`nSMOKE OK - all security checks passed." -ForegroundColor Green
} else {
    Write-Host "`nSMOKE FAILED - review output above." -ForegroundColor Red
}
exit $code
