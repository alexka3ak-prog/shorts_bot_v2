# Инструкция по установке на Windows

## Шаг 1: Подготовка

### 1.1 Скачайте проект
Скопируйте архив `autovideo.tar` на компьютер и распакуйте:
- Используйте 7-Zip или WinRAR для распаковки .tar
- Или просто перенесите все файлы проекта

### 1.2 Установите Python
Если нет Python, скачайте с https://www.python.org/downloads/
**Важно:** При установке поставьте галочку "Add Python to PATH"

Проверьте в командной строке:
```cmd
python --version
```

## Шаг 2: Установка необходимых программ

### 2.1 FFmpeg (обязательно!)
Скачайте FFmpeg:
1. Перейдите на https://gyan.dev/ffmpeg/builds/
2. Скачайте "ffmpeg-release-essentials.zip"
3. Распакуйте архив
4. Добавьте папку `bin` в PATH:

```cmd
# В командной строке от имени администратора:
setx /M PATH "%PATH%;C:\путь\к\ffmpeg\bin"
```

Проверьте:
```cmd
ffmpeg -version
```

### 2.2 Ollama (для LLM)
1. Скачайте с https://ollama.com/download/windows
2. Установите приложение
3. Запустите `Ollama` из меню Пуск

### 2.3 Скачайте модель Qwen3
Откройте терминал (PowerShell или cmd) и выполните:
```cmd
ollama pull qwen3:8b
```
Это скачает модель (~5GB, может занять время)

## Шаг 3: Установка зависимостей проекта

Откройте терминал в папке с проектом:
```cmd
pip install -r requirements.txt
```

## Шаг 4: Запуск

### Вариант А: Web UI (рекомендуется)

```cmd
python webui/app.py
```

Откройте в браузере: **http://localhost:5000**

### Вариант Б: Telegram бот

```cmd
set TELEGRAM_BOT_TOKEN=ВАШ_ТОКЕН
python telegram_bot\bot.py
```

### Вариант В: Командная строка

```cmd
python main.py "Путешествие через космос"
```

---

## Решение проблем

### "pip не является внутренней или внешней командой"
```cmd
# Используйте полный путь
python -m pip install -r requirements.txt
```

### "ollama не найден"
- Перезагрузите компьютер после установки Ollama
- Или откройте новое окно терминала

### "Нет модуля flask"
```cmd
pip install flask
```

### Медленная генерация
- Без видеокарты GPU генерация изображений создаёт заглушки
- Для полноценной работы желательна видеокарта NVIDIA с 8GB+ памяти

---

## Быстрые команды для PowerShell:

```powershell
# Проверить установку Python
python --version

# Проверить FFmpeg  
ffmpeg -version

# Установить зависимости
pip install -r requirements.txt

# Запустить Web UI
python webui\app.py
```

## Если что-то не работает - пишите, помогу!