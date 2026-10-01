[CmdletBinding(SupportsShouldProcess)]
param()

$ErrorActionPreference = 'Stop'
if ((Get-TimeZone).Id -ne 'Turkey Standard Time') { throw 'Bu gorev Turkiye yerel saati gerektirir.' }
$root = Split-Path -Parent $PSScriptRoot
$runner = Join-Path $PSScriptRoot 'run-signalbot-task.ps1'
$hiddenHost = Join-Path $env:SystemRoot 'System32\wscript.exe'
$launcher = Join-Path $PSScriptRoot 'run-borsa-hidden.vbs'

if (-not (Test-Path -LiteralPath (Join-Path $root '.signalbot\local.env')) -and -not (Test-Path -LiteralPath (Join-Path $root 'strategy-lab\.env'))) {
    throw 'Once .signalbot\\local.env.example dosyasini .signalbot\\local.env olarak kopyalayip Telegram degerlerini ekleyin; sonra bu komutu yeniden calistirin.'
}

function Set-BorsaTask {
    param([string]$Name, [string]$At, [int]$DurationHours, [string]$Mode)

    $action = New-ScheduledTaskAction -Execute $hiddenHost -Argument "//B //Nologo `"$launcher`" `"$runner`" $Mode"
    $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At $At
    # The cmdlet exposes repetition only on a once trigger; copy its CIM value.
    $repeating = New-ScheduledTaskTrigger -Once -At $At -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration (New-TimeSpan -Hours $DurationHours)
    $trigger.Repetition = $repeating.Repetition
    $trigger.Repetition.Interval = 'PT5M'
    $trigger.Repetition.Duration = "PT$DurationHours`H"
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 4)
    $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited

    if ($PSCmdlet.ShouldProcess($Name, 'Windows Task Scheduler gorevini kaydet')) {
        Register-ScheduledTask -TaskName $Name -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Force | Out-Null
        Write-Host "$Name kaydedildi: hafta ici $At, 5 dakikada bir, $DurationHours saat."
    }
}

# Yerel saat Windows'un Europe/Istanbul saatidir.
# Every weekday 09:00-00:00 TR, every five minutes. The Python calendar gate
# stops actual scans at the NY close (including DST, holidays and early closes).
# EUR/GBP retired 2026-09-30. Remove the obsolete London-only task.
if (Get-ScheduledTask -TaskName 'Borsa-Signalbot-London' -ErrorAction SilentlyContinue) {
    if ($PSCmdlet.ShouldProcess('Borsa-Signalbot-London', 'Remove retired London scan task')) {
        Unregister-ScheduledTask -TaskName 'Borsa-Signalbot-London' -Confirm:$false
    }
}
Set-BorsaTask -Name 'Borsa-Signalbot-NQ-Mobile' -At '09:00' -DurationHours 15 -Mode 'both'
