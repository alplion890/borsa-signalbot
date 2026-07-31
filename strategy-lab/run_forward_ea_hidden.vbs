' Forward EA'yi PENCERE ACMADAN calistirir.
' Task Scheduler dogrudan .cmd cagirinca 5 dakikada bir cmd penceresi acilip
' kapaniyordu. Bu shim ayni .cmd'yi gizli pencerede kosturur.
'   Run(komut, 0, False) -> 0 = pencere gizli, False = bitmesini bekleme
Dim shell, here
Set shell = CreateObject("WScript.Shell")
here = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))
shell.Run """" & here & "run_forward_ea.cmd""", 0, False
