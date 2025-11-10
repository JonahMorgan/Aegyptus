@echo off
echo ================================================================================
echo Egyptian Lemma Network Visualizer Launcher
echo ================================================================================
echo.
echo Starting web server...
echo.

cd /d "%~dp0"
start http://localhost:8000
python server.py

pause
