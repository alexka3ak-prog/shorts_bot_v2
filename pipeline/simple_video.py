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
        """FFmpeg generation with various effects"""
        
        total_frames = int(duration * fps)
        
        # Animation effects
        effects = {
            # Smooth zoom
            "zoom": (
                f"zoompan=z='min(zoom+0.001,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"d={total_frames}:fps={fps},format=yuv420p"
            ),
            # Zoom in center
            "zoom_in": (
                f"zoompan=z='1+0.4*sin(n/{total_frames}*3.14159)':x='(iw-iw/zoom)/2':y='(ih-ih/zoom)/2':"
                f"d={total_frames}:fps={fps},format=yuv420p"
            ),
            # Pan left
            "pan_left": (
                f"zoompan=x=lerp(0,iw/4,n/{total_frames}):y='ih/4':"
                f"d={total_frames}:fps={fps},zoom='1-0.2*sin(n/{total_frames}*3.14159)',format=yuv420p"
            ),
            # Pan right
            "pan_right": (
                f"zoompan=x=lerp(iw/4,0,n/{total_frames}):y='ih/4':"
                f"d={total_frames}:fps={fps},zoom='1-0.2*sin(n/{total_frames}*3.14159)',format=yuv420p"
            ),
            # Tilt up
            "tilt_up": (
                f"zoompan=y=lerp(0,ih/4,n/{total_frames}):x='iw/4':"
                f"d={total_frames}:fps={fps},format=yuv420p"
            ),
            # Tilt down
            "tilt_down": (
                f"zoompan=y=lerp(ih/4,0,n/{total_frames}):x='iw/4':"
                f"d={total_frames}:fps={fps},format=yuv420p"
            ),
            # Circle motion
            "circle": (
                f"zoompan=x='iw/2+(iw/2.5)*cos(n/{total_frames}*6.28318)':y='ih/2+(ih/2.5)*sin(n/{total_frames}*6.28318)':"
                f"zoom='1-0.3*sin(n/{total_frames}*6.28318)':d={total_frames}:fps={fps},format=yuv420p"
            ),
            # Wave
            "wave": (
                f"zoompan=x='iw/2+(iw/10)*sin(n/fps*3)':y='ih/2+(ih/10)*cos(n/fps*2)':"
                f"d={total_frames}:fps={fps},format=yuv420p"
            ),
            # Fade only
            "fade": (
                f"fade=t=in:st=0:d=1,fade=t=out:st={duration-1}:d=1,format=yuv420p"
            ),
            # Float
            "float": (
                f"zoompan=y=lerp(-ih/10,ih/10,n/{total_frames}):x=lerp(-iw/10,iw/10,n/{total_frames}):"
                f"d={total_frames}:fps={fps},format=yuv420p"
            ),
        }
        
        # Choose effect or random
        if effect == "random":
            effect = random.choice(list(effects.keys()))
        
        filter_complex = effects.get(effect, effects["zoom"])
        
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-vf", filter_complex,
            "-t", str(duration),
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "18",
            str(output_path)
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=60)
            if result.returncode != 0:
                logger.warning(f"FFmpeg error: {result.stderr}")
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