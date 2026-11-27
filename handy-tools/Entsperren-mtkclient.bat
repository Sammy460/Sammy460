@echo off
chcp 65001 >nul
title PhoneDeck - Redmi 9A entsperren (mtkclient)
REM Entsperrt den Bootloader OHNE SIM und OHNE Wartezeit.
REM Nur fuer MediaTek-Geraete wie Redmi 9A (dandelion / MT6762).
REM ACHTUNG: Loescht das Handy. Im Fehlerfall Brick moeglich.

cd /d "%~dp0"
set "PY="
for %%P in (python.exe) do if not defined PY set "PY=%%~$PATH:P"
if not defined PY (
  echo Python fehlt. Erst installieren: https://www.python.org/downloads/
  echo Beim Setup Haken bei "Add python.exe to PATH" setzen.
  pause & exit /b 1
)

echo.
echo ===========================================================
echo  WARNUNG
echo  Das entsperrt den Bootloader und LOESCHT das Handy.
echo  Im Fehlerfall startet es evtl. nicht mehr (Brick).
echo  Ein Backup wird vorher auf den PC gelesen.
echo ===========================================================
echo.
choice /c JN /m "Wirklich fortfahren"
if errorlevel 2 exit /b 0

echo.
echo [1/4] mtkclient installieren (von GitHub, braucht Git) ...
where git >nul 2>&1
if errorlevel 1 (
  echo Git fehlt. Installieren: https://git-scm.com/download/win
  pause & exit /b 1
)
"%PY%" -m pip install --upgrade "git+https://github.com/bkerler/mtkclient"
"%PY%" -m mtkclient.mtk --help >nul 2>&1
if errorlevel 1 (
  echo mtkclient-Installation fehlgeschlagen. Fehler oben lesen.
  pause & exit /b 1
)

echo.
echo ===========================================================
echo  HANDY IN DEN BROM-MODUS BRINGEN:
echo  1. Handy ganz ausschalten (Kabel ab).
echo  2. Lautstaerke HOCH + RUNTER zusammen gedrueckt halten.
echo  3. Dabei USB-Kabel einstecken. Bildschirm bleibt schwarz.
echo  (UsbDk-Treiber muss installiert sein:
echo   https://github.com/daynix/UsbDk/releases )
echo ===========================================================
echo.
pause

if not exist "%~dp0backup" mkdir "%~dp0backup"
echo.
echo [2/4] Backup lesen (dauert mehrere Minuten, nicht abbrechen) ...
"%PY%" -m mtkclient.mtk rl "%~dp0backup\mtk_backup" --skip userdata
if errorlevel 1 (
  echo.
  echo Handy nicht gefunden oder Lesen fehlgeschlagen.
  echo BROM-Schritt wiederholen. Klappt es nie: Testpunkt noetig - melde dich.
  pause & exit /b 1
)
echo Backup: %~dp0backup\mtk_backup

echo.
echo [3/4] Bootloader entsperren ...
"%PY%" -m mtkclient.mtk da seccfg unlock
if errorlevel 1 (
  echo Entsperren fehlgeschlagen. Backup liegt im Ordner backup.
  pause & exit /b 1
)

echo.
echo ===========================================================
echo  [4/4] FERTIG. Kabel ab, Handy neu starten
echo  (Power lang druecken). Es warnt "Orange State" - normal.
echo  Handy neu einrichten, dann USB-Debugging anschalten.
echo  Danach: PhoneDeck-Einrichtung.exe - Schritt 4 (Root).
echo ===========================================================
pause
