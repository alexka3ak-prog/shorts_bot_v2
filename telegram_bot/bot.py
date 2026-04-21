"""
Telegram Bot для AutoVideo Generator
Управление генерацией видео через Telegram
"""
import os
import sys
import json
import logging
import asyncio
from pathlib import Path
from threading import Thread
from typing import Optional

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

from main import AutoVideoPipeline
from config import INSTAGRAM_FORMATS, DEFAULT_FORMAT

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Состояние пользователей
user_states = {}


class VideoGenerationManager:
    """Менеджер генерации видео для бота"""
    
    def __init__(self):
        self.generations = {}  # user_id -> generation state
    
    def start_generation(self, user_id: int, idea: str, format_name: str, num_scenes: int) -> str:
        """Запуск генерации"""
        self.generations[user_id] = {
            "status": "starting",
            "idea": idea,
            "format": format_name,
            "scenes": num_scenes,
            "result": None,
            "error": None
        }
        
        # Запуск в отдельном потоке
        thread = Thread(target=self._run_generation, args=(user_id, idea, format_name, num_scenes))
        thread.start()
        
        return "🚀 Генерация началась!"
    
    def _run_generation(self, user_id: int, idea: str, format_name: str, num_scenes: int):
        """Выполнение генерации в фоне"""
        try:
            self.generations[user_id]["status"] = "generating"
            pipeline = AutoVideoPipeline(format_name=format_name)
            final_video = pipeline.run(idea, num_scenes)
            
            self.generations[user_id]["status"] = "completed"
            self.generations[user_id]["result"] = final_video
            
        except Exception as e:
            self.generations[user_id]["status"] = "error"
            self.generations[user_id]["error"] = str(e)
    
    def get_status(self, user_id: int) -> dict:
        """Получить статус генерации"""
        return self.generations.get(user_id, {"status": "not_started"})
    
    def get_result(self, user_id: int) -> Optional[str]:
        """Получить результат"""
        gen = self.generations.get(user_id, {})
        if gen.get("status") == "completed":
            return gen.get("result")
        return None
    
    def clear(self, user_id: int):
        """Очистить состояние"""
        if user_id in self.generations:
            del self.generations[user_id]


# Менеджер генерации
manager = VideoGenerationManager()


# Команда /start
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Приветствие"""
    await update.message.reply_text(
        "🎬 *AutoVideo Generator*\n\n"
        "Создавайте видео из текста с помощью AI\n\n"
        "Доступные команды:\n"
        "/start - Показать это сообщение\n"
        "/help - Помощь\n"
        "/generate - Начать генерацию видео\n"
        "/settings - Настройки генерации\n"
        "/status - Проверить статус",
        parse_mode="Markdown"
    )


# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Помощь"""
    await update.message.reply_text(
        "📖 *Как использовать:*\n\n"
        "1. Отправьте /generate для начала\n"
        "2. Введите описание видео\n"
        "3. Выберите формат и количество сцен\n"
        "4. Дождитесь генерации\n\n"
        "📱 *Форматы:*\n"
        "• Reels (9:16) - для Instagram\n"
        "• Stories (9:16)\n"
        "• Square (1:1)\n"
        "• Portrait (4:5)",
        parse_mode="Markdown"
    )


