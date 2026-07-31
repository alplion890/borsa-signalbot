@echo off
rem Forward EA tek dongu — Task Scheduler her 5 dk cagirir.
rem MT5 terminali acik olmali; kapaliysa dongu sessizce atlar (log'a yazar).
rem
rem Python yolu: FORWARD_EA_PYTHON ortam degiskeninden okunur. Tanimli degilse
rem %USERPROFILE%\vectorbt-lab\.venv altindaki venv denenir, o da yoksa PATH'teki
rem python kullanilir. Boylece kullanici adi/makine yolu repoya yazilmaz.
cd /d "%~dp0"
set PYTHONPATH=%~dp0
set PYTHONIOENCODING=utf-8

set "PY=%FORWARD_EA_PYTHON%"
if not defined PY set "PY=%USERPROFILE%\vectorbt-lab\.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

"%PY%" -m intraday.forward_ea.live_runner --once >> "%~dp0outputs\intraday\forward_ea\runner.log" 2>&1
