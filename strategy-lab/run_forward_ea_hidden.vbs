' Forward EA'yi PENCERE ACMADAN calistirir.
' Task Scheduler dogrudan .cmd cagirinca 5 dakikada bir cmd penceresi acilip
' kapaniyordu. Bu shim ayni .cmd'yi gizli pencerede kosturur.
' Wait for Python so Task Scheduler receives the actual exit status.
Dim shell, here, result
Set shell = CreateObject("WScript.Shell")
here = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))
result = shell.Run("""" & here & "run_forward_ea.cmd""", 0, True)
WScript.Quit result
