@echo off
setlocal EnableDelayedExpansion
set "PUBLISH_RC="
chcp 65001 >nul
title Forward EA - Veri Guncelle
cd /d "%~dp0"
set PYTHONPATH=%~dp0
set PYTHONIOENCODING=utf-8

set "PY=%FORWARD_EA_PYTHON%"
if not defined PY set "PY=%USERPROFILE%\vectorbt-lab\.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"

echo.
echo  ============================================================
echo   FORWARD EA - kacirilan barlari yakala
echo  ============================================================
echo.
echo  MT5 terminali kapaliysa kendisi acilir (giris yapilmis olmali).
echo  En fazla 40 GUN ara verebilirsin; daha uzun ara veri kaybettirir.
echo.

"%PY%" -m intraday.forward_ea.live_runner --once
set "RC=%ERRORLEVEL%"

echo.
if "%RC%"=="0" (
  rem Defteri repoya yayinla: 21 Agustos'tan beri 30 forward isleminin 6'si
  rem YALNIZ MT5'te vardi (bulut UK100/FRA40/US2000'i kaciriyor), yani tek
  rem diskte duruyordu. Forward defteri yeniden URETILEMEZ.
  "%PY%" -m intraday.forward_ea.defter_yayinla
  set "PUBLISH_RC=!ERRORLEVEL!"
  if "!PUBLISH_RC!"=="0" (
    echo  [TAMAM] Defter guncellendi. MT5'i simdi kapatabilirsin.
  ) else (
    echo  [HATA] Defter yayinlanamadi. MT5'i kapatmadan yukaridaki mesaja bak.
  )
) else (
  echo  [HATA] Cikis kodu %RC%. Yukaridaki mesaja bak.
)
echo.
pause
if defined PUBLISH_RC exit /b !PUBLISH_RC!
exit /b %RC%
