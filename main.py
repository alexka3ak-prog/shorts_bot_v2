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
    ImageGenerator,
    VideoGenerator,
    VideoConcatenator
)
from config import (
    OUTPUT_DIR,
    TEMP_DIR,
    FINAL_VIDEO_NAME,
    SCENE_DURATION,
    INSTAGRAM_FORMATS,
    DEFAULT_FORMAT
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AutoVideoPipeline:
    """Main video generation pipeline"""
    
    def __init__(self, output_dir: str = OUTPUT_DIR, temp_dir: str = TEMP_DIR, 
                 format_name: str = DEFAULT_FORMAT):
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir)
        self.format_name = format_name
        
        # Ensure directories exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Get format info
        format_info = INSTAGRAM_FORMATS.get(format_name, INSTAGRAM_FORMATS[DEFAULT_FORMAT])
        logger.info(f"Using format: {format_name} ({format_info['aspect_ratio']})")
        
        # Initialize components
        self.script_gen = None  # Uses module-level function
        self.image_generator = ImageGenerator(str(self.temp_dir), format_name)
        self.video_generator = VideoGenerator(str(self.temp_dir))
        self.concatenator = VideoConcatenator(str(self.output_dir), str(self.temp_dir))
        
        logger.info(f"Pipeline initialized. Output: {self.output_dir}")
    
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
        logger.info(f"  Preview: {json.dumps(script[:2], indent=2)[:200]}...")
        
        # Step 2: Generate images for each scene
        logger.info("\n[2/5] Generating images with Stable Diffusion XL...")
        image_paths = self.image_generator.generate_all_images(script)
        
        for i, (scene, img_path) in enumerate(zip(script, image_paths)):
            logger.info(f"  Scene {scene['scene_id']}: {os.path.basename(img_path)}")
        
        # Step 3: Generate videos from images
        logger.info("\n[3/5] Generating videos with LTX 2.3...")
        video_paths = self.video_generator.generate_all_videos(script, image_paths)
        
        for i, (scene, vid_path) in enumerate(zip(script, video_paths)):
            logger.info(f"  Scene {scene['scene_id']}: {os.path.basename(vid_path)}")
        
        # Step 4: Concatenate videos
        logger.info("\n[4/5] Concatenating scene videos...")
        transitions = [s.get("transition", "fade") for s in script[:-1]]
        
        final_video = self.concatenator.concatenate_videos(
            video_paths,
            transitions=transitions,
            output_filename=FINAL_VIDEO_NAME
        )
        logger.info(f"  ✓ Final video: {os.path.basename(final_video)}")
        
        # Step 5: Generate metadata
        logger.info("\n[5/5] Saving metadata...")
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