# Команда /generate
async def generate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать генерацию"""
    user_id = update.effective_user.id
    
    # Показать клавиатуру с форматами
    keyboard = []
    for key, fmt in INSTAGRAM_FORMATS.items():
        keyboard.append([InlineKeyboardButton(
            f"{fmt['description']} ({fmt['aspect_ratio']})", 
            callback_data=f"format_{key}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📱 *Выберите формат видео:*",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )
    
    # Сохраняем состояние
    user_states[user_id] = {"step": "format_select"}


# Обработка callback
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data.startswith("format_"):
        format_name = data.replace("format_", "")
        user_states[user_id] = {"step": "scenes", "format": format_name}
        
        # Количество сцен
        keyboard = [
            [InlineKeyboardButton("2 сцены", callback_data="scenes_2")],
            [InlineKeyboardButton("3 сцены", callback_data="scenes_3")],
            [InlineKeyboardButton("4 сцены", callback_data="scenes_4")],
            [InlineKeyboardButton("5 сцен", callback_data="scenes_5")],
            [InlineKeyboardButton("6 сцен", callback_data="scenes_6")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "🎬 *Выберите количество сцен:*",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    
    elif data.startswith("scenes_"):
        num_scenes = int(data.replace("scenes_", ""))
        user_states[user_id]["scenes"] = num_scenes
        user_states[user_id]["step"] = "idea"
        
        await query.edit_message_text(
            "✍️ *Введите описание видео:*\n\n"
            "Например: «Путешествие через космос к новым планетам»",
            parse_mode="Markdown"
        )


# Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    user_id = update.effective_user.id
    text = update.message.text
    
    # Пропускаем команды
    if text.startswith('/'):
        return
    
    # Проверяем состояние
    if user_id not in user_states:
        await update.message.reply_text(
            "Отправьте /generate чтобы начать генерацию"
        )
        return
    
    state = user_states[user_id]
    
    if state.get("step") == "idea":
        # Запускаем генерацию
        format_name = state.get("format", "reels")
        num_scenes = state.get("scenes", 4)
        
        await update.message.reply_text("🚀 Запускаю генерацию...")
        
        msg = manager.start_generation(user_id, text, format_name, num_scenes)
        await update.message.reply_text(msg)
        
        # Начинаем проверку статуса
        await check_generation_status(update, context, user_id)
        
        # Очищаем состояние
        user_states[user_id]["step"] = "waiting"


async def check_generation_status(update, context, user_id):
    """Проверка статуса генерации"""
    for i in range(30):  # Максимум 60 секунд
        await asyncio.sleep(2)
        
        status = manager.get_status(user_id)
        
        if status["status"] == "completed":
            result_video = manager.get_result(user_id)
            if result_video:
                await update.message.reply_text("✅ Видео готово! Отправляю...")
                try:
                    with open(result_video, 'rb') as video:
                        await update.message.reply_video(video)
                except Exception as e:
                    await update.message.reply_text(f"❌ Ошибка отправки: {e}")
            else:
                await update.message.reply_text("❌ Видео не найдено")
            return
            
        elif status["status"] == "error":
            await update.message.reply_text(f"❌ Ошибка: {status.get('error', 'Unknown')}")
            return
    
    await update.message.reply_text("⏰ Генерация занимает слишком долго. Проверьте статус позже.")


# Команда /status
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверить статус"""
    user_id = update.effective_user.id
    status = manager.get_status(user_id)
    
    if status["status"] == "not_started":
        await update.message.reply_text("У вас нет активной генерации. Отправьте /generate")
    else:
        await update.message.reply_text(
            f"📊 *Статус:* {status['status']}\n"
            f"Идея: {status.get('idea', 'N/A')}",
            parse_mode="Markdown"
        )


# Команда /settings
async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Настройки"""
    await update.message.reply_text(
        "⚙️ *Настройки*\n\n"
        "Текущие параметры:\n"
        f"• LLM: Qwen3:8b\n"
        f"• SDXL: local\n"
        f"• Формат по умолчанию: Instagram Reels\n\n"
        "Изменить параметры можно в config.py",
        parse_mode="Markdown"
    )


def run_bot(token: str = None):
    """Запуск бота"""
    if not token:
        # Попробовать получить из переменной окружения
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            print("❌ Укажите токен бота: TELEGRAM_BOT_TOKEN=xxx python telegram_bot/bot.py")
            return
    
    # Создаем приложение
    application = Application.builder().token(token).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("generate", generate_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("settings", settings_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Telegram бот запущен...")
    print("Откройте @your_bot_name и отправьте /start")
    
    # Запуск
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    run_bot()