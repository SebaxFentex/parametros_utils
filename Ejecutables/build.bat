@echo off
setlocal
cd /d "%~dp0.."
if errorlevel 1 (
    pause
    exit /b 1
)
uv build
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" (
    echo ERROR: la construccion fallo.
    pause
    exit /b %EXIT_CODE%
)
echo.
echo Artefactos generados en dist:
dir /b dist
pause
exit /b %EXIT_CODE%
