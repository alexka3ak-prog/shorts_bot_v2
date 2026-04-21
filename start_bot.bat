@echo off
chcp 65001 >nul
title AutoVideo Generator - Telegram Bot

REM Установка токена
if "%TELEGRAM_BOT_TOKEN%"=="" (
    echo Введите токен бота:
    set /p TOKEN=
    set TELEGRAM_BOT_TOKEN=%TOKEN%
)

echo Запуск Telegram бота...
python telegram_bot\bot.py

pause