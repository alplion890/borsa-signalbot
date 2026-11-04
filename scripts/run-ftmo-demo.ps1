param(
    [ValidateSet('Inspect', 'Check', 'Micro', 'Preview', 'DemoRun', 'Dashboard')]
    [string]$Mode = 'Inspect',
    [string]$TerminalPath = 'C:\Program Files\MetaTrader 5\terminal64.exe'
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$labPath = Join-Path $repoRoot 'strategy-lab'
$pythonPath = Join-Path $env:USERPROFILE 'vectorbt-lab\.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "Python ortami bulunamadi: $pythonPath"
}
Push-Location -LiteralPath $labPath
try {
    switch ($Mode) {
        'Inspect' { & $pythonPath -m intraday.ftmo_demo inspect --terminal-path $TerminalPath }
        'Check' { & $pythonPath -m intraday.ftmo_demo check }
        'Micro' { & $pythonPath -m intraday.ftmo_demo micro }
        'Preview' { & $pythonPath -m intraday.ftmo_demo run }
        'DemoRun' { & $pythonPath -m intraday.ftmo_demo run --execute-demo }
        'Dashboard' { & $pythonPath -m intraday.ftmo_demo dashboard }
    }
    if ($LASTEXITCODE -ne 0) { throw "FTMO komutu durdu (kod $LASTEXITCODE); otomatik tekrar denenmedi." }
}
finally { Pop-Location }
