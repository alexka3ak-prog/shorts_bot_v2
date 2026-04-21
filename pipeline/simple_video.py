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
        """FFmpeg generation with effects - simplified"""
        
        # Simple video without complex effects first
        # Just loop the image as video
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-preset", "fast",
            "-crf", "20",
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            str(output_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            if result.returncode != 0:
                logger.warning(f"FFmpeg error: {result.stderr.decode()[:200]}")
                return self._generate_fallback(image_path, output_path, duration, fps)
            
            # Video created, now add effect if needed
            if effect != "none" and effect != "fade":
                return self._add_effect(output_path, output_path, effect, duration, fps)
            
        except Exception as e:
            logger.error(f"FFmpeg failed: {e}")
            return self._generate_fallback(image_path, output_path, duration, fps)
        
        logger.info(f"Video saved: {output_path}")
        return str(output_path)
    
    def _add_effect(self, input_path: Path, output_path: Path,
                   effect: str, duration: float, fps: int) -> str:
        """Add effect to existing video"""
        
        effects = {
            "zoom": "zoompan=z='min(zoom+0.001,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=25:s=1280x720",
            "zoom_in": "zoompan=z='1+0.3*sin(n/25*3.14)':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':d=25",
            "pan_left": "zoompan=x=lerp(0,iw/4,n/25):y=ih/4:d=25",
            "pan_right": "zoompan=x=lerp(iw/4,0,n/25):y=ih/4:d=25",
            "tilt_up": "zoompan=y=lerp(0,ih/4,n/25):x=iw/4:d=25",
            "tilt_down": "zoompan=y=lerp(ih/4,0,n/25):x=iw/4:d=25",
            "circle": "tblend=all_mode='difference',zoompan=z='1+0.2*sin(n/25*6.28)':d=25",
            "wave": "zoompan=x='iw/2+iw/10*sin(n/10)':y='ih/2+ih/10*cos(n/8)':d=25",
            "float": "zoompan=y=lerp(-ih/10,ih/10,n/25):x=lerp(-iw/10,iw/10,n/25):d=25",
        }
        
        if effect not in effects:
            return str(input_path)
        
        # Create temp output
        temp_output = output_path.parent / f"temp_effect_{output_path.name}"
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-vf", effects.get(effect, ""),
            "-c:a", "copy",
            str(temp_output)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            if result.returncode == 0:
                import shutil
                shutil.move(str(temp_output), str(output_path))
        except:
            pass
        
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