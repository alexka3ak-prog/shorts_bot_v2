"""
Video Generator via ComfyUI - LTX 2.3 video generation

Интеграция с ComfyUI для генерации видео из изображений
Поддерживает LTX 2.3 модели
"""

import os
import json
import time
import logging
import requests
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# ComfyUI настройки
COMFYUI_HOST = os.environ.get("COMFYUI_HOST", "127.0.0.1")
COMFYUI_PORT = int(os.environ.get("COMFYUI_PORT", "8188"))
COMFYUI_API_URL = f"http://{COMFYUI_HOST}:{COMFYUI_PORT}"

# Пути к моделям
DEFAULT_CHECKPOINT_PATH = os.environ.get(
    "COMFYUI_CHECKPOINT_PATH", 
    r"D:\Models\ComfyUI_Models\models\checkpoints"
)

DEFAULT_VAE_PATH = os.environ.get(
    "COMFYUI_VAE_PATH",
    r"D:\Models\ComfyUI_Models\models\vae"
)

DEFAULT_TEXT_ENCODER_PATH = os.environ.get(
    "COMFYUI_TEXT_ENCODER_PATH",
    r"D:\Models\ComfyUI_Models\models\text_encoders"
)


class ComfyUIVideoGenerator:
    """Генератор видео через ComfyUI API"""
    
    def __init__(self, 
                checkpoint_path: str = DEFAULT_CHECKPOINT_PATH,
                comfyui_url: str = COMFYUI_API_URL):
        self.checkpoint_path = Path(checkpoint_path)
        self.comfyui_url = comfyui_url
        self.api_url = comfyui_url
        
        logger.info(f"ComfyUI Video Generator initialized")
        logger.info(f"  API: {self.api_url}")
        logger.info(f"  Checkpoints: {self.checkpoint_path}")
    
    def is_comfyui_running(self) -> bool:
        """Проверить, запущен ли ComfyUI"""
        try:
            response = requests.get(f"{self.api_url}/system_stats", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_available_models(self) -> Dict[str, List[str]]:
        """Получить список доступных моделей"""
        models = {
            "checkpoints": [],
            "vae": [],
            "clip": []
        }
        
        if self.checkpoint_path.exists():
            for f in self.checkpoint_path.glob("*ltx*.safetensors"):
                models["checkpoints"].append(f.name)
            for f in self.checkpoint_path.glob("*wan*.safetensors"):
                models["checkpoints"].append(f.name)
            for f in self.checkpoint_path.glob("*.vae.safetensors"):
                models["vae"].append(f.name)
            for f in self.checkpoint_path.glob("clip_*.safetensors"):
                models["clip"].append(f.name)
        
        return models
    
    def get_object_info(self) -> Dict[str, Any]:
        """Получить информацию о доступных нодах"""
        try:
            response = requests.get(f"{self.api_url}/api/object_info", timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Cannot get object info: {e}")
        return {}
    
    def generate_video_ltx(self, 
                        image_path: str,
                        prompt: str,
                        output_path: str,
                        model_name: str = "ltx-2.3-22b-dev-fp8.safetensors",
                        width: int = 1024,
                        height: int = 1792,
                        num_frames: int = 81,
                        fps: int = 24,
                        seed: int = 42,
                        cfg_scale: float = 0.8,
                        steps: int = 5) -> str:
        """
        Генерировать видео через LTX 2.3
        
        Args:
            image_path: Путь к входному изображению
            prompt: Текстовый промпт
            output_path: Путь для сохранения видео
            model_name: Название модели
            width: Ширина
            height: Высота
            num_frames: Количество кадров
            fps: Кадров в секунду
            seed: Сид
            cfg_scale: CFG scale
            steps: Шаги
            
        Returns:
            Путь к сгенерированному видео
        """
        logger.info(f"Generating video via LTX 2.3: {prompt[:50]}...")
        
        # Получаем информацию о нодах
        object_info = self.get_object_info()
        
        # Определяем доступные ноды
        has_ltx_sampler = "LTXVideoSampler" in object_info
        has_video_combine = "VideoCombine" in object_info
        
        if has_ltx_sampler:
            return self._generate_via_ltx_sampler(
                image_path, prompt, output_path, model_name,
                width, height, num_frames, fps, seed, cfg_scale, steps
            )
        else:
            # Пробуем альтернативный метод
            logger.warning("LTXVideoSampler not found, trying alternative")
            return self._generate_alternative(
                image_path, prompt, output_path, model_name
            )
    
    def _generate_via_ltx_sampler(self,
                                image_path: str,
                                prompt: str,
                                output_path: str,
                                model_name: str,
                                width: int,
                                height: int,
                                num_frames: int,
                                fps: int,
                                seed: int,
                                cfg_scale: float,
                                steps: int) -> str:
        """Генерировать через LTXVideoSampler"""
        
        workflow = {
            "nodes": [
                {
                    "id": 1,
                    "type": "LoadImage",
                    "widgets_values": ["image"]
                },
                {
                    "id": 2,
                    "type": "CLIPTextEncode",
                    "widgets_values": [prompt]
                },
                {
                    "id": 3,
                    "type": "CLIPTextEncode", 
                    "widgets_values": ["blurry, low quality, bad anatomy, text, watermark"]
                },
                {
                    "id": 4,
                    "type": "LTXVideoLoader",
                    "widgets_values": [model_name]
                },
                {
                    "id": 5,
                    "type": "DualCLIPLoader",
                    "widgets_values": ["clip_l.safetensors", "clip_g.safetensors"]
                },
                {
                    "id": 6,
                    "type": "VASelector", 
                    "widgets_values": ["vae.safetensors"]
                },
                {
                    "id": 7,
                    "type": "LTXVideoSampler",
                    "widgets_values": [
                        width, height, num_frames, fps, 1, seed,
                        cfg_scale, steps, "DPM++ 2M", "normal", 1
                    ]
                },
                {
                    "id": 8,
                    "type": "VideoCombine",
                    "widgets_values": ["mp4", "h264", "none", "output.mp4"]
                },
                {
                    "id": 9,
                    "type": "PreviewVideo",
                    "widgets_values": []
                }
            ],
            "links": [
                [2, 1, 0, "IMAGE", "IMAGE"],
                [4, 4, 0, "MODEL", "MODEL"],
                [5, 5, 0, "CLIP", "CLIP"],
                [6, 2, "CONDITIONING", "CONDITIONING"],
                [7, 3, "CONDITIONING", "CONDITIONING"],
                [8, 6, "VAE", "VAE"],
                [9, 7, "VIDEO", "VIDEO"]
            ]
        }
        
        return self._execute_workflow(workflow, output_path)
    
    def _generate_alternative(self,
                           image_path: str,
                           prompt: str,
                           output_path: str,
                           model_name: str) -> str:
        """Альтернативный метод генерации"""
        
        # Пробуем базовый workflow
        workflow = {
            "prompt": {
                "1": {"inputs": {"image": image_path}, "class_type": "LoadImage"},
                "2": {"inputs": {"text": prompt}, "class_type": "CLIPTextEncode"},
                "3": {
                    "inputs": {"model": model_name},
                    "class_type": "LTXVideoLoader"
                },
                "4": {
                    "inputs": {
                        "model": ["3", 0],
                        "positive": ["2", 0],
                        "image": ["1", 0]
                    },
                    "class_type": "LTXVideoSampler"
                }
            }
        }
        
        try:
            return self._execute_workflow(workflow, output_path)
        except Exception as e:
            logger.error(f"Alternative generation failed: {e}")
            raise
    
    def _execute_workflow(self, workflow: dict, output_path: str) -> str:
        """Выполнить workflow через ComfyUI API"""
        
        try:
            response = requests.post(
                f"{self.api_url}/prompt", 
                json={"prompt": workflow},
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            prompt_id = result.get("prompt_id")
            
            if not prompt_id:
                raise ValueError(f"No prompt_id: {result}")
            
            # Ждем выполнения
            status = self._wait_for_completion(prompt_id)
            
            if status.get("status") == "success":
                return output_path
            else:
                raise RuntimeError(f"Generation failed: {status}")
                
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to ComfyUI at {self.api_url}")
            raise
    
    def _wait_for_completion(self, prompt_id: str, timeout: int = 600) -> dict:
        """Ждать выполнения"""
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(
                    f"{self.api_url}/history/{prompt_id}",
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    prompt_data = data.get(prompt_id, {})
                    status = prompt_data.get("status", "")
                    
                    if status == "success":
                        return {"status": "success"}
                    elif status == "failed":
                        return {"status": "failed"}
                
                time.sleep(2)
            except Exception as e:
                logger.warning(f"Error: {e}")
                time.sleep(2)
        
        return {"status": "timeout"}


def generate_video_via_comfyui(image_path: str,
                              prompt: str,
                              output_path: str,
                              model_type: str = "ltx",
                              **kwargs) -> str:
    """Удобная функция"""
    generator = ComfyUIVideoGenerator()
    return generator.generate_video_ltx(image_path, prompt, output_path, **kwargs)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    generator = ComfyUIVideoGenerator()
    print(f"Running: {generator.is_comfyui_running()}")
    print(f"Models: {generator.get_available_models()}")