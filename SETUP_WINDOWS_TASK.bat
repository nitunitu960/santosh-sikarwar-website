@echo off
chcp 65001 >nul
title Setup Windows Background Autopilot for Santosh Sikarwar Website
echo ========================================================
echo   Setup Windows Background Autopilot for Santosh Sikarwar Website
echo ========================================================
echo.
echo Registering Windows Scheduled Task "SantoshSikarwarAutopilot"...
echo It will run automatically every 2 hours in the background.
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0setup_task.ps1"

if %ERRORLEVEL% equ 0 (
    echo.
    echo [SUCCESS] Windows Scheduled Task "SantoshSikarwarAutopilot" is ACTIVE!
    echo It will check for new posts every 2 hours even when you are out.
    echo.
    echo To remove this task later, run:
    echo   schtasks /delete /tn "SantoshSikarwarAutopilot" /f
) else (
    echo.
    echo [ERROR] Could not register task. Please right-click and Run as Administrator.
)

echo.
pause
