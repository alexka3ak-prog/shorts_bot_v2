"""
Simple Video Generator - FFmpeg based fallback
Создает видео из изображений с простыми эффектами
"""

import os
import logging
import subprocess
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# FFmpeg path
FFMPEG_PATH = os.environ.get("FFMPEG_PATH", "ffmpeg")


class SimpleVideoGenerator:
    """Простой генератор видео через FFmpeg"""
    
    def __init__(self, output_dir: str = "output/temp"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check FFmpeg
        self.has_ffmpeg = self._check_ffmpeg()
        if not self.has_ffmpeg:
            logger.warning("FFmpeg not found, using fallback")
    
    def _check_ffmpeg(self) -> bool:
        """Проверить FFmpeg"""
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
                   fps: int = 24,
                   effect: str = "zoom") -> str:
        """
        Генерировать видео из изображения
        
        Args:
            image_path: Путь к изображению
            output_path: Путь для сохранения видео
            duration: Длительность в секундах
            fps: Кадров в секунду
            effect: Эффект - "zoom", "fade", "pan"
            
        Returns:
            Путь к видео
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
        """FFmpeg генерация"""
        
        total_frames = int(duration * fps)
        
        if effect == "zoom":
            # Плавный зум эффект
            filter_complex = (
                f"zoompan=z='min(zoom+0.001,1.5)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"d={total_frames}:s={fps}p,format=yuv420p"
            )
        elif effect == "pan":
            # Плавное движение
            filter_complex = (
                f"zoompan=x=lerp(0,iw/4,n/{total_frames}):y=lerp(0,ih/4,n/{total_frames}):"
                f"d={total_frames}:s={fps}p,format=yuv420p"
            )
        elif effect == "fade":
            # Fade эффект
            filter_complex = (
                f"fade=t=in:st=0:d=1,fade=t=out:st={duration-1}:d=1,"
                f"format=yuv420p"
            )
        else:
            filter_complex = "format=yuv420p"
        
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
        """Простой fallback - копирует изображение как видео placeholder"""
        import shutil
        
        # Просто копируем как placeholder
        # В реальном случае нужно установить ffmpeg
        output_path = output_path.with_suffix(".mp4")
        shutil.copy(image_path, output_path)
        
        logger.warning(f"Created placeholder: {output_path} (install ffmpeg for real video)")
        return str(output_path)


def generate_simple_video(image_path: str,
                        output_path: str,
                        duration: float = 4.0,
                        effect: str = "zoom") -> str:
    """Удобная функция"""
    generator = SimpleVideoGenerator()
    return generator.generate_video(image_path, output_path, duration, effect=effect)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test
    gen = SimpleVideoGenerator()
    print(f"FFmpeg available: {gen.has_ffmpeg}")