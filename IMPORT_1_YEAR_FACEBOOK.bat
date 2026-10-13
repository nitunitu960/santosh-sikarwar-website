@echo off
chcp 65001 >nul
title Import 1 Year Facebook Posts - santoshsikarwar.in
echo ========================================================
echo   Santosh Sikarwar Website - 1-Year Facebook History Importer
echo ========================================================
echo.
echo Facebook restricts public timeline browsing to only ~10 posts
echo unless you are logged into a Facebook account.
echo.
echo When you press any key:
echo   1. A Chrome browser window will open.
echo   2. If you are not logged in, please log in to your Facebook account.
echo   3. Once logged in, press Enter in this window.
echo   4. The script will automatically scroll through the past 1 year,
echo      download photos, expand text with Gemini AI, and publish to santoshsikarwar.in!
echo.
pause

cd /d "%~dp0"
python import_facebook_history.py --login --max 50

echo.
pause
