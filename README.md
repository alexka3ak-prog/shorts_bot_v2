# AutoVideo Generator - shorts_bot_v2

Генерация видео из текста с персонажами и диалогами.

## Возможности

- Текст → видео с персонажами
- Диалоги с TTS озвучкой
- Burned-in субтитры
- Lip-sync (опционально)

## Быстрый старт

```bash
pip install -r requirements.txt
python main.py "Разговор мудреца и путешественника"
```

## API ключи

ElevenLabs TTS (рекомендуется):
```cmd
set ELEVENLABS_API_KEY=ваш_ключ
```

или OpenAI TTS:
```cmd  
set OPENAI_TTS_API_KEY=ваш_ключ
```

## Требования

- FFmpeg (для видео)
- Ollama + Qwen3 (для сценария, опционально)
- API ключи TTS (для озвучки)

## Форматы

```bash
python main.py "Идея" --format reels    # 9:16
python main.py "Идея" --format youtube # 16:9
```

## Пример

```bash
python main.py "Волшебник объясняет заклинание ученику в башне"
```
