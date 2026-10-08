@echo off
REM Mikoshi Gear — Catalog Studio (Windows launcher)
REM Opens the local admin for mikoshigear.ca in your browser.
setlocal
echo Starting Mikoshi Catalog Studio…
echo.
python "%~dp0server.py"
if errorlevel 1 (
  echo.
  echo The server exited with an error. Make sure Python 3 is installed.
  pause
)
endlocal
