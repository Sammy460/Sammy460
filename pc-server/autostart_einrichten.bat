@echo off
REM Legt den PhoneDeck-Server in den Windows-Autostart (startet ohne Fenster).
set "TARGET=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\PhoneDeck.bat"
(
  echo @echo off
  echo start "" pythonw "%~dp0server.py"
) > "%TARGET%"
echo Autostart eingerichtet: %TARGET%
echo Entfernen: diese Datei loeschen.
pip install keyboard
pause
