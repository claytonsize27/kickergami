param(
    [string]$ProjectDir = "C:\Users\clayt\OneDrive\Documents\Kickeragami\kickergami"
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $ProjectDir

$venvPython = Join-Path $ProjectDir ".venv\Scripts\python.exe"
if (Test-Path -LiteralPath $venvPython) {
    & $venvPython "scripts\run_scheduled_update.py"
} else {
    python "scripts\run_scheduled_update.py"
}

