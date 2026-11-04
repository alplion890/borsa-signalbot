[CmdletBinding()]
param([string]$Python = 'C:\Users\quantum\vectorbt-lab\.venv\Scripts\pythonw.exe')
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Python)) { throw 'MT5 Python environment missing' }
$lab = Join-Path (Split-Path -Parent $PSScriptRoot) 'strategy-lab'
$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$action = New-ScheduledTaskAction -Execute $Python -Argument '-m intraday.research_panel.broker_history --count 40000 --daily-if-needed' -WorkingDirectory $lab
$triggers = @((New-ScheduledTaskTrigger -AtLogOn -User $user), (New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 5)))
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 5) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName 'Borsa-ResearchPanel-BrokerHistory' -Action $action -Trigger $triggers -Settings $settings -Principal $principal -Description 'Read-only Maven MT5 closed-bar history snapshots; never starts terminal or sends orders.' -Force | Out-Null
Write-Output 'Broker history: checks every 5 minutes/logon, exports at most daily per pair; MT5 must already be open.'
