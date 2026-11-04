[CmdletBinding()]
param([string]$Python = (Get-Command pythonw.exe -ErrorAction Stop).Source)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$lab = Join-Path $root 'strategy-lab'
$user = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$action = New-ScheduledTaskAction -Execute $Python -Argument '-m intraday.research_panel.sync --once' -WorkingDirectory $lab
$repeat = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 5)
$login = New-ScheduledTaskTrigger -AtLogOn -User $user
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 3) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 2 -RestartInterval (New-TimeSpan -Minutes 1)
$principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName 'Borsa-ResearchPanel-Sync' -Action $action -Trigger @($repeat,$login) -Settings $settings -Principal $principal -Description 'GitHub cloud ledger mirror for the local research panel; no broker access or notifications.' -Force | Out-Null
Start-ScheduledTask -TaskName 'Borsa-ResearchPanel-Sync'
$panelAction = New-ScheduledTaskAction -Execute $Python -Argument '-m intraday.research_panel --port 8766' -WorkingDirectory $lab
$panelSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName 'Borsa-ResearchPanel-Dashboard' -Action $panelAction -Trigger $login -Settings $panelSettings -Principal $principal -Description 'Local-only research panel on 127.0.0.1:8766; starts at user logon.' -Force | Out-Null
Write-Output 'Cloud mirror: logon + every 5 minutes. Dashboard: logon. MT5 measurement: existing ForwardEA-5dk.'
