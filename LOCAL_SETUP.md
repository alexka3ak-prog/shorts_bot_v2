# shorts_bot_v2 - Локальная работа

## ✅ Установлено:
- `C:\ai-project\ffmpeg` - FFmpeg
- `C:\ai-project\piper` - TTS
- `C:\ai-project\ComfyUI` - видео генерация
- `D:\ollama` - LLM
- `D:\Models\ComfyUI_Models` - модели

## Пути в config.py:
```python
FFMPEG_PATH = r"C:\ai-project\ffmpeg\bin\ffmpeg.exe"
PIPER_PATH = r"C:\ai-project\piper\piper.exe"
COMFYUI_MODELS_PATH = r"D:\Models\ComfyUI_Models\models"
```

## Запуск:

```cmd
# Окно 1: Ollama
ollama serve

# Окно 2: ComfyUI  
cd C:\ai-project\ComfyUI
python main.py

# Окно 3: shorts_bot_v2
cd C:\ai-project\shorts_bot_v2
python main.py "Диалог мага и ученика"
```

## Опции:
```cmd
python main.py "Идея" --format reels    # 9:16
python main.py "Идея" --format youtube  # 16:9
python main.py "Идея" --scenes 4
```
