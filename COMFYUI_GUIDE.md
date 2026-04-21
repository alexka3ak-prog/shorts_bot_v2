# Инструкция по настройке ComfyUI для Wan/LTX

## Шаг 1: Запуск ComfyUI

### Вариант А: Запуск через Python
```bash
# Активируйте venv с ComfyUI
cd D:\ComfyUI
python main.py --listen 127.0.0.1 --port 8188
```

### Вариант Б: Запуск через batch файл
Создайте `run_comfyui.bat`:
```batch
@echo off
cd /d D:\ComfyUI
python main.py --listen 127.0.0.1 --port 8188 --cpu
pause
```

## Шаг 2: Установка нод для Wan/LTX

### Для LTX Video:
1. Откройте ComfyUI в браузере: http://localhost:8188
2. Перейдите в Manager
3. Установите "LTX Video" ноды

### Для Wan:
1. Manager → Custom Nodes
2. Установите "Wan Video" или аналогичные ноды

## Шаг 3: Скачивание моделей

### Рекомендуемые модели (поместить в checkpoints):
- `ltx_video.safetensors` - LTX Video base
- `ltx_video_2b.safetensors` - LTX 2B параметров
- `wan.safetensors` - Wan модель
- `wan21.safetensors` - Wan 2.1

### VAE файлы (в папку vae):
- `vae.safetensors` - для LTX

## Шаг 4: Проверка

1. Запустите ComfyUI
2. Откройте http://localhost:8188
3. Загрузите Workflow (примеры есть в папке workflows)
4. Проверьте генерацию

## Шаг 5: Интеграция с AutoVideo

В файле `pipeline/comfyui_video.py` настройте:
```python
COMFYUI_HOST = "127.0.0.1"  # или IP компьютера с ComfyUI
COMFYUI_PORT = 8188
DEFAULT_CHECKPOINT_PATH = r"D:\Models\ComfyUI_Models\models\checkpoints"
```

## Шаг 6: Запуск генерации

### Через Web UI:
```
1. Запустите ComfyUI на отдельном порту (например 8189)
2. Запустите AutoVideo: python webui/app.py
3. Выберите модель "ltx" или "wan"
```

### Через командную строку:
```bash
python main.py "Кошка летит на ракете" --model ltx
```

---

## Troubleshooting

### "Cannot connect to ComfyUI"
- Проверьте что ComfyUI запущен
- Проверьте порт (8188 по умолчанию)
- Проверьте firewall

### "Model not found"
- Проверьте путь к чекпойнтам
- Проверьте название файла

### "No nodes found"
- Установите нужные ноды через Manager
- Перезапустите ComfyUI

---

## Links

- ComfyUI: https://github.com/comfyanonymous/ComfyUI
- LTX Video: https://github.com/Lightricks/LTX-Video
- Wan Video: https://github.com/Wan-Video/WanVideo

## Ваши модели

Проверьте наличие файлов в:
`D:\Models\ComfyUI_Models\models\checkpoints`

Файлы должны быть формата:
- *.safetensors
- *.ckpt
- *.pth