"""
Video Generator via ComfyUI - LTX/Wan video generation

Интеграция с ComfyUI для генерации видео из изображений
Поддерживает LTX Video и Wan видео модели
"""

import os
import json
import time
import logging
import requests
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# ComfyUI настройки
COMFYUI_HOST = os.environ.get("COMFYUI_HOST", "127.0.0.1")
COMFYUI_PORT = int(os.environ.get("COMFYUI_PORT", "8188"))
COMFYUI_API_URL = f"http://{COMFYUI_HOST}:{COMFYUI_PORT}"

# Путь к чекпойнтам
DEFAULT_CHECKPOINT_PATH = os.environ.get(
    "COMFYUI_CHECKPOINT_PATH", 
    r"D:\Models\ComfyUI_Models\models\checkpoints"
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
    
    def get_models(self) -> Dict[str, List[str]]:
        """Получить список доступных моделей"""
        models = {
            "checkpoints": [],
            "video_models": []
        }
        
        if self.checkpoint_path.exists():
            for f in self.checkpoint_path.glob("*.safetensors"):
                models["checkpoints"].append(f.name)
            for f in self.checkpoint_path.glob("*.ckpt"):
                models["checkpoints"].append(f.name)
        
        return models
    
    def generate_video_ltx(self, 
                        image_path: str,
                        prompt: str,
                        output_path: str,
                        model: str = "ltx_video.safetensors",
                        num_frames: int = 81,
                        fps: int = 24,
                        seed: int = 42) -> str:
        """
        Генерировать видео через LTX Video 模型
        
        Args:
            image_path: Путь к входному изображению
            prompt: Текстовый промпт
            output_path: Путь для сохранения видео
            model: Название модели
            num_frames: Количество кадров
            fps: Кадров в секунду
            seed: Сид для генерации
            
        Returns:
            Путь к сгенерированному видео
        """
        logger.info(f"Generating video via LTX: {prompt[:50]}...")
        
        # Workflow для LTX Video
        workflow = self._create_ltx_workflow(
            image_path=image_path,
            prompt=prompt,
            output_path=output_path,
            model=model,
            num_frames=num_frames,
            fps=fps,
            seed=seed
        )
        
        return self._execute_workflow(workflow, output_path)
    
    def generate_video_wan(self,
                     image_path: str,
                     prompt: str,
                     output_path: str,
                     model: str = "wan.safetensors",
                     num_frames: int = 81,
                     fps: int = 24,
                     seed: int = 42) -> str:
        """
        Генерировать видео через Wan 模型
        
        Args:
            image_path: Путь к входному изображению
            prompt: Текстовый промпт
            output_path: Путь для сохранения видео
            model: Название модели
            num_frames: Количество кадров
            fps: Кадров в секунду
            seed: Сид для генерации
            
        Returns:
            Путь к сгенерированному видео
        """
        logger.info(f"Generating video via Wan: {prompt[:50]}...")
        
        # Workflow для Wan
        workflow = self._create_wan_workflow(
            image_path=image_path,
            prompt=prompt,
            output_path=output_path,
            model=model,
            num_frames=num_frames,
            fps=fps,
            seed=seed
        )
        
        return self._execute_workflow(workflow, output_path)
    
    def _create_ltx_workflow(self,
                        image_path: str,
                        prompt: str,
                        output_path: str,
                        model: str,
                        num_frames: int,
                        fps: int,
                        seed: int) -> dict:
        """Создать workflow для LTX Video"""
        
        # Base workflow - нужно настроить под вашу версию ComfyUI
        workflow = {
            "3": {
                "inputs": {
                    "image_path": image_path,
                    "choose_image_to_upload": "image"
                },
                "class_type": "LoadImage",
                "_meta": {"title": "Load Image"}
            },
            "4": {
                "inputs": {
                    "text": prompt,
                    "clip": ["5", 0]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode"}
            },
            "5": {
                "inputs": {
                    "model_name": model
                },
                "class_type": "UNETLoader",
                "_meta": {"title": "Load UNET"}
            },
            "6": {
                "inputs": {
                    "width": 512,
                    "height": 896,
                    "video_frames": num_frames,
                    "fps": fps,
                    "batch_size": 1,
                    "seed": seed,
                    "noise": ["7", 0],
                    "model": ["5", 0],
                    "positive": ["4", 0],
                    "negative": ["4", 0],
                    "vae": ["8", 0]
                },
                "class_type": "LTXVideoSampler",
                "_meta": {"title": "LTX Video Sampler"}
            },
            "7": {
                "inputs": {
                    "noise_type": "gaussian",
                    "seed": seed
                },
                "class_type": "Seed",
                "_meta": {"title": "Seed"}
            },
            "8": {
                "inputs": {
                    "model_name": "vae.safetensors"
                },
                "class_type": "VAELoader",
                "_meta": {"title": "Load VAE"}
            },
            "9": {
                "inputs": {
                    "filename_prefix": "ltx_video",
                    "images": ["3", 0],
                    "video_encoder": ["6", 0]
                },
                "class_type": "SaveVideo",
                "_meta": {"title": "Save Video"}
            }
        }
        
        return workflow
    
    def _create_wan_workflow(self,
                          image_path: str,
                          prompt: str,
                          output_path: str,
                          model: str,
                          num_frames: int,
                          fps: int,
                          seed: int) -> dict:
        """Создать workflow для Wan"""
        
        workflow = {
            "3": {
                "inputs": {
                    "image_path": image_path,
                    "choose_image_to_upload": "image"
                },
                "class_type": "LoadImage",
                "_meta": {"title": "Load Image"}
            },
            "4": {
                "inputs": {
                    "text": prompt,
                    "clip": ["5", 0]
                },
                "class_type": "CLIPTextEncode",
                "_meta": {"title": "CLIP Text Encode"}
            },
            "5": {
                "inputs": {
                    "model_name": model
                },
                "class_type": "UNETLoader",
                "_meta": {"title": "Load UNET"}
            },
            "6": {
                "inputs": {
                    "width": 512,
                    "height": 896,
                    "video_frames": num_frames,
                    "fps": fps,
                    "batch_size": 1,
                    "seed": seed,
                    "image": ["3", 0],
                    "model": ["5", 0],
                    "positive": ["4", 0],
                    "negative": ["4", 0]
                },
                "class_type": "WanVideoSampler",
                "_meta": {"title": "Wan Video Sampler"}
            },
            "9": {
                "inputs": {
                    "filename_prefix": "wan_video",
                    "frames": ["6", 0]
                },
                "class_type": "SaveVideo",
                "_meta": {"title": "Save Video"}
            }
        }
        
        return workflow
    
    def _execute_workflow(self, workflow: dict, output_path: str) -> str:
        """Выполнить workflow через ComfyUI API"""
        
        # Запустить промпт
        prompt_data = {"prompt": workflow}
        
        try:
            response = requests.post(
                f"{self.api_url}/prompt", 
                json=prompt_data,
                timeout=300
            )
            response.raise_for_status()
            
            result = response.json()
            prompt_id = result.get("prompt_id")
            
            if not prompt_id:
                raise ValueError(f"No prompt_id in response: {result}")
            
            # Ждать выполнения
            status = self._wait_for_completion(prompt_id)
            
            if status.get("status") == "success":
                logger.info(f"Video generated successfully")
                return output_path
            else:
                raise RuntimeError(f"Generation failed: {status}")
                
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to ComfyUI at {self.api_url}")
            logger.error("Make sure ComfyUI is running!")
            raise
    
    def _wait_for_completion(self, prompt_id: str, timeout: int = 600) -> dict:
        """Ждать выполнения промпта"""
        
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
                        return {"status": "success", "data": prompt_data}
                    elif status == "failed":
                        error_msg = prompt_data.get("error", "Unknown error")
                        return {"status": "failed", "error": error_msg}
                
                time.sleep(2)
                
            except Exception as e:
                logger.warning(f"Error checking status: {e}")
                time.sleep(2)
        
        return {"status": "timeout", "error": "Timeout after 10 minutes"}


def generate_video_via_comfyui(image_path: str,
                              prompt: str,
                              output_path: str,
                              model_type: str = "ltx",
                              **kwargs) -> str:
    """
    Удобная функция для генерации видео
    
    Args:
        image_path: Путь к изображению
        prompt: Текстовый промпт
        output_path: Путь для сохранения
        model_type: "ltx" или "wan"
        
    Returns:
        Путь к видео
    """
    generator = ComfyUIVideoGenerator()
    
    if model_type.lower() == "ltx":
        return generator.generate_video_ltx(image_path, prompt, output_path, **kwargs)
    else:
        return generator.generate_video_wan(image_path, prompt, output_path, **kwargs)


if __name__ == "__main__":
    # Тест
    logging.basicConfig(level=logging.INFO)
    
    generator = ComfyUIVideoGenerator()
    
    print(f"ComfyUI running: {generator.is_comfyui_running()}")
    print(f"Available models: {generator.get_models()}")