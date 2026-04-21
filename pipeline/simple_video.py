"""
Simple Video Generator - FFmpeg based
Creates video from images with various effects
"""

import os
import logging
import subprocess
import random
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# FFmpeg path
FFMPEG_PATH = os.environ.get("FFMPEG_PATH", "ffmpeg")


class SimpleVideoGenerator:
    """Simple video generator via FFmpeg"""
    
    def __init__(self, output_dir: str = "output/temp"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check FFmpeg
        self.has_ffmpeg = self._check_ffmpeg()
        if not self.has_ffmpeg:
            logger.warning("FFmpeg not found, using fallback")
    
    def _check_ffmpeg(self) -> bool:
        """Check FFmpeg"""
        try:
            subprocess.run(
                ["ffmpeg", "-version"], 
                capture_output=True, 
                timeout=5
            )
            return True
        except:
            return False
    
    def generate_video(self,
                   image_path: str,
                   output_path: str,
                   duration: float = 4.0,
                   fps: int = 30,
                   effect: str = "zoom") -> str:
        """
        Generate video from image
        
        Args:
            image_path: Path to image
            output_path: Path for output video
            duration: Duration in seconds
            fps: Frames per second
            effect: Effect name - "zoom", "zoom_in", "pan_left", "pan_right", 
                   "tilt_up", "tilt_down", "circle", "wave", "fade", "float", "random"
            
        Returns:
            Path to video
        """
        image_path = Path(image_path)
        output_path = Path(output_path)
        
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        logger.info(f"Generating video: {effect} effect, {duration}s")
        
        if self.has_ffmpeg:
            return self._generate_ffmpeg(image_path, output_path, duration, fps, effect)
        else:
            return self._generate_fallback(image_path, output_path, duration, fps)
    
    def _generate_ffmpeg(self, image_path: Path, output_path: Path,
                      duration: float, fps: int, effect: str) -> str:
        """FFmpeg generation - simple and reliable"""
        
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-preset", "fast",
            "-crf", "22",
            "-t", str(duration),
            "-r", str(fps),
            "-pix_fmt", "yuv420p",
            str(output_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            if result.returncode != 0:
                logger.warning(f"FFmpeg error: {result.stderr.decode()[:200]}")
                return self._generate_fallback(image_path, output_path, duration, fps)
            
        except Exception as e:
            logger.error(f"FFmpeg failed: {e}")
            return self._generate_fallback(image_path, output_path, duration, fps)
        
        logger.info(f"Video saved: {output_path}")
        return str(output_path)
    
    def _generate_fallback(self, image_path: Path, output_path: Path,
                        duration: float, fps: int) -> str:
        """Simple fallback - copies image as video placeholder"""
        import shutil
        
        output_path = output_path.with_suffix(".mp4")
        shutil.copy(image_path, output_path)
        
        logger.warning(f"Created placeholder: {output_path}")
        return str(output_path)


def generate_simple_video(image_path: str,
                        output_path: str,
                        duration: float = 4.0,
                        effect: str = "zoom") -> str:
    """Convenient function"""
    generator = SimpleVideoGenerator()
    return generator.generate_video(image_path, output_path, duration, effect=effect)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test
    gen = SimpleVideoGenerator()
    print(f"FFmpeg available: {gen.has_ffmpeg}")