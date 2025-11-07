@echo off
echo ========================================
echo   LLM Eval Tool - Serverless Dev Mode
echo ========================================
echo.

REM Kill any existing processes
echo Cleaning up old processes...
taskkill /F /IM python.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
timeout /t 1 >nul
echo.

REM Set MongoDB URI with optimized connection settings
set MONGODB_URI=mongodb+srv://wordftw_user:Q0UY6fIio575I1vG@cluster0.rolg174.mongodb.net/llm_reviews?retryWrites=true^&w=majority^&appName=Cluster0^&maxPoolSize=1^&serverSelectionTimeoutMS=5000^&connectTimeoutMS=10000

REM Check if vercel is installed
where vercel >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Vercel CLI not found!
    echo.
    echo Installing Vercel CLI...
    npm i -g vercel
    echo.
)

echo Starting serverless functions locally...
echo URL: http://localhost:8069
echo.
echo NOTE: First request may be slow (~2s) while connecting to MongoDB
echo       Subsequent requests will be fast (~200ms)
echo.
echo Press Ctrl+C to stop
echo ========================================
echo.

REM Open browser after a short delay
start "" cmd /c "timeout /t 3 >nul && start http://localhost:8069"

vercel dev --listen 8069

pause

