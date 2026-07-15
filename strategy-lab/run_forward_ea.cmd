@echo off
rem Forward EA tek dongu — Task Scheduler her 5 dk cagirir.
rem MT5 terminali acik olmali; kapaliysa dongu sessizce atlanir (log'a yazar).
cd /d "%~dp0"
set PYTHONPATH=%~dp0
set PYTHONIOENCODING=utf-8
"C:\Users\quantum\vectorbt-lab\.venv\Scripts\python.exe" -m intraday.forward_ea.live_runner --once >> "%~dp0outputs\intraday\forward_ea\runner.log" 2>&1
