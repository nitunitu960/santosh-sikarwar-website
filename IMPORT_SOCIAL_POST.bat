@echo off
chcp 65001 >nul
title Import Social Post (FB / Twitter) - santoshsikarwar.in
echo ========================================================
echo   Santosh Sikarwar Website - Social Media Importer
echo ========================================================
echo.
echo Options:
echo   - Paste a specific Twitter/X or Facebook post URL below to import immediately.
echo   - OR press Enter without typing anything to run Autopilot on all accounts!
echo.

set "POST_URL="
set /p POST_URL="Paste post URL (or press Enter for Autopilot): "

echo.
cd /d "%~dp0"

if "%POST_URL%"=="" (
    echo Running Autopilot across all monitored accounts...
    python social_importer.py --autopilot
) else (
    echo Importing post...
    python social_importer.py --url "%POST_URL%"
)

echo.
pause
