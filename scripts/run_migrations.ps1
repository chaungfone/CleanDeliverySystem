<#
PowerShell script to run Supabase migrations on Windows.
Usage: .\scripts\run_migrations.ps1   (requires $env:DIRECT_URL or -DirectUrl)
Requires: npx (Node) with the Supabase CLI, or `supabase` on PATH.
#>
param(
    [string]$DirectUrl = $env:DIRECT_URL,
    [string]$ProjectRef = $env:SUPABASE_PROJECT_ID
)

if (-not $DirectUrl) {
    Write-Error "DIRECT_URL not set. Use: .\scripts\run_migrations.ps1 -DirectUrl postgresql://..."
    exit 2
}

$env:DATABASE_URL = $DirectUrl

# Prefer a globally installed supabase CLI; otherwise fall back to npx.
$supabase = Get-Command supabase -ErrorAction SilentlyContinue
if ($supabase) {
    & supabase db push
} else {
    npx --yes supabase db push
}

exit $LASTEXITCODE
