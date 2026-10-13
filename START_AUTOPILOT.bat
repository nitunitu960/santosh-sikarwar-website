@echo off
chcp 65001 >nul
title Santosh Sikarwar Website - Social Autopilot
echo ========================================================
echo   Santosh Sikarwar Website - Social Media Autopilot
echo ========================================================
echo.
echo Autopilot is starting...
echo It will automatically scan the following accounts:
echo   1. Facebook: https://www.facebook.com/Santoshsikarwarbjpagra/
echo   2. Twitter:  https://x.com/ssikarwarbjp
echo   3. Twitter:  https://x.com/BJP4UP
echo.
echo Whenever a new post is detected, it will:
echo   - Expand short posts into 300+ word articles with Gemini AI
echo   - Download event photos
echo   - Pre-render static pages & update sitemaps
echo   - Commit and push live to santoshsikarwar.in
echo.
echo Checking every 2 hours (120 minutes).
echo You can leave this window open or minimized when you go out.
echo.
cd /d "%~dp0"
python social_importer.py --loop --interval 120

echo.
pause
