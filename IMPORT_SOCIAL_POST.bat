@echo off
chcp 65001 >nul
title Import Social Post (FB / Twitter) - santoshsikarwar.in
echo ========================================================
echo   Santosh Sikarwar Website - Social Media Importer
echo ========================================================
echo.
echo Paste a Twitter/X or Facebook post link below.
echo The script will automatically:
echo   1. Extract the Hindi/English text and photos
echo   2. Download photos to the website images folder
echo   3. Create a clean article with title, slug, and category
echo   4. Pre-render the static HTML article
echo   5. Commit and push live to santoshsikarwar.in
echo.

set /p POST_URL="Paste post URL (X / Twitter / Facebook): "

if "%POST_URL%"=="" (
    echo No URL entered. Exiting...
    pause
    exit /b
)

echo.
echo Importing post...
cd /d "%~dp0santosh-sikarwar-website" 2>nul || cd /d "%~dp0"
python social_importer.py --url "%POST_URL%"

echo.
pause
