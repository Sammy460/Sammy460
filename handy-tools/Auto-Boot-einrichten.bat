@echo off
chcp 65001 >nul
title PhoneDeck - Auto-Boot einrichten
REM Redmi 9A: Handy faehrt automatisch hoch, sobald USB-Strom kommt.
REM Voraussetzung: Root mit Magisk (siehe README, Schritte 2-4).

cd /d "%~dp0"
set "HT=%~dp0"
if exist "%~dp0handy-tools\autoboot_einrichten.sh" set "HT=%~dp0handy-tools\"
set "ADB=%~dp0tools\platform-tools\adb.exe"

if not exist "%ADB%" (
  echo Lade ADB herunter ...
  powershell -NoProfile -Command "Invoke-WebRequest https://dl.google.com/android/repository/platform-tools-latest-windows.zip -OutFile '%TEMP%\pt.zip'; Expand-Archive '%TEMP%\pt.zip' '%~dp0tools' -Force"
)
if not exist "%ADB%" ( echo ADB konnte nicht geladen werden. & pause & exit /b 1 )

echo.
echo Suche Handy ...
"%ADB%" start-server >nul 2>&1
set "STATE="
for /f %%s in ('"%ADB%" get-state 2^>nul') do set "STATE=%%s"
if not "%STATE%"=="device" (
  echo Kein Handy gefunden.
  echo  - USB-Kabel pruefen
  echo  - Am Handy "USB-Debugging zulassen" mit "Immer erlauben" bestaetigen
  pause & exit /b 1
)

echo Pruefe Root - am Handy ggf. Magisk-Anfrage fuer "Shell" ERLAUBEN ...
"%ADB%" shell "su -c id" | find "uid=0" >nul
if errorlevel 1 (
  echo.
  echo KEIN ROOT. Ohne Root kann das Redmi 9A nicht automatisch booten.
  echo Erst Bootloader entsperren und Magisk installieren ^(README^).
  pause & exit /b 1
)

echo.
echo Das Boot-Image wird geaendert. Vorher wird ein Backup gesichert.
choice /c JN /m "Fortfahren"
if errorlevel 2 exit /b 0

"%ADB%" shell mkdir -p /sdcard/phonedeck
"%ADB%" push "%HT%autoboot_einrichten.sh" /sdcard/phonedeck/ || goto fail
"%ADB%" push "%HT%autoboot_rueckgaengig.sh" /sdcard/phonedeck/ || goto fail
"%ADB%" push "%HT%autoboot.rc" /sdcard/phonedeck/ || goto fail

"%ADB%" shell "su -c 'sh /sdcard/phonedeck/autoboot_einrichten.sh'" > "%TEMP%\autoboot.log" 2>&1
type "%TEMP%\autoboot.log"

if not exist "%~dp0backup" mkdir "%~dp0backup"
"%ADB%" pull /sdcard/phonedeck/boot_backup.img "%~dp0backup\boot_backup.img"

find "Fertig" "%TEMP%\autoboot.log" >nul || goto fail

echo.
echo ===========================================================
echo  FERTIG. Test: Handy ausschalten, USB-Kabel einstecken.
echo  Es sollte von selbst hochfahren.
echo  Backup: %~dp0backup\boot_backup.img
echo  Notfall ^(Handy startet nicht^): Fastboot-Modus, dann
echo    tools\platform-tools\fastboot flash boot backup\boot_backup.img
echo ===========================================================
pause
exit /b 0

:fail
echo.
echo FEHLER - siehe Ausgabe oben. Ohne "Fertig" wurde nichts geflasht.
pause
exit /b 1
