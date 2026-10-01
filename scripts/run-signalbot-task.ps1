[CmdletBinding()]
param(
    [ValidateSet('scan', 'mobile', 'both', 'inbox')]
    [string]$Mode = 'both'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$log = Join-Path $root '.signalbot\task_errors.log'
try {
    & (Join-Path $PSScriptRoot 'run-signalbot-local.ps1') -Mode $Mode
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
catch {
    $entry = "$(Get-Date -Format o) type=$($_.Exception.GetType().FullName) line=$($_.InvocationInfo.ScriptLineNumber) script=$([IO.Path]::GetFileName($_.InvocationInfo.ScriptName))"
    Add-Content -LiteralPath $log -Value $entry -Encoding UTF8
    $_.ScriptStackTrace | Add-Content -LiteralPath $log -Encoding UTF8
    exit 1
}
