"""
Configuration settings for AutoVideo Generator

Локальный запуск:
1. LLM: Установите Ollama + qwen2:8b
2. SDXL: Используйте локальный Diffusers или API
3. LTX: Используйте локальный генератор или API
"""
import os

# ============================================
# LLM - Qwen3 via Ollama (локально)
# ============================================
# Доступные модели в Ollama: qwen3:0.6b, qwen3:1.7b, qwen3:4b, qwen3:8b, qwen3:14b, qwen3:32b, qwen3:235b
# qwen3:8b = 5.2GB, qwen3:4b = 2.5GB
QWEN_MODEL_SIZE = os.getenv("QWEN_MODEL_SIZE", "8b").lower()  # "8b", "4b", "14b", "32b"
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# ============================================
# Stable Diffusion XL (локально или API)
# ============================================
# Вариант 1: Локальный запуск через Diffusers (рекомендуется)
USE_LOCAL_SDXL = os.getenv("USE_LOCAL_SDXL", "true").lower() == "true"

# Вариант 2: Stability AI API (если нет GPU)
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY", "")
STABILITY_API_URL = "https://api.stability.ai/v2beta/image-generation/text-to-image"

# ============================================
# LTX/Wan Video Generation (локально через ComfyUI)
# ============================================
# Вариант 1: Локальный генератор (базовый)
USE_LOCAL_LTX = os.getenv("USE_LOCAL_LTX", "true").lower() == "true"

# Вариант 2: LTX API
LTX_API_KEY = os.getenv("LTX_API_KEY", "")
LTX_API_URL = os.getenv("LTX_API_URL", "https://api.ltx.latent.space/v1/video/generate")

# Вариант 3: ComfyUI (LTX 2.3) - РЕКОМЕНДУЕТСЯ
USE_COMFYUI = os.getenv("USE_COMFYUI", "true").lower() == "true"
COMFYUI_HOST = os.getenv("COMFYUI_HOST", "127.0.0.1")
COMFYUI_PORT = int(os.getenv("COMFYUI_PORT", "8188"))
COMFYUI_CHECKPOINT_PATH = os.getenv(
    "COMFYUI_CHECKPOINT_PATH", 
    r"D:\Models\ComfyUI_Models\models\checkpoints"
)

# LTX 2.3 model names
LTX_MODEL_NAME = "ltx-2.3-22b-dev-fp8.safetensors"  # или "ltx-2.3-22b-distilled-fp8.safetensors"
LTX_VAE_NAME = "LTX23_video_vae_bf16.safetensors"
LTX_CLIP_L = "clip_l.safetensors"
LTX_CLIP_G = "clip_g.safetensors"

# Default модель для видео: "ltx" или "wan"
DEFAULT_VIDEO_MODEL = os.getenv("DEFAULT_VIDEO_MODEL", "ltx")

# Video Settings
IMAGE_WIDTH = 1024
IMAGE_HEIGHT = 1024
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