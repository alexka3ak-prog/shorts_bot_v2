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
    CharacterVideoGenerator
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
        
        # ComfyUI video generator (для LTX/Wan)
        self.comfyui_generator = None
        self.simple_generator = None
        
        if video_model in ["ltx", "wan"]:
            try:
                self.comfyui_generator = ComfyUIVideoGenerator()
                # Check if LTX nodes are available
                nodes = self.comfyui_generator.check_ltx_nodes()
                if not nodes.get("LTXVideoSampler"):
                    logger.warning("LTX nodes not found, using simple fallback")
                    self.simple_generator = SimpleVideoGenerator(str(self.temp_dir))
            except Exception as e:
                logger.warning(f"ComfyUI not available: {e}, using simple fallback")
                self.simple_generator = SimpleVideoGenerator(str(self.temp_dir))
        
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
        
        if self.simple_generator:
            # Use simple FFmpeg-based generator
            logger.info("Using simple video generator (FFmpeg)")
            video_paths = []
            for i, (scene, img_path) in enumerate(zip(script, image_paths)):
                scene_id = scene.get("scene_id", i+1) if isinstance(scene, dict) else i+1
                duration = scene.get("duration", 4.0)
                
                output_path = self.temp_dir / f"scene_{scene_id}.mp4"
                vid_path = self.simple_generator.generate_video(
                    img_path, str(output_path), duration
                )
                video_paths.append(vid_path)
                logger.info(f"  Scene {scene_id}: {os.path.basename(vid_path)}")
        else:
            # Use default VideoGenerator
            video_paths = self.video_generator.generate_all_videos(script, image_paths)
            for i, (scene, vid_path) in enumerate(zip(script, video_paths)):
                scene_id = scene.get("scene_id", i+1) if isinstance(scene, dict) else i+1
                logger.info(f"  Scene {scene_id}: {os.path.basename(vid_path)}")
        
        # Step 4: Add character dialogs to videos (NEW!)
        if audio_by_scene:
            logger.info("\n[4/6] Adding dialog audio to videos...")
            enhanced_videos = []
            for i, (scene, vid_path) in enumerate(zip(script, video_paths)):
                scene_id = scene.get("scene_id", i+1) if isinstance(scene, dict) else i+1
                scene_dialogs = scene.get("dialogs", [])
                
                if scene_dialogs and scene_id in audio_by_scene:
                    scene_audio = audio_by_scene[scene_id]
                    # Generate video with audio (character video generator)
                    enhanced_path = self.character_video_generator.generate_scene_video(
                        scene, 
                        vid_path,
                        scene_audio,
                        str(self.temp_dir / f"scene_{scene_id}_dialog.mp4")
                    )
                    enhanced_videos.append(enhanced_path)
                    logger.info(f"  Scene {scene_id}: Added {len(scene_audio)} dialogs")
                else:
                    enhanced_videos.append(vid_path)
            video_paths = enhanced_videos
        
        # Step 5: Concatenate videos
        logger.info("\n[5/6] Concatenating scene videos...")
        
        # Safely extract transitions
        transitions = []
        for i, s in enumerate(script[:-1]):
            if isinstance(s, dict):
                transitions.append(s.get("transition", "fade"))
            else:
                transitions.append("fade")
        
        final_video = self.concatenator.concatenate_videos(
            video_paths,
            transitions=transitions,
            output_filename=FINAL_VIDEO_NAME
        )
        logger.info(f"  ✓ Final video: {os.path.basename(final_video)}")
        
        # Step 6: Generate metadata
        logger.info("\n[6/6] Saving metadata...")
        metadata = self.concatenator.generate_metadata(script, final_video, image_paths)
        
        logger.info("\n" + "=" * 60)
        logger.info("✓ Pipeline completed successfully!")
        logger.info(f"Final video: {final_video}")
        logger.info(f"Metadata: {self.output_dir / 'metadata.json'}")
        logger.info("=" * 60)
        
        return final_video


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="AutoVideo Generator - AI-powered automated video creation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "A journey through space discovering new planets"
  python main.py --idea "Beautiful sunset over ocean" --scenes 6
  python main.py -i "Forest adventure" -s 3 --output ./my_videos
        """
    )
    
    parser.add_argument(
        "idea",
        nargs="?",
        help="Text idea for the video (required if not using --idea)"
    )
    
    parser.add_argument(
        "-i", "--idea",
        dest="idea_arg",
        help="Text idea for the video"
    )
    
    parser.add_argument(
        "-s", "--scenes",
        type=int,
        default=4,
        help="Number of scenes to generate (default: 4)"
    )
    
    parser.add_argument(
        "-o", "--output",
        default=OUTPUT_DIR,
        help=f"Output directory (default: {OUTPUT_DIR})"
    )
    
    parser.add_argument(
        "-t", "--temp",
        default=TEMP_DIR,
        help=f"Temporary files directory (default: {TEMP_DIR})"
    )
    
    parser.add_argument(
        "-f", "--format",
        choices=list(INSTAGRAM_FORMATS.keys()),
        default=DEFAULT_FORMAT,
        help=f"Video format: {', '.join(INSTAGRAM_FORMATS.keys())} (default: {DEFAULT_FORMAT})"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Get the idea from args
    idea = args.idea or args.idea_arg
    
    if not idea:
        print("Error: Please provide a video idea")
        print("Usage: python main.py \"Your video idea here\"")
        print("   or: python main.py --idea \"Your video idea here\"")
        sys.exit(1)
    
    # Run the pipeline
    try:
        pipeline = AutoVideoPipeline(args.output, args.temp, args.format)
        final_video = pipeline.run(idea, args.scenes)
        
        print(f"\n✅ Success! Video generated: {final_video}")
        return 0
        
    except KeyboardInterrupt:
        logger.warning("\nPipeline interrupted by user")
        return 1
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())