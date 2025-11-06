@echo off
echo ========================================
echo   Eval Tool - Local Development
echo ========================================
echo.

REM Kill any existing Python/Streamlit processes
echo Stopping any existing servers...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
timeout /t 1 >nul
echo.

REM Set MongoDB URI environment variable
set MONGODB_URI=mongodb+srv://msorkin_db_user:L9nsLcR7ZYIM3iOP@cluster0.rolg174.mongodb.net/llm_reviews?retryWrites=true^&w=majority

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

REM Open browser after a short delay
start "" cmd /c "timeout /t 3 >nul && start http://localhost:8069"

vercel dev --listen 8069

pause

