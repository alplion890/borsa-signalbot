[CmdletBinding()]
param(
    [ValidateSet('scan', 'mobile', 'both', 'inbox')]
    [string]$Mode = 'scan'
)

$ErrorActionPreference = 'Stop'
if ($Mode -ne 'inbox' -and (Get-Date).DayOfWeek -in @('Saturday', 'Sunday')) { exit 0 }
$root = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $root '.signalbot\local.env'
if (-not (Test-Path -LiteralPath $envFile)) {
    $envFile = Join-Path $root 'strategy-lab\.env'
}

if (-not (Test-Path -LiteralPath $envFile)) {
    throw "Yerel sir dosyasi yok: $envFile. .signalbot\\local.env.example dosyasini kopyalayip degerleri ekleyin."
}

# Sirlar sadece bu islem ve onun Python alt islemlerine aktarilir; ekrana ve
# Task Scheduler tanimina yazilmaz.
foreach ($line in Get-Content -LiteralPath $envFile -Encoding UTF8) {
    $trimmed = $line.TrimStart([char]0xFEFF).Trim()
    if (-not $trimmed -or $trimmed.StartsWith('#')) { continue }
    # Windows PowerShell 5 Turkish culture mishandles ASCII I in -match ranges.
    if ($trimmed -cnotmatch '^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$') {
        throw "Gecersiz local.env satiri (deger yazdirilmadi)."
    }
    if ($Matches[1] -in @('TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID', 'FINNHUB_API_KEY', 'LSE_API_KEY', 'SIGNALBOT_PYTHON', 'PHASE', 'ACCOUNT_BALANCE')) {
        [Environment]::SetEnvironmentVariable($Matches[1], $Matches[2].Trim().Trim('"').Trim("'"), 'Process')
    }
}

foreach ($key in 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID') {
    if ([string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($key, 'Process'))) {
        throw "local.env icinde zorunlu $key eksik."
    }
}

$env:SIGNALBOT_STATE_PATH = Join-Path $root '.signalbot\state.json'
$env:MOBILE_WATCH_STATE_PATH = Join-Path $root '.signalbot\mobile_watch.json'
$env:MOBILE_WATCH_HEALTH_PATH = Join-Path $root '.signalbot\mobile_health.jsonl'
$env:MT5_CONTEXT_PATH = Join-Path $root '.signalbot\mt5_context.json'
$env:TELEGRAM_INBOX_STATE_PATH = Join-Path $root '.signalbot\telegram_inbox.json'
$env:TELEGRAM_DECISION_NOTES_PATH = Join-Path $root '.signalbot\telegram_decision_notes.json'
$env:EMA12_PAPER_STATE_PATH = Join-Path $root '.signalbot\ema12_paper_local.json'
$env:PYTHONPATH = Join-Path $root 'strategy-lab'
$env:PYTHONIOENCODING = 'utf-8'
$bundledPython = Join-Path $env:USERPROFILE 'vectorbt-lab\.venv\Scripts\python.exe'
$python = if ($env:SIGNALBOT_PYTHON) { $env:SIGNALBOT_PYTHON } elseif (Test-Path -LiteralPath $bundledPython) { $bundledPython } else { 'python' }
if ($Mode -ne 'inbox') {
    & $python -m intraday.signalbot.scan_schedule | Out-Null
    if ($LASTEXITCODE -eq 1) { exit 0 }
    if ($LASTEXITCODE -ne 0) { throw 'Tarama saat kapisi calistirilamadi.' }
}
$log = Join-Path $root '.signalbot\local_scanner.log'
$contextLog = Join-Path $root '.signalbot\mt5_context.log'
$inboxLog = Join-Path $root '.signalbot\telegram_inbox.log'
New-Item -ItemType Directory -Path (Split-Path -Parent $log) -Force | Out-Null

Push-Location $root
try {
    if ($Mode -eq 'inbox') {
        & $python -m intraday.signalbot.telegram_inbox 2>&1 | Out-File -LiteralPath $inboxLog -Encoding UTF8 -Append
        exit $LASTEXITCODE
    }
    & $python -m intraday.signalbot.mt5_context 2>&1 | Out-File -LiteralPath $contextLog -Encoding UTF8 -Append
    $brokerContext = Get-Content -LiteralPath $env:MT5_CONTEXT_PATH -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($brokerContext.status -eq 'ok') {
        $env:ACCOUNT_BALANCE = ([double]$brokerContext.balance).ToString([System.Globalization.CultureInfo]::InvariantCulture)
    }
    $cloudPrimary = (& $python -c "from intraday.signalbot.local_lease import cloud_active; print('true' if cloud_active() else 'false')").Trim() -eq 'true'
    $scanArgs = @()
    $alertArgs = @()
    if ($cloudPrimary) { $scanArgs = @('--dry-run'); $alertArgs = @('--suppress-alert') }
    if ($Mode -in 'scan', 'both') {
        "$(Get-Date -Format o) scan basladi" | Add-Content -LiteralPath $log -Encoding UTF8
        $scanOutput = @(& $python (Join-Path $root 'run_bot.py') @scanArgs 2>&1)
        $scanExit = $LASTEXITCODE
        $scanOutput | Out-File -LiteralPath $log -Encoding UTF8 -Append
    }
    if ($Mode -in 'mobile', 'both') {
        & $python -m intraday.signalbot.mobile_watch @alertArgs 2>&1 | Out-File -LiteralPath $log -Encoding UTF8 -Append
        $mobileExit = $LASTEXITCODE
        & $python -m intraday.signalbot.ema12_paper --suppress-result @alertArgs 2>&1 | Out-File -LiteralPath $log -Encoding UTF8 -Append
        $paperExit = $LASTEXITCODE
    }
    if ($Mode -in 'scan', 'both') {
        & $python -m intraday.signalbot.market_events 2>&1 | Out-File -LiteralPath $log -Encoding UTF8 -Append
        $marketExit = $LASTEXITCODE
    }
    "$(Get-Date -Format o) bitti scan=$scanExit mobile=$mobileExit paper=$paperExit makro=$marketExit" | Add-Content -LiteralPath $log -Encoding UTF8
    if ($scanExit -or $mobileExit -or $paperExit -or $marketExit) { exit 1 }
    if ($Mode -in 'scan', 'both' -and ($scanOutput -match 'hata 0, veri kontrolu [1-9]')) {
        & $python -m intraday.signalbot.local_lease 2>&1 | Out-File -LiteralPath $log -Encoding UTF8 -Append
    }
}
finally {
    Pop-Location
}
