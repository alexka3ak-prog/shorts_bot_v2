@echo off
chcp 65001 >nul
title AutoVideo Generator

echo ========================================
echo   AutoVideo Generator - Windows Setup
echo ========================================
echo.

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ОШИБКА] Python не найден!
    echo Скачайте с https://www.python.org/downloads/
    echo Не забудьте добавить Python в PATH
    pause
    exit /b 1
)

echo [OK] Python найден

REM Проверка FFmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [ПРЕДУПРЕЖДЕНИЕ] FFmpeg не найден!
    echo Видео не будут создаваться
    echo Скачайте с https://gyan.dev/ffmpeg/builds/
) else (
    echo [OK] FFmpeg найден
)

echo.
echo Установка зависимостей Python...
pip install -r requirements.txt >nul 2>&1
echo [OK] Зависимости установлены

echo.
echo ========================================
echo Запуск AutoVideo Generator
echo ========================================
echo.
echo Откройте в браузере: http://localhost:5000
echo.
echo Для остановки нажмите Ctrl+C
echo.

python webui\app.py

pause