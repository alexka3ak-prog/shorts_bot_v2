# Полная установка AutoVideo + ComfyUI с нуля

## ЧАСТЬ 1: Установка ComfyUI

### 1.1 Скачивание ComfyUI
```powershell
# Создайте папку D:\ComfyUI
New-Item -ItemType Directory -Path D:\ComfyUI -Force

# Скачайте ComfyUI (через Git или ZIP)
cd D:\
git clone https://github.com/comfyanonymous/ComfyUI.git
# Или скачайте: https://github.com/comfyanonymous/ComfyUI/releases
```

### 1.2 Установка Python зависимостей
```powershell
cd D:\ComfyUI

# Создайте виртуальное окружение
python -m venv venv

# Активируйте
.\venv\Scripts\activate

# Обновите pip
python -m pip install --upgrade pip

# Установите зависимости
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install xformers
pip install -r requirements.txt
```

### 1.3 Запуск ComfyUI
```powershell
cd D:\ComfyUI
.\venv\Scripts\activate
python main.py --listen 127.0.0.1 --port 8188
```

---

## ЧАСТЬ 2: Установка нод (Custom Nodes)

### 2.1 Через ComfyUI Manager
После запуска ComfyUI:
1. Откройте http://127.0.0.1:8188
2. Нажмите **Manager** (кнопка внизу)
3. Нажмите **Install Custom Nodes**
4. Найдите и установите:
   - `ComfyUI-LTX` или `ltx-video`
   - `ComfyUI-Wan` или `wan-video`
   - `ComfyUI-Manager` (если нет)

### 2.2 Ручная установка (если не работает менеджер)

#### Для LTX Video:
```powershell
# Создайте папку для нод
New-Item -ItemType Directory -Path D:\ComfyUI\custom_nodes\comfyui-ltx -Force
cd D:\ComfyUI\custom_nodes\comfyui-ltx

# Скачайте ноды
git clone https://github.com/Lightricks/ComfyUI-LTX-Video.git .
# или
git clone https://github.com/kijai/ComfyUI-ltx.git .
```

#### Для Wan Video:
```powershell
New-Item -ItemType Directory -Path D:\ComfyUI\custom_nodes\comfyui-wan -Force
cd D:\ComfyUI\custom_nodes\comfyui-wan

git clone https://github.com/Wan-Video/ComfyUI.git .
# или ноды от other
```

### 2.3 Установка дополнительных библиотек
```powershell
cd D:\ComfyUI
.\venv\Scripts\activate

# Стандартные библиотеки
pip install scipy numpy opencv-python

# Для видео
pip install opencv-python

# Для продвинутых нод
pip install -r custom_nodes/REQUIREMENTS.txt
```

---

## ЧАСТЬ 3: Скачивание моделей

### 3.1 Создайте папки
```powershell
New-Item -ItemType Directory -Path D:\Models\ComfyUI\models\checkpoints -Force -Recurse
New-Item -ItemType Directory -Path D:\Models\ComfyUI\models\vae -Force -Recurse
New-Item -ItemType Directory -Path D:\Models\ComfyUI\models\clip -Force -Recurse
```

### 3.2 Скачивание моделей (ссылки нужно найти):

#### LTX Video модели:
- `ltx_video.safetensors` (~2-4GB)
- Искать: 
  - https://huggingface.co/Lightricks/LTX-Video
  - https://civitai.com (искать "LTX Video")

#### Wan модели:
- `wan.safetensors`
- Искать:
  - https://huggingface.co/Wan-Video
  - https://civitai.com (искать "Wan")

#### VAE (обязательно!):
- `vae.safetensors` - для LTX

### 3.3 Куда положить:
```
D:\Models\ComfyUI\models\checkpoints\  →  .safetensors файлы
D:\Models\ComfyUI\models\vae\        →  .vae файлы
D:\Models\ComfyUI\models\clip\        →  .clip файлы
```

---

## ЧАСТЬ 4: Настройка AutoVideo

### 4.1 Клонирование AutoVideo
```powershell
cd D:\
git clone https://github.com/alexka3ak-prog/shorts_bot_v2.git AutoVideo
cd AutoVideo
```

### 4.2 Настройка config.py
Откройте `config.py` и измените:
```python
# ComfyUI настройки
COMFYUI_HOST = "127.0.0.1"
COMFYUI_PORT = 8188
COMFYUI_CHECKPOINT_PATH = r"D:\Models\ComfyUI\models\checkpoints"

# Модель по умолчанию
DEFAULT_VIDEO_MODEL = "ltx"  # или "wan"
```

### 4.3 Запуск
```powershell
cd D:\AutoVideo
python main.py "ваша идея" --model ltx
```

---

## ЧАСТЬ 5: Запуск

### 5.1 Окно 1: ComfyUI
```powershell
cd D:\ComfyUI
.\venv\Scripts\activate
python main.py --listen 127.0.0.1 --port 8188
```

### 5.2 Окно 2: AutoVideo
```powershell
cd D:\AutoVideo
python webui\app.py
# или
python main.py "Кошка летит на ракете"
```

---

## ЧАСТЬ 6: Если что-то не работает

### Ошибка: "torch not found"
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

### Ошибка: "No module named xformers"
```bash
pip install xformers --index-url https://download.pytorch.org/whl/cu121
```

### Ошибка: "Out of memory"
```bash
# Запустите на CPU
python main.py --cpu --listen 127.0.0.1 --port 8188
```

### Ошибка: "Model not found"
- Проверьте путь: `D:\Models\ComfyUI\models\checkpoints`
- Проверьте название файла

---

## Быстрая проверка работы

### Проверка ComfyUI:
```bash
curl http://127.0.0.1:8188/system_stats
```

### Проверка модели:
1. Откройте http://127.0.0.1:8188
2. Нажмите ** Manager **
3. Нажмите ** Check Custom Nodes **
4. Должно показывать установленные ноды

---

## Ссылки для скачивания моделей

### HuggingFace:
- https://huggingface.co/Lightricks/LTX-Video
- https://huggingface.co/Wan-Video

### CivitAI:
- https://civitai.com (регистрация бесплатна)
- Искать: "LTX Video", "Wan Video"

### Если нет ссылок - напишите, помогу найти!