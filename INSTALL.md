# Инструкция по установке и запуску AutoVideo Generator

## Шаг 1: Копирование проекта на ПК

### Вариант А: Скачать архив (рекомендуется)
```bash
# На этой машине создадим архив
cd /workspace/project
zip -r autovideo.zip . -x "*.git*"
```

### Вариант Б: Git clone (если есть git)
```bash
# Скопируйте все файлы проекта на ПК любым способом
```

## Шаг 2: Установка на ПК

### 2.1 Установите зависимости

```bash
# Перейдите в папку с проектом
cd autovideo

# Установите Python зависимости
pip install -r requirements.txt
```

### 2.2 Установите FFmpeg

**Windows:**
```bash
# Через winget
winget install FFmpeg

# Или скачайте с https://ffmpeg.org/download.html
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg  # Ubuntu/Debian
sudo yum install ffmpeg  # CentOS/RHEL
```

### 2.3 Установите Ollama

```bash
# Скачайте с https://ollama.com и установите

# Затем в терминале:
ollama serve

# В другом терминале скачайте модель:
ollama pull qwen3:8b
# или для 4b: ollama pull qwen3:4b
```

## Шаг 3: Запуск

### Вариант А: Web UI (рекомендуется)

```bash
# Запуск Web UI
cd autovideo
python webui/app.py
```

Откройте в браузере: **http://localhost:5000**

### Вариант Б: Telegram бот

```bash
# Установите токен бота
# Получить токен можно у @BotFather в Telegram

# Запуск бота
cd autovideo
TELEGRAM_BOT_TOKEN="ВАШ_ТОКЕН_ЗДЕСЬ" python telegram_bot/bot.py
```

### Вариант В: Командная строка

```bash
cd autovideo
python main.py "Путешествие через космос к новым планетам"
```

## Возможные проблемы

### Ollama не запускается
```bash
# Проверьте что Ollama установлен
ollama --version

# Запустите сервер
ollama serve
```

### Модель не найдена
```bash
# Скачайте модель
ollama pull qwen3:8b

# Проверьте установленные модели
ollama list
```

### Нет GPU / медленная генерация
- Без GPU генерация изображений создаёт заглушки
- Для полноценной работы нужен GPU с 8GB+ VRAM

### Видео не создаётся
```bash
# Проверьте FFmpeg
ffmpeg -version

# Если нет, установите
```

## Структура папок после установки

```
autovideo/
├── main.py
├── config.py
├── requirements.txt
├── README.md
├── pipeline/
│   ├── __init__.py
│   ├── script_generator.py
│   ├── image_generator.py
│   ├── video_generator.py
│   └── video_concatenator.py
├── webui/
│   ├── app.py
│   └── templates/
│       └── index.html
└── telegram_bot/
    └── bot.py
```

## Команды для быстрого запуска

```bash
# 1. Установка всех зависимостей
pip install -r requirements.txt

# 2. Запуск Ollama (в одном терминале)
ollama serve

# 3. Скачивание модели (в другом терминале)
ollama pull qwen3:8b

# 4. Запуск Web UI (в новом терминале)
cd autovideo
python webui/app.py
```

Откройте http://localhost:5000 и попробуйте создать видео!