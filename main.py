#!/usr/bin/env python3
"""
AutoVideo Generator - Main Entry Point

Автоматическая система генерации видео:
1. Принимает текстовую идею
2. Генерирует JSON сценарий через LLM (Qwen2-VL через Ollama)
3. Генерирует изображения (Stable Diffusion XL)
4. Генерирует видео (LTX 2.3 / базовый аниматор)
5. Склеивает сцены в один видеофайл
6. Сохраняет результат

Полностью автоматически, без участия пользователя!
"""

import argparse
import logging
import sys
import os
import json
from pathlib import Path
from typing import Optional, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from pipeline import (
    generate_script,
    validate_script,
    extract_characters_from_script,
    extract_all_dialogs,
    ImageGenerator,
    VideoGenerator,
    VideoConcatenator,
    ComfyUIVideoGenerator,
    SimpleVideoGenerator,
    TTSGenerator,
    LipSyncGenerator,
    CharacterVideoGenerator,
    LTXVideoGenerator,
)
from config import (
    OUTPUT_DIR,
    TEMP_DIR,
    FINAL_VIDEO_NAME,
    SCENE_DURATION,
    INSTAGRAM_FORMATS,
    DEFAULT_FORMAT,
    DEFAULT_VIDEO_MODEL,
    COMFYUI_CHECKPOINT_PATH
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AutoVideoPipeline:
    """Main video generation pipeline with character and dialog support"""
    
    def __init__(self, output_dir: str = OUTPUT_DIR, temp_dir: str = TEMP_DIR, 
                 format_name: str = DEFAULT_FORMAT, video_model: str = DEFAULT_VIDEO_MODEL):
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir)
        self.format_name = format_name
        self.video_model = video_model
        
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Get format info
        format_info = INSTAGRAM_FORMATS.get(format_name, INSTAGRAM_FORMATS[DEFAULT_FORMAT])
        logger.info(f"Using format: {format_name} ({format_info['aspect_ratio']})")
        logger.info(f"Using video model: {video_model}")
        
        # Initialize components
        self.script_gen = None  # Uses module-level function
        self.image_generator = ImageGenerator(str(self.temp_dir), format_name)
        self.video_generator = VideoGenerator(str(self.temp_dir))
        
        # Character and dialog components
        self.tts_generator = TTSGenerator(str(self.temp_dir))
        self.lipsync_generator = LipSyncGenerator(str(self.temp_dir))
        self.character_video_generator = CharacterVideoGenerator(str(self.temp_dir))
        
        # LTX Video generator (приоритет)
        self.ltx_generator = None
        
        if video_model in ["ltx", "wan"]:
            try:
                self.ltx_generator = LTXVideoGenerator()
                if not self.ltx_generator.available:
                    logger.warning("LTX недоступен, используем простой генератор")
                    self.ltx_generator = None
            except Exception as e:
                logger.warning(f"LTX не работает: {e}")
        
        self.concatenator = VideoConcatenator(str(self.output_dir), str(self.temp_dir))
        
        logger.info(f"Pipeline initialized. Output: {self.output_dir}")
        logger.info("Character and dialog support: ENABLED")
    
    def run(self, idea: str, num_scenes: int = 4) -> str:
        """
        Run the complete video generation pipeline
        
        Args:
            idea: Text idea description
            num_scenes: Number of scenes to generate
            
        Returns:
            Path to the final generated video
        """
        logger.info("=" * 60)
        logger.info(f"Starting AutoVideo Pipeline")
        logger.info(f"Idea: {idea}")
        logger.info(f"Scenes: {num_scenes}")
        logger.info("=" * 60)
        
        # Step 1: Generate JSON script
        logger.info("\n[1/5] Generating video script from idea...")
        script = generate_script(idea, num_scenes)
        
        # Validate script
        validate_script(script)
        logger.info(f"  ✓ Generated {len(script)} scenes")
        
        # Safe preview - show first 2 scenes
        preview_scenes = []
        for i, s in enumerate(script[:2]):
            if isinstance(s, dict):
                preview_scenes.append({
                    "scene_id": s.get("scene_id", i+1),
                    "description": s.get("description", "")[:50]
                })
        logger.info(f"  Preview: {json.dumps(preview_scenes)}...")
        
        # Step 2: Generate images for each scene
        logger.info("\n[2/5] Generating images with Stable Diffusion XL...")
        image_paths = self.image_generator.generate_all_images(script)
        
        for i, (scene, img_path) in enumerate(zip(script, image_paths)):
            # Safely get scene_id
            if isinstance(scene, dict):
                scene_id = scene.get("scene_id", i+1)
                if scene_id == 0:
                    scene_id = i + 1
            else:
                scene_id = i + 1
            logger.info(f"  Scene {scene_id}: {os.path.basename(img_path)}")
        
        # Step 2.5: Generate TTS audio for dialogs (NEW!)
        all_dialogs = extract_all_dialogs(script)
        if all_dialogs:
            logger.info("\n[2.5/6] Generating speech audio for dialogs...")
            # Group dialogs by scene
            audio_by_scene = {}
            for scene in script:
                scene_id = scene.get("scene_id", 0)
                scene_dialogs = scene.get("dialogs", [])
                if scene_dialogs:
                    audio_paths_scene = self.tts_generator.generate_all_dialogs(scene_dialogs)
                    audio_by_scene[scene_id] = audio_paths_scene
                    logger.info(f"  Scene {scene_id}: {len(audio_paths_scene)} dialogs")
        else:
            audio_by_scene = {}
        
        # Step 3: Generate videos from images
        logger.info("\n[3/6] Generating videos...")

        video_paths = []

        if self.ltx_generator and self.ltx_generator.available:
            # Use LTX 2.3
            logger.info("Using LTX Video Generator...")
            for i, scene in enumerate(script):
                scene_id = scene.get("scene_id", i+1) if isinstance(scene, dict) else i+1
                prompt = scene.get("description", "") if isinstance(scene, dict) else str(scene)
                img_path = image_paths[i]
                
                if img_path and Path(img_path).exists():
                    video_path = self.ltx_generator.generate_i2v(
                        img_path, prompt, 81,
                        output_name=f"scene_{scene_id}.mp4"
                    )
                else:
                    video_path = self.ltx_generator.generate_t2v(
                        prompt, 81,
                        output_name=f"scene_{scene_id}.mp4"
                    )
                
                if not video_path:
                    video_path = str(self.temp_dir / f"scene_{scene_id}.mp4")
                video_paths.append(video_path)
                logger.info(f"  Scene {scene_id}: {os.path.basename(video_path)}")

        elif self.simple_generator:
