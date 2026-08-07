param(
    [switch]$SkipBuild
)
$ErrorActionPreference = "Stop"

$root   = Split-Path -Parent $PSScriptRoot
$dist   = Join-Path $root "web-dashboard\dist"
$backend = Join-Path $root "backend"
$outZip = Join-Path $root "pythonanywhere_upload.zip"

if (-not $SkipBuild) {
    Push-Location (Join-Path $root "web-dashboard")
    try {
        Write-Host "Building web-dashboard (npm run build:prod) ..."
        npm run build:prod
        if ($LASTEXITCODE -ne 0) { throw "Frontend build failed" }
    } finally {
        Pop-Location
    }
}

$tmp = Join-Path $env:TEMP ("pa_pkg_" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tmp | Out-Null
try {
    $stageBackend = Join-Path $tmp "backend"
    Copy-Item -LiteralPath $backend -Destination $stageBackend -Recurse

    foreach ($x in @(".venv", "__pycache__", ".pytest_cache", ".ruff_cache", ".artifacts", ".dbg", "logs", "scratch")) {
        $p = Join-Path $stageBackend $x
        if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Recurse -Force }
    }
    foreach ($f in @(".env", ".env.production", ".env.staging")) {
        $p = Join-Path $stageBackend $f
        if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Force }
    }

    $stageDist = Join-Path $tmp "web-dashboard"
    New-Item -ItemType Directory -Path $stageDist | Out-Null
    Copy-Item -LiteralPath $dist -Destination (Join-Path $stageDist "dist") -Recurse

    if (Test-Path -LiteralPath $outZip) { Remove-Item -LiteralPath $outZip -Force }
    Compress-Archive -Path (Join-Path $tmp "*") -DestinationPath $outZip -CompressionLevel Optimal

    Write-Output "Created $outZip"
    Get-Item $outZip | Select-Object FullName, @{n = 'SizeMB'; e = { [math]::Round($_.Length / 1MB, 2) } }
} finally {
    Remove-Item -LiteralPath $tmp -Recurse -Force
}
