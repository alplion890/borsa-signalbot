$ErrorActionPreference = 'Stop'
if ((Get-TimeZone).Id -ne 'Turkey Standard Time') { throw 'Bu gorev Turkiye yerel saati gerektirir.' }
$runner = Join-Path $PSScriptRoot 'run-coverage-watchdog.ps1'
$launcher = Join-Path $PSScriptRoot 'run-borsa-hidden.vbs'
$action = New-ScheduledTaskAction -Execute (Join-Path $env:SystemRoot 'System32\wscript.exe') -Argument "//B //Nologo `"$launcher`" `"$runner`""
$trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At '20:10'
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 5)
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName 'Borsa-Seans-Tarama-Alarmi' -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
Write-Output 'Bagimsiz seans alarmi kuruldu: hafta ici 20:10 TR; bilgisayar ve kullanici oturumu acik olmali.'
