Option Explicit
Dim shell, command, runner, mode, quote, result
If WScript.Arguments.Count < 1 Or WScript.Arguments.Count > 2 Then WScript.Quit 2
runner = WScript.Arguments(0)
quote = Chr(34)
If InStr(runner, quote) > 0 Then WScript.Quit 2
Set shell = CreateObject("WScript.Shell")
command = quote & shell.ExpandEnvironmentStrings("%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe") & quote
command = command & " -WindowStyle Hidden -NoProfile -NonInteractive -ExecutionPolicy Bypass -File " & quote & runner & quote
If WScript.Arguments.Count = 2 Then
    mode = WScript.Arguments(1)
    If mode <> "scan" And mode <> "mobile" And mode <> "both" And mode <> "inbox" Then WScript.Quit 2
    command = command & " -Mode " & mode
End If
' GUI host starts the console hidden from creation, and preserves its exit code.
result = shell.Run(command, 0, True)
WScript.Quit result
