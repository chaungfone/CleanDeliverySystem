<#
PowerShell script to run backend tests in Windows environment.
Usage: .\scripts\run_tests.ps1
#>
param(
    [string]$Python = "python",
    [string]$VenvPath = ".venv"
)

# Create virtualenv if not exists
if (-not (Test-Path $VenvPath)) {
    & $Python -m venv $VenvPath
}

$activate = Join-Path $VenvPath "Scripts\Activate.ps1"
. $activate

pip install -r backend/requirements.txt
pip install pytest

# Ensure tests run from backend folder
Push-Location backend
pytest tests -v
Pop-Location
