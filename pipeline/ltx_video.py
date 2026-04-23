"""
LTX Video Generator via ComfyUI API

Поддерживает:
- T2V (Text-to-Video) с текстовым промптом
- I2V (Image-to-Video) из изображения

Важное примечание о нодах:
- EmptyLTXVLatentVideo, LTXVScheduler, LTXVSeparateAVLatent, LTXVConcatAVLatent - это
  ВСТРОЕННЫЕ ноды ComfyUI (comfy_extras/nodes_lt.py), а НЕ ComfyUI-LTXVideo
- Используем workflow из example_workflows/2.3/LTX-2.3_T2V_I2V_Single_Stage_Distilled_Full.json
- Упрощённая версия для T2V генерации
"""
import os
import json
import logging
import uuid
import time
import requests
import shutil
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from config import (
        COMFYUI_HOST,
        COMFYUI_PORT,
        TEMP_DIR,
        OUTPUT_DIR,
        COMFYUI_CHECKPOINT_PATH,
    )
except ImportError:
    COMFYUI_HOST = "127.0.0.1"
    COMFYUI_PORT = 8188
    TEMP_DIR = "/workspace/project/shorts_bot_v2/output/temp"
    OUTPUT_DIR = "/workspace/project/shorts_bot_v2/output"
    COMFYUI_CHECKPOINT_PATH = "D:/Models/ComfyUI_Models/models/checkpoints"

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
        self.comfyui_output_dir = None  # Will be determined dynamically
        logger.info(f"LTXVideoGenerator: ComfyUI={'доступен' if self.available else 'недоступен'}")
    
    def _check_connection(self) -> bool:
        """Проверить подключение к ComfyUI и получить output directory"""
        try:
            resp = requests.get(f"{self.base_url}/api/object_info", timeout=5)
            if resp.status_code == 200:
                # Try to get output directory from system stats
                try:
                    stats = requests.get(f"{self.base_url}/api/system_stats", timeout=5)
                    if stats.status_code == 200:
                        data = stats.json()
                        self.comfyui_output_dir = data.get("output_directory")
                        if self.comfyui_output_dir:
                            logger.info(f"ComfyUI output dir: {self.comfyui_output_dir}")
                except:
                    pass
                return True
        except:
            pass
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
    
    def _wait_for_result(self, prompt_id: str, timeout: int = 600) -> Optional[Dict[str, Any]]:
        """Ждать результата и вернуть полные outputs"""
        start = time.time()
        
        while time.time() - start < timeout:
            try:
                resp = requests.get(f"{self.base_url}/api/prompt_history/{prompt_id}", timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    status = data.get("status", {})
                    
                    if status.get("completed"):
                        outputs = data.get("outputs", {})
                        # Return the full outputs for processing
                        return outputs
                    
                    if status.get("error"):
                        logger.error(f"Error: {status['error']}")
                        return None
                        
            except Exception as e:
                logger.debug(f"Waiting... {e}")
            
            time.sleep(3)
        
        logger.warning("Timeout waiting for result")
        return None
    
    def _get_output_filename(self, outputs: Dict[str, Any]) -> Optional[str]:
        """Извлечь имя файла из outputs"""
        for node_id, out in outputs.items():
            # VHS_VideoCombine
            if "video" in out:
                fname = out["video"].get("filename")
                if fname:
                    logger.info(f"Video generated: {fname}")
                    return fname
            # SaveVideo node
            if "videos" in out:
                for v in out.get("videos", []):
                    if v.get("filename"):
                        return v["filename"]
            # Images (for VAEDecode)
            if "images" in out:
                for img in out.get("images", []):
                    if img.get("filename"):
                        logger.info(f"Images generated: {img['filename']}")
                        return img["filename"]
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
        
        Использует локальный encoder БЕЗ API:
        - LTXAVTextEncoderLoader (загружает Gemma локально)
        - CLIPTextEncode (кодирует промпт без API key!)
        - MultimodalGuider
        - KSampler + LTXVScheduler
        """
        if not self.available:
            logger.error("ComfyUI недоступен")
            return None
        
        logger.info(f"Generating T2V: {prompt[:50]}...")
        
        # Упрощённый T2V workflow - точно как в v4.1
        prompt_data = {
            # Node 1: Checkpoint
            "1": {
                "inputs": {"ckpt_name": "ltx-2.3-22b-dev-fp8.safetensors"},
                "class_type": "CheckpointLoaderSimple"
            },
            # Node 2: LTX AV Text Encoder Loader (локальный)
            "2": {
                "inputs": {
                    "text_encoder": "gemma_3_12B_it_fp4_mixed.safetensors",
                    "ckpt_name": "ltx-2.3-22b-dev-fp8.safetensors",
                    "device": "default"
                },
                "class_type": "LTXAVTextEncoderLoader"
            },
            # Node 3: Apply LoRA (optional, for better quality)
            "3": {
                "inputs": {
                    "model": ["1", 0],
                    "lora_name": "ltx-2.3-22b-distilled-lora-384.safetensors",
                    "strength_model": 1.0
                },
                "class_type": "LoraLoaderModelOnly"
            },
            # Node 5: Positive Prompt - CLIPTextEncode (локальный)
            "5": {
                "inputs": {
                    "text": prompt,
                    "clip": ["2", 0]
                },
                "class_type": "CLIPTextEncode"
            },
            # Node 6: Negative Prompt
            "6": {
                "inputs": {
                    "text": negative_prompt,
                    "clip": ["2", 0]
                },
                "class_type": "CLIPTextEncode"
            },
            # Node 8: Empty Latent Video
            "8": {
                "inputs": {
                    "width": width,
                    "height": height,
                    "length": num_frames,
                    "batch_size": 1
                },
                "class_type": "EmptyLTXVLatentVideo"
            },
            # Node 13: LTX Conditioning
            "13": {
                "inputs": {
                    "positive": ["5", 0],
                    "negative": ["6", 0],
                    "frame_rate": fps
                },
                "class_type": "LTXVConditioning"
            },
            # Node 14: Scheduler
            "14": {
                "inputs": {
                    "steps": steps,
                    "max_shift": 2.05,
                    "base_shift": 0.95,
                    "stretch": True,
                    "terminal": 0.1
                },
                "class_type": "LTXVScheduler"
            },
            # Node 15: Sampler
            "15": {
                "inputs": {"sampler_name": "euler"},
                "class_type": "KSamplerSelect"
            },
            # Node 16: Random noise
            "16": {
                "inputs": {"noise_seed": int(time.time()) % 1000000},
                "class_type": "RandomNoise"
            },
            # Node 17: CFG Guider (как в v4.1!)
            "17": {
                "inputs": {
                    "model": ["3", 0],
                    "positive": ["13", 0],
                    "negative": ["13", 1],
                    "cfg": cfg
                },
                "class_type": "CFGGuider"
            },
            # Node 18: Sampler
            "18": {
                "inputs": {
                    "noise": ["16", 0],
                    "guider": ["17", 0],
                    "sampler": ["15", 0],
                    "sigmas": ["14", 0],
                    "latent_image": ["8", 0]
                },
                "class_type": "SamplerCustomAdvanced"
            },
            # Node 19: Separate AV
            "19": {
                "inputs": {
                    "av_latent": ["18", 0]
                },
                "class_type": "LTXVSeparateAVLatent"
            },
            # Node 20: VAE Decode
            "20": {
                "inputs": {
                    "samples": ["19", 0],
                    "vae": ["1", 2]
                },
                "class_type": "LTXVTiledVAEDecode"
            },
            # Node 21: Create Video
            "21": {
                "inputs": {
                    "frame_rate": fps
                },
                "class_type": "CreateVideo"
            },
            # Node 22: Save Video
            "22": {
                "inputs": {
                    "video": ["21", 0]
                },
                "class_type": "SaveVideo"
            }
        }
        
        # Queue
        prompt_id = self._queue_prompt(prompt_data)
        if not prompt_id:
            logger.error("Не удалось поставить в очередь")
            return None
        
        logger.info(f"В очереди: {prompt_id}")
        
        # Wait for completion
        outputs = self._wait_for_result(prompt_id, timeout=600)
        
        if outputs:
            # Get filename from outputs
            output_file = self._get_output_filename(outputs)
            
            if output_file:
                # Determine source path (try dynamic first, then common defaults)
                source = None
                
                if self.comfyui_output_dir:
                    potential_paths = [
                        Path(self.comfyui_output_dir) / output_file,
                        Path(self.comfyui_output_dir.replace("\\", "/")) / output_file,
                    ]
                    for p in potential_paths:
                        if p.exists():
                            source = p
                            break
                
                # Common ComfyUI output paths on Windows
                if not source:
                    common_paths = [
                        Path("C:/ai-project/ComfyUI/output") / output_file,
                        Path("C:/ComfyUI/output") / output_file,
                        Path("D:/Models/ComfyUI/output") / output_file,
                        Path("output") / output_file,
                        Path("ComfyUI/output") / output_file,
                    ]
                    for p in common_paths:
                        if p.exists():
                            source = p
                            break
                
                if source and source.exists():
                    out_path = self.output_dir / (output_name or output_file)
                    shutil.copy(source, out_path)
                    logger.info(f"Saved: {out_path}")
                    return str(out_path)
                else:
                    logger.warning(f"Output file not found: {output_file}")
                    logger.warning(f"Searched paths: {self.comfyui_output_dir}, C:/ai-project/ComfyUI/output")
                    return str(output_file) if output_file else None
        
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
        
        logger.info(f"Queued I2V: {prompt_id}")
        
        # Wait for completion
        outputs = self._wait_for_result(prompt_id, timeout=600)
        
        if outputs:
            output_file = self._get_output_filename(outputs)
            
            if output_file:
                source = None
                if self.comfyui_output_dir:
                    source = Path(self.comfyui_output_dir) / output_file
                
                if not source or not source.exists():
                    for p in [
                        Path("C:/ai-project/ComfyUI/output") / output_file,
                        Path("output") / output_file,
                    ]:
                        if p.exists():
                            source = p
                            break
                
                if source and source.exists():
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