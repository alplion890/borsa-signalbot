$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path -LiteralPath (Join-Path $root 'strategy-lab\.env')) -and -not (Test-Path -LiteralPath (Join-Path $root '.signalbot\local.env'))) { throw 'Telegram sir dosyasi yok.' }
$runner = Join-Path $PSScriptRoot 'run-signalbot-local.ps1'
$launcher = Join-Path $PSScriptRoot 'run-borsa-hidden.vbs'
$action = New-ScheduledTaskAction -Execute (Join-Path $env:SystemRoot 'System32\wscript.exe') -Argument "//B //Nologo `"$launcher`" `"$runner`" inbox"
$trigger = New-ScheduledTaskTrigger -Daily -At '00:00'
$repeating = New-ScheduledTaskTrigger -Once -At '00:00' -RepetitionInterval (New-TimeSpan -Minutes 1) -RepetitionDuration (New-TimeSpan -Hours 24)
$trigger.Repetition = $repeating.Repetition
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 2)
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName 'Borsa-Telegram-Defter' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
Write-Output 'Telegram defter koprusu kaydedildi: PC ve oturum acikken her dakika.'
