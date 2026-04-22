"""
LTX Video Generator via ComfyUI API

Подключается к работающему ComfyUI и использует LTX 2.3.
Workflow: LoadImage -> LTXVideoI2V -> SaveVideo
"""
import os
import json
import logging
import uuid
import time
import requests
import shutil
from pathlib import Path
from typing import Optional

try:
    from config import (
        COMFYUI_HOST,
        COMFYUI_PORT,
        TEMP_DIR,
        OUTPUT_DIR,
    )
except ImportError:
    COMFYUI_HOST = "127.0.0.1"
    COMFYUI_PORT = 8188
    TEMP_DIR = "/workspace/project/shorts_bot_v2/output/temp"
    OUTPUT_DIR = "/workspace/project/shorts_bot_v2/output"

logger = logging.getLogger(__name__)


class LTXVideoGenerator:
    """Генерация видео через ComfyUI LTX 2.3"""
    
    def __init__(self, host: str = None, port: int = None):
        self.host = host or COMFYUI_HOST
        self.port = port or COMFYUI_PORT
        self.base_url = f"http://{self.host}:{self.port}"
        self.output_dir = Path(TEMP_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.available = self._check_connection()
        logger.info(f"LTXVideoGenerator: ComfyUI={'доступен' if self.available else 'недоступен'}")
    
    def _check_connection(self) -> bool:
        try:
            resp = requests.get(f"{self.base_url}/api/object_info", timeout=5)
            return resp.status_code == 200
        except:
            return False
    
    def _queue_prompt(self, prompt: dict) -> Optional[str]:
        """Отправить промпт в ComfyUI"""
        try:
            prompt_id = str(uuid.uuid4())
            resp = requests.post(
                f"{self.base_url}/api/prompt",
                json={"prompt": prompt, "prompt_id": prompt_id},
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json().get("prompt_id")
        except Exception as e:
            logger.error(f"Failed to queue: {e}")
        return None
    
    def _wait_for_result(self, prompt_id: str, timeout: int = 600) -> Optional[str]:
        """Ждать результата"""
        start = time.time()
        
        while time.time() - start < timeout:
            try:
                resp = requests.get(f"{self.base_url}/api/prompt_history/{prompt_id}", timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    status = data.get("status", {})
                    
                    if status.get("completed"):
                        outputs = data.get("outputs", {})
                        for node_id, out in outputs.items():
                            if "video" in out:
                                fname = out["video"].get("filename")
                                logger.info(f"Video generated: {fname}")
                                return fname
                    
                    if status.get("error"):
                        logger.error(f"Error: {status['error']}")
                        return None
                        
            except Exception as e:
                logger.debug(f"Waiting... {e}")
            
            time.sleep(3)
        
        logger.warning("Timeout")
        return None
    
    def _upload_image(self, image_path: str) -> Optional[str]:
        """Загрузить изображение"""
        if not Path(image_path).exists():
            return None
        
        try:
            with open(image_path, "rb") as f:
                files = {"image": (Path(image_path).name, f, "image/png")}
                resp = requests.post(f"{self.base_url}/api/upload/image", files=files, timeout=30)
            if resp.status_code == 200:
                return resp.json().get("name")
        except Exception as e:
            logger.error(f"Upload error: {e}")
        return None
    
    def generate_i2v(self, image_path: str, prompt: str,
                     num_frames: int = 81,
                     width: int = 512,
                     height: int = 768,
                     fps: int = 24,
                     output_name: str = None) -> Optional[str]:
        """Image-to-Video через LTX 2.3
        
        Workflow из video_ltx2_3_i2v.json:
        - Node 269: LoadImage
        - Node 320: LTXVideoI2V (UUID type)
        - Node 75: SaveVideo
        """
        if not self.available:
            logger.error("ComfyUI недоступен")
            return None
        
        # Upload image
        image_name = self._upload_image(image_path)
        if not image_name:
            logger.error("Не удалось загрузить изображение")
            return None
        
        logger.info(f"Загружено: {image_name}")
        
        # Build workflow - точно по video_ltx2_3_i2v.json
        prompt_data = {
            # Node 269: LoadImage
            "269": {
                "inputs": {
                    "image_path": image_name,
                    "choose_image_to_upload": "uploaded_image"
                },
                "class_type": "LoadImage"
            },
            # Node 320: LTX Video I2V (UUID node)
            "320": {
                "inputs": {
                    "input": ["269", 0],  # IMAGE from LoadImage
                    "value_2": width,
                    "value_3": height,
                    "value_4": num_frames,
                    "lora_name": "ltx-2.3-22b-distilled-lora-384.safetensors",
                    "model_name": "",
                    "value_5": fps
                },
                "class_type": "2454ad83-157c-40dd-9f19-5daaf4041ce0"
            },
            # Node 75: SaveVideo
            "75": {
                "inputs": {
                    "video": ["320", 0]
                },
                "class_type": "SaveVideo",
                "widgets_values": ["video/LTX_2.3_i2v", "auto", "auto"]
            }
        }
        
        # Queue
        prompt_id = self._queue_prompt(prompt_data)
        if not prompt_id:
            logger.error("Не удалось поставить в очередь")
            return None
        
        logger.info(f"В очереди: {prompt_id}")
        
        # Wait
        output_file = self._wait_for_result(prompt_id, timeout=600)
        
        if output_file:
            # ComfyUI сохраняет в C:\ai-project\ComfyUI\output\
            source = Path("C:/ai-project/ComfyUI/output") / output_file
            
            if source.exists():
                out_path = self.output_dir / (output_name or f"ltx_{int(time.time())}.mp4")
                shutil.copy(source, out_path)
                logger.info(f"Сохранено: {out_path}")
                return str(out_path)
            else:
                logger.warning(f"Файл не найден: {source}")
                return str(source)
        
        return None


def generate_video(prompt: str = None, output_dir: str = TEMP_DIR) -> Optional[str]:
    """Генерировать видео"""
    gen = LTXVideoGenerator()
    return gen.generate_t2v(prompt) if prompt else None


if __name__ == "__main__":
    gen = LTXVideoGenerator()
    print(f"ComfyUI: {gen.available}")