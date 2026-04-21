@echo off
REM AutoVideo Generator - Windows Setup

echo ========================================
echo   AutoVideo Generator - Windows Setup
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Download from https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python found

REM Check FFmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] FFmpeg not found!
    echo Download from https://gyan.dev/ffmpeg/builds/
) else (
    echo [OK] FFmpeg found
)

echo.
echo Installing Python dependencies...
pip install -r requirements.txt
echo [OK] Dependencies installed

echo.
echo ========================================
echo Starting AutoVideo Generator
echo ========================================
echo.
echo Open in browser: http://localhost:5000
echo.
echo To stop press Ctrl+C
echo.

python webui\app.py

pause