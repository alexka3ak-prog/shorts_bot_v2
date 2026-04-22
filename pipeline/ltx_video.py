"""
LTX Video Generator via ComfyUI API

Поддерживает:
- T2V (Text-to-Video) с текстовым промптом
- I2V (Image-to-Video) из изображения

Workflow из video_ltx2_3_t2v.json (полная структура)
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
                        # VHS_VideoCombine saves video
                        for node_id, out in outputs.items():
                            if "video" in out or "images" in out:
                                # Try video first
                                if "video" in out:
                                    fname = out["video"].get("filename")
                                    if fname:
                                        logger.info(f"Video generated: {fname}")
                                        return fname
                                # Then images
                                if "images" in out:
                                    for img in out.get("images", []):
                                        if img.get("filename"):
                                            logger.info(f"Images generated: {img['filename']}")
                                            return img["filename"]
                    
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
    
    def generate_t2v(self, prompt: str,
                     negative_prompt: str = "blurry, low quality, still frame, watermark",
                     width: int = 768,
                     height: int = 512,
                     num_frames: int = 105,
                     fps: int = 25,
                     steps: int = 20,
                     cfg: float = 3.0,
                     output_name: str = None) -> Optional[str]:
        """Text-to-Video через LTX 2.3
        
        Полная структура из T2V workflow:
        - CheckpointLoaderSimple
        - LTXVGemmaCLIPModelLoader  
        - CLIPTextEncode (positive + negative)
        - EmptyLTXVLatentVideo
        - MultimodalGuider + GuiderParameters
        - SamplerCustomAdvanced
        - VAEDecode + VHS_VideoCombine
        """
        if not self.available:
            logger.error("ComfyUI недоступен")
            return None
        
        logger.info(f"Generating T2V: {prompt[:50]}...")
        
        # Упрощённый T2V workflow (основные ноды)
        prompt_data = {
            # Node 1: Checkpoint
            "1": {
                "inputs": {"ckpt_name": "ltx-2.3-22b-dev-fp8.safetensors"},
                "class_type": "CheckpointLoaderSimple"
            },
            # Node 2: Gemma CLIP Model Loader
            "2": {
                "inputs": {
                    "gemma_path": "gemma_3_12B_it_fp4_mixed.safetensors",
                    "ltxv_path": "ltx-2.3-22b-dev-fp8.safetensors",
                    "max_length": 1024
                },
                "class_type": "LTXVGemmaCLIPModelLoader"
            },
            # Node 3: Positive prompt
            "3": {
                "inputs": {
                    "text": prompt,
                    "clip": ["2", 0]
                },
                "class_type": "CLIPTextEncode"
            },
            # Node 4: Negative prompt
            "4": {
                "inputs": {
                    "text": negative_prompt,
                    "clip": ["2", 0]
                },
                "class_type": "CLIPTextEncode"
            },
            # Node 8: Sampler
            "8": {
                "inputs": {"sampler_name": "euler"},
                "class_type": "KSamplerSelect"
            },
            # Node 9: Scheduler
            "9": {
                "inputs": {
                    "steps": steps,
                    "max_shift": 2.05,
                    "base_shift": 0.95,
                    "stretch": True,
                    "terminal": 0.1
                },
                "class_type": "LTXVScheduler"
            },
            # Node 11: Random noise
            "11": {
                "inputs": {"noise_seed": int(time.time()) % 1000000},
                "class_type": "RandomNoise"
            },
            # Node 12: VAE Decode
            "12": {
                "inputs": {
                    "samples": ["41", 0],
                    "vae": ["1", 2]
                },
                "class_type": "VAEDecode"
            },
            # Node 15: Video Combine (Save)
            "15": {
                "inputs": {
                    "frame_rate": fps,
                    "loop_count": 0,
                    "filename_prefix": "ltx_video",
                    "format": "video/h264-mp4",
                    "pix_fmt": "yuv420p",
                    "crf": 19,
                    "save_metadata": True,
                    "save_output": True,
                    "images": ["12", 0]
                },
                "class_type": "VHS_VideoCombine"
            },
            # Node 17: Multimodal Guider
            "17": {
                "inputs": {
                    "skip_blocks": 29,
                    "model": ["44", 0],
                    "positive": ["22", 0],
                    "negative": ["22", 1]
                },
                "class_type": "MultimodalGuider"
            },
            # Node 18: Guider Parameters (Video)
            "18": {
                "inputs": {
                    "modality": "VIDEO",
                    "cfg": cfg,
                    "stg": 0,
                    "rescale": 0,
                    "modality_scale": 3
                },
                "class_type": "GuiderParameters"
            },
            # Node 22: Conditioning
            "22": {
                "inputs": {
                    "frame_rate": fps,
                    "positive": ["3", 0],
                    "negative": ["4", 0]
                },
                "class_type": "LTXVConditioning"
            },
            # Node 23: FPS constant
            "23": {
                "inputs": {"value": fps},
                "class_type": "FloatConstant"
            },
            # Node 27: Frames constant
            "27": {
                "inputs": {"value": num_frames},
                "class_type": "INTConstant"
            },
            # Node 41: Sampler
            "41": {
                "inputs": {
                    "noise": ["11", 0],
                    "guider": ["17", 0],
                    "sampler": ["8", 0],
                    "sigmas": ["9", 0],
                    "latent_image": ["43", 0]
                },
                "class_type": "SamplerCustomAdvanced"
            },
            # Node 43: Empty Latent Video
            "43": {
                "inputs": {
                    "width": width,
                    "height": height,
                    "length": num_frames,
                    "batch_size": 1
                },
                "class_type": "EmptyLTXVLatentVideo"
            },
            # Node 44: Model Patcher
            "44": {
                "inputs": {
                    "torch_compile": False,
                    "disable_backup": False,
                    "model": ["1", 0]
                },
                "class_type": "LTXVSequenceParallelMultiGPUPatcher"
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
    
    def generate_i2v(self, image_path: str, prompt: str,
                     num_frames: int = 81,
                     width: int = 512,
                     height: int = 768,
                     fps: int = 24,
                     output_name: str = None) -> Optional[str]:
        """Image-to-Video - использует I2V workflow"""
        if not self.available:
            logger.error("ComfyUI недоступен")
            return None
        
        # Upload image
        image_name = self._upload_image(image_path)
        if not image_name:
            logger.error("Не удалось загрузить изображение")
            return None
        
        logger.info(f"Загружено: {image_name}")
        
        # I2V workflow (из video_ltx2_3_i2v.json)
        prompt_data = {
            # Node 269: LoadImage
            "269": {
                "inputs": {
                    "image_path": image_name,
                    "choose_image_to_upload": "uploaded_image"
                },
                "class_type": "LoadImage"
            },
            # Node 320: LTX Video I2V
            "320": {
                "inputs": {
                    "input": ["269", 0],
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
        
        prompt_id = self._queue_prompt(prompt_data)
        if not prompt_id:
            return None
        
        logger.info(f"В очереди I2V: {prompt_id}")
        
        output_file = self._wait_for_result(prompt_id, timeout=600)
        
        if output_file:
            source = Path("C:/ai-project/ComfyUI/output") / output_file
            
            if source.exists():
                out_path = self.output_dir / (output_name or f"ltx_i2v_{int(time.time())}.mp4")
                shutil.copy(source, out_path)
                return str(out_path)
        
        return None


def generate_video(prompt: str = None, output_dir: str = TEMP_DIR) -> Optional[str]:
    gen = LTXVideoGenerator()
    return gen.generate_t2v(prompt) if prompt else None


if __name__ == "__main__":
    gen = LTXVideoGenerator()
    print(f"ComfyUI: {gen.available}")
    if gen.available:
        print("Generating test video...")
        result = gen.generate_t2v("A wizard casting a magical spell with glowing particles")
        print(f"Result: {result}")