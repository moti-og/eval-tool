@echo off
echo ========================================
echo   Eval Tool - Local Development
echo ========================================
echo.

REM Check if vercel is installed
where vercel >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Vercel CLI not found!
    echo.
    echo Installing Vercel CLI...
    npm i -g vercel
    echo.
)

echo Starting at http://localhost:8069
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

vercel dev --listen 8069

pause

