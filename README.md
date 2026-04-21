# AutoVideo Generator

Автоматическая система генерации видео из текстовой идеи.

## Возможности

- 📝 **Ввод**: Текстовая идея
- 🤖 **LLM**: Qwen2-VL (локально через Ollama) для генерации сценария
- 🖼️ **Изображения**: Stable Diffusion XL (локально или API)
- 🎬 **Видео**: LTX 2.3 / базовый аниматор
- 📱 **Форматы**: Instagram Reels, Stories, Square, Portrait

## Быстрый старт

### 1. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 2. Установка Ollama (для LLM)

```bash
# Скачайте с https://ollama.com
ollama serve  # запустите в фоне

# Скачайте модель Qwen3 (доступные: 4b, 8b, 14b, 32b)
ollama pull qwen3:8b
# или для 4B версии: ollama pull qwen3:4b
```

### 3. (Опционально) Stable Diffusion XL

Для локальной генерации изображений:
```bash
pip install torch diffusers transformers accelerate
```

### 4. Запуск

```bash
# Базовая команда
python main.py "Путешествие через космос к новым планетам"

# С указанием количества сцен
python main.py "Закат над океаном" --scenes 6

# Instagram Reels формат (по умолчанию)
python main.py "Твой текст" --format reels
```

## Использование

```
usage: main.py [-h] [-i IDEA] [-s SCENES] [-o OUTPUT] [-f {reels,stories,feed_square,feed_portrait}] [-v] [idea]

Позиционные аргументы:
  idea                 Текстовая идея для видео

Опции:
  -i, --idea          Текстовая идея
  -s, --scenes        Количество сцен (по умолчанию: 4)
  -o, --output        Директория для вывода
  -f, --format        Формат видео: reels, stories, feed_square, feed_portrait
  -v, --verbose       Подробный вывод
```

## Конфигурация

Настройки в `config.py`:

- `QWEN_MODEL_SIZE`: Размер модели ("8b", "7b", "4b")
- `USE_LOCAL_SDXL`: Использовать локальный SDXL
- `USE_LOCAL_LTX`: Использовать локальный генератор видео
- Форматы Instagram: reels, stories, feed_square, feed_portrait

## Структура проекта

```
/workspace/project/
├── main.py                 # Точка входа
├── config.py               # Конфигурация
├── pipeline/
│   ├── script_generator.py   # Генерация сценария (Qwen2)
│   ├── image_generator.py    # Генерация изображений (SDXL)
│   ├── video_generator.py    # Генерация видео (LTX)
│   └── video_concatenator.py # Склейка видео
├── output/                 # Результаты
└── requirements.txt        # Зависимости
```

## Примеры

```bash
# Instagram Reels (9:16, до 90 сек)
python main.py "Утро в горах" --format reels

# Instagram Stories (9:16, до 15 сек)  
python main.py "Важный момент" --format stories --scenes 3

# Square (1:1)
python main.py "Квадратное видео" --format feed_square
```

## Требования

- Python 3.8+
- FFmpeg (для склейки видео)
- Ollama (для LLM, опционально)
- GPU с 8GB+ VRAM (для локальных моделей)

## Интерфейсы

### Web UI
```bash
pip install flask
cd webui
python app.py
# Откройте http://localhost:5000
```

### Telegram Bot
```bash
pip install python-telegram-bot
export TELEGRAM_BOT_TOKEN="ваш_токен"
python telegram_bot/bot.py
```