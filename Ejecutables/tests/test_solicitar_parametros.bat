@echo off
setlocal
cd /d "%~dp0..\.."
if errorlevel 1 (
    pause
    exit /b 1
)
uv run python tests/test_solicitar_parametros.py
set "EXIT_CODE=%ERRORLEVEL%"
echo.
echo Codigo de salida: %EXIT_CODE%
pause
exit /b %EXIT_CODE%
