"""
LTX Video Generator via ComfyUI API

Подключается к работающему ComfyUI и использует LTX 2.3.
"""
import os
import json
import logging
import uuid
import time
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from config import (
        COMFYUI_HOST,
        COMFYUI_PORT,
        COMFYUI_CHECKPOINT_PATH,
        TEMP_DIR,
        OUTPUT_DIR,
        SCENE_DURATION
    )
except ImportError:
    COMFYUI_HOST = "127.0.0.1"
    COMFYUI_PORT = 8188
    COMFYUI_CHECKPOINT_PATH = r"D:\Models\ComfyUI_Models\models\checkpoints"
    TEMP_DIR = "/workspace/project/shorts_bot_v2/output/temp"
    OUTPUT_DIR = "/workspace/project/shorts_bot_v2/output"
    SCENE_DURATION = 4

logger = logging.getLogger(__name__)


class LTXVideoGenerator:
    """Генерация видео через ComfyUI LTX 2.3"""
    
    def __init__(self, host: str = None, port: int = None):
        self.host = host or COMFYUI_HOST
        self.port = port or COMFYUI_PORT
        self.base_url = f"http://{self.host}:{self.port}"
        self.checkpoint_path = COMFYUI_CHECKPOINT_PATH
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
    
    def _queue_prompt(self, prompt: Dict) -> Optional[str]:
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
    
    def _wait_for_result(self, prompt_id: str, timeout: int = 300) -> Optional[str]:
        """Ждать результата"""
        start = time.time()
        while time.time() - start < timeout:
            try:
                resp = requests.get(f"{self.base_url}/api/prompt_history/{prompt_id}", timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("status", {}).get("completed"):
                        outputs = data.get("outputs", {})
                        for out in outputs.values():
                            if "video" in out:
                                return out["video"].get("filename")
            except:
                pass
            time.sleep(3)
        return None
    
    def generate_t2v(self, prompt: str, num_frames: int = 81,
                    output_name: str = None) -> Optional[str]:
        """Text-to-Video генерация через LTX"""
        if not self.available:
            logger.error("ComfyUI не доступен")
            return None
        
        # Базовый промпт для LTX - нужно подстроить под конкретные ноды
        prompt_data = {
            "1": {
                "inputs": {
                    "prompt": prompt,
                    "negative_prompt": "",
                    "steps": 20,
                    "CFG": 1.5,
                    "sampler": "euler",
                    "num_frames": num_frames
                },
                "class_type": "LTXVideoTextGenerate"
            },
            "2": {
                "inputs": {"video": ["1", 0]},
                "class_type": "SaveVideo"
            }
        }
        
        prompt_id = self._queue_prompt(prompt_data)
        if not prompt_id:
            return None
        
        output_file = self._wait_for_result(prompt_id, timeout=600)
        
        if output_file:
            out_path = self.output_dir / (output_name or f"ltx_{int(time.time())}.mp4")
            # Copy from ComfyUI output folder
            return str(out_path)
        
        return None
    
    def generate_i2v(self, image_path: str, prompt: str,
                     num_frames: int = 81,
                     output_name: str = None) -> Optional[str]:
        """Image-to-Video генерация"""
        if not self.available or not Path(image_path).exists():
            return None
        
        # Upload image first
        try:
            with open(image_path, "rb") as f:
                resp = requests.post(
                    f"{self.base_url}/api/upload/image",
                    files={"image": f},
                    timeout=30
                )
            if resp.status_code != 200:
                return None
            image_name = resp.json().get("name")
        except:
            return None
        
        # Build prompt
        prompt_data = {
            "3": {
                "inputs": {"image": image_name},
                "class_type": "LoadImage"
            },
            "4": {
                "inputs": {
                    "image": ["3", 0],
                    "prompt": prompt,
                    "num_frames": num_frames
                },
                "class_type": "LTXVideoGenerate"
            },
            "5": {
                "inputs": {"video": ["4", 0]},
                "class_type": "SaveVideo"
            }
        }
        
        prompt_id = self._queue_prompt(prompt_data)
        if not prompt_id:
            return None
        
        output_file = self._wait_for_result(prompt_id, timeout=600)
        
        if output_file:
            out_path = self.output_dir / (output_name or f"ltx_i2v_{int(time.time())}.mp4")
            return str(out_path)
        
        return None


def generate_video(prompt: str, output_dir: str = TEMP_DIR) -> Optional[str]:
    """Генерировать видео"""
    gen = LTXVideoGenerator()
    return gen.generate_t2v(prompt)


if __name__ == "__main__":
    gen = LTXVideoGenerator()
    print(f"ComfyUI: {gen.available}")
    
    if gen.available:
        print("Generating test video...")
        result = gen.generate_t2v("A wizard casting spell", 41)
        print(f"Result: {result}")