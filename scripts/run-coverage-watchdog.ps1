$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = Join-Path $root 'strategy-lab'
$env:PYTHONIOENCODING = 'utf-8'
$python = Join-Path $env:USERPROFILE 'vectorbt-lab\.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { $python = (Get-Command python -ErrorAction Stop).Source }
$log = Join-Path $root '.signalbot\coverage_watchdog.log'
New-Item -ItemType Directory -Path (Split-Path -Parent $log) -Force | Out-Null
Push-Location $root
try {
    & $python -m intraday.signalbot.coverage_watchdog >> $log 2>&1
    exit $LASTEXITCODE
} finally { Pop-Location }
