"""
Configuration settings for AutoVideo Generator - LOCAL VERSION

Локальный запуск на ПК пользователя:
1. Ollama + Qwen3:8b (сценарий)
2. Diffusers/ComfyUI SDXL (изображения)  
3. ComfyUI LTX 2.3 (видео)
"""
import os

# ============================================
# LLM - Qwen3 через Ollama (локально)
# ============================================
QWEN_MODEL_SIZE = os.getenv("QWEN_MODEL_SIZE", "8b")  # "8b", "4b", "14b"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# ============================================
# IMAGE - Stable Diffusion XL (локально)
# ============================================
USE_LOCAL_SDXL = os.getenv("USE_LOCAL_SDXL", "true").lower() == "true"
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY", "")  # Не используем - только локально

# ============================================
# VIDEO - LTX 2.3 через ComfyUI (локально)
# ============================================
USE_COMFYUI = os.getenv("USE_COMFYUI", "true").lower() == "true"
COMFYUI_HOST = os.getenv("COMFYUI_HOST", "127.0.0.1")
COMFYUI_PORT = int(os.getenv("COMFYUI_PORT", "8188"))

# Путь к моделям ComfyUI
COMFYUI_MODELS_PATH = os.getenv(
    "COMFYUI_MODELS_PATH",
    r"D:\Models\ComfyUI_Models\models"
)

# LTX модели (файлы уже есть в models/checkpoints)
LTX_MODEL_NAME = "ltx-2.3-22b-dev-fp8.safetensors"
LTX_VAE_NAME = "LTX23_video_vae_bf16.safetensors"

# ============================================
# TTS - ЛОКАЛЬНЫЙ Coqui/Piper (без облака!)
# ============================================
# Не используем облачные API - только локальный TTS
USE_LOCAL_TTS = os.getenv("USE_LOCAL_TTS", "true").lower() == "true"

# Путь к Piper (установлен локально)
PIPER_PATH = os.getenv(
    "PIPER_PATH",
    r"C:\ai-project\piper\piper.exe"
)

# Модель Piper
PIPER_MODEL = os.getenv(
    "PIPER_MODEL",
    r"C:\ai-project\piper\en_US-lessac-piper.onnx"
)
LTX_CLIP_L = "clip_l.safetensors"
LTX_CLIP_G = "clip_g.safetensors"
DEFAULT_VIDEO_MODEL = os.getenv("DEFAULT_VIDEO_MODEL", "ltx")

# Для обратной совместимости (устаревшие, но нужны для импорта)
STABILITY_API_URL = ""
STABILITY_API_KEY = ""
LTX_API_KEY = ""
LTX_API_URL = ""
ELEVENLABS_API_KEY = ""
OPENAI_TTS_API_KEY = ""
USE_LOCAL_LTX = True  # Используем локальный генератор
USE_LOCAL_SDXL = True
USE_COMFYUI = True
USE_LOCAL_TTS = True

# Video Settings
IMAGE_WIDTH = 1024
IMAGE_HEIGHT = 1024

# FFmpeg path (installed locally)
FFMPEG_PATH = os.getenv(
    "FFMPEG_PATH",
    r"C:\ai-project\ffmpeg\bin\ffmpeg.exe"
)

# Scene Settings
SCENE_DURATION = 4  # seconds per scene
TRANSITION_DURATION = 0.5  # seconds

# Instagram Format Presets
INSTAGRAM_FORMATS = {
    "reels": {
        "width": 1080,
        "height": 1920,  # 9:16
        "aspect_ratio": "9:16",
        "max_duration": 90,
        "description": "Instagram Reels (vertical video)"
    },
    "stories": {
        "width": 1080,
        "height": 1920,  # 9:16
        "aspect_ratio": "9:16",
        "max_duration": 15,
        "description": "Instagram Stories"
    },
    "feed_square": {
        "width": 1080,
        "height": 1080,  # 1:1
        "aspect_ratio": "1:1",
        "max_duration": 60,
        "description": "Instagram Feed (square)"
    },
    "feed_portrait": {
        "width": 1080,
        "height": 1350,  # 4:5
        "aspect_ratio": "4:5",
        "max_duration": 60,
        "description": "Instagram Feed (portrait)"
    },
    "youtube": {
        "width": 1920,
        "height": 1080,  # 16:9
        "aspect_ratio": "16:9",
        "max_duration": 600,
        "description": "YouTube / TikTok Landscape"
    },
    "youtube_short": {
        "width": 1080,
        "height": 1920,  # 9:16
        "aspect_ratio": "9:16",
        "max_duration": 180,
        "description": "YouTube Shorts"
    },
    "default": {
        "width": 1920,
        "height": 1080,  # 16:9 - DEFAULT
        "aspect_ratio": "16:9",
        "max_duration": 60,
        "description": "Default 16:9 landscape"
    }
}

# Default format
DEFAULT_FORMAT = "youtube"  # 16:9 landscape

# Output Settings
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
TEMP_DIR = os.path.join(OUTPUT_DIR, "temp")
FINAL_VIDEO_NAME = "final_video.mp4"

# FFmpeg Settings
FFMPEG_CODEC = "libx264"
FFMPEG_PRESET = "medium"
FFMPEG_CRF = 23