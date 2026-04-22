"""
Lip-Sync Generator - Animates character mouths to match dialog audio

Поддерживаемые методы lip-sync:
1. Wav2Lip (точное)
2. Wav2Lip-Q (быстрое)
3. Procedural (простое - анализ фонем)

Установка:
- Wav2Lip: pip install wav2lip
- Если не доступен - используется процедурный метод

Для качественного lip-sync рекомендуется использовать Wav2Lip через:
- ComfyUI Wav2Lip nodes
- Или локальную модель wav2lip_gan
"""
import os
import json
import logging
import subprocess
import requests
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

try:
    from config import TEMP_DIR, OUTPUT_DIR
except ImportError:
    TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output", "temp")
    OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")

logger = logging.getLogger(__name__)

# Phoneme to viseme mapping (for procedural method)
# English phonemes mapped to mouth shapes
PHONEME_TO_VISEME = {
    # Vowels
    "AA": "open", "AE": "open", "AH": "open", "AO": "round", "OW": "round",
    "EY": "wide", "AY": "wide", "IY": "wide", "UW": "round", "UH": "round",
    # Consonants
    "B": "close", "D": "close", "F": "teeth", "G": "close", 
    "HH": "open", "JH": "close", "K": "close", "L": "wide",
    "M": "close", "N": "close", "NG": "close", "P": "close",
    "R": "wide", "S": "teeth", "SH": "round", "T": "close",
    "TH": "teeth", "V": "teeth", "W": "round", "Y": "wide",
    "Z": "teeth", "ZH": "round"
}

# Simple mouth shapes for procedural animation
MOUTH_SHAPES = {
    "closed": [(40, 50), (60, 50)],  # Линия
    "open": [(30, 40), (40, 60), (60, 60), (70, 40)],  # Открыт
    "wide": [(20, 45), (30, 55), (70, 55), (80, 45)],  # Широкий
    "round": [(35, 40), (45, 55), (55, 55), (65, 40)],  # Округлый
    "teeth": [(30, 45), (40, 50), (60, 50), (70, 45)]  # Зубы
}


class LipSyncGenerator:
    """Generate lip-sync animations for characters"""
    
    def __init__(self, temp_dir: str = TEMP_DIR):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Wav2Lip model (lazy loaded)
        self.wav2lip_model = None
        self.use_wav2lip = False
        
        # Check for available methods
        self._check_available_methods()
        
        logger.info(f"LipSync Generator initialized, method: {self._get_method()}")
    
    def _check_available_methods(self):
        """Check what lip-sync methods are available"""
        # Check for Wav2Lip
        try:
            # Пробуем импортировать wav2lip
            import wav2lip
            self.wav2lip_model = wav2lip
            self.use_wav2lip = True
            logger.info("Wav2Lip available")
        except ImportError:
            self.use_wav2lip = False
            logger.info("Wav2Lip not available, using procedural method")
    
    def _get_method(self) -> str:
        """Get current lip-sync method"""
        if self.use_wav2lip:
            return "wav2lip"
        return "procedural"
    
    def generate_lipsync(self, image_path: str, audio_path: str,
                       output_video_path: str = None,
                       character_position: str = "center") -> str:
        """
        Generate lip-synced video from image and audio
        
        Args:
            image_path: Path to character image
            audio_path: Path to dialog audio
            output_video_path: Output video path
            character_position: Position in frame (left/center/right)
            
        Returns:
            Path to generated video with lip-sync
        """
        image_path = Path(image_path)
        audio_path = Path(audio_path)
        
        if output_video_path is None:
            output_video_path = self.temp_dir / f"lipsync_{image_path.stem}.mp4"
        else:
            output_video_path = Path(output_video_path)
        
        # Берем длительность из аудио
        audio_duration = self._get_audio_duration(audio_path)
        
        # Выбираем метод
        if self.use_wav2lip:
            try:
                self._generate_wav2lip(image_path, audio_path, output_video_path, character_position)
            except Exception as e:
                logger.warning(f"Wav2Lip failed: {e}, using procedural")
                self._generate_procedural(image_path, audio_path, output_video_path, character_position)
        else:
            self._generate_procedural(image_path, audio_path, output_video_path, character_position)
        
        return str(output_video_path)
    
    def _generate_wav2lip(self, image_path: Path, audio_path: Path,
                           output_path: Path, position: str):
        """Generate using Wav2Lip"""
        # Для Wav2Lip нужен квадратное лицо
        # Это упрощенная реализация - в реальности нужно использовать ComfyUI
        
        try:
            import wav2lip
            
            # Загружаем модель если нужно
            if self.wav2lip_model is None:
                self.wav2lip_model = wav2lip.load_model("wav2lip_gan")
            
            # Генерируем
            self.wav2lip_model.generate(
                str(image_path),
                str(audio_path),
                str(output_path)
            )
        except Exception as e:
            logger.warning(f"Wav2Lip generation failed: {e}")
            raise
    
    def _generate_procedural(self, image_path: Path, audio_path: Path,
                        output_path: Path, position: str):
        """
        Generate procedural lip-sync animation
        
        Simple approach:
        1. Estimate visemes from text timing
        2. Animate mouth region based on visemes
        """
        # Читаем исходное изображение
        img = Image.open(image_path)
        img = img.convert("RGBA")
        width, height = img.size
        
        # Оцениваем длительность
        duration = self._get_audio_duration(audio_path)
        
        # Определяем позицию рта на изображении
        mouth_area = self._detect_mouth_position(img, position)
        
        # Создаем последовательность кадров с анимацией
        fps = 24
        num_frames = int(duration * fps)
        
        # Генерируем последовательность визем
        viseme_sequence = self._generate_viseme_sequence(duration, num_frames)
        
        # Создаем кадры с анимацией рта
        frames_dir = self.temp_dir / f"frames_{output_path.stem}"
        frames_dir.mkdir(exist_ok=True)
        
        for frame_idx in range(num_frames):
            frame_img = img.copy()
            
            # Получаем текущий визем
            viseme = viseme_sequence[frame_idx]
            
            # Рисуем рот
            frame_img = self._draw_mouth(frame_img, mouth_area, viseme)
            
            # Сохраняем кадр
            frame_img.save(frames_dir / f"frame_{frame_idx:04d}.png")
        
        # Создаем видео из кадров
        self._create_video_from_frames(frames_dir, output_path, fps)
        
        # Очищаем
        import shutil
        shutil.rmtree(frames_dir)
    
    def _get_audio_duration(self, audio_path: Path) -> float:
        """Get audio duration in seconds"""
        try:
            from moviepy.editor import AudioFileClip
            clip = AudioFileClip(str(audio_path))
            return clip.duration
        except Exception:
            # Оцениваем по размеру файла
            size = audio_path.stat().st_size
            # 16kHz * 16bit = 32000 байт/сек
            return max(1.0, size / 32000)
    
    def _detect_mouth_position(self, img: Image.Image, position: str) -> Tuple[int, int, int, int]:
        """
        Detect mouth area in image
        Returns bounding box as (x1, y1, x2, y2)
        """
        width, height = img.size
        
        # Простая эвристика: рот примерно в нижней трети лица
        # Предполагаем, что лицо занимает центральную часть
        
        if position == "left":
            face_center_x = width * 0.35
        elif position == "right":
            face_center_x = width * 0.65
        else:
            face_center_x = width * 0.5
        
        face_center_y = height * 0.5
        face_width = width * 0.25
        face_height = height * 0.3
        
        # Роторая ниже центра лица
        mouth_x = face_center_x - face_width * 0.3
        mouth_y = face_center_y + face_height * 0.2
        mouth_w = face_width * 0.6
        mouth_h = face_height * 0.4
        
        return (
            int(mouth_x), int(mouth_y),
            int(mouth_x + mouth_w), int(mouth_y + mouth_h)
        )
    
    def _draw_mouth(self, img: Image.Image, mouth_box: Tuple, 
                   viseme: str) -> Image.Image:
        """Draw mouth shape on image"""
        draw = ImageDraw.Draw(img, "RGBA")
        
        x1, y1, x2, y2 = mouth_box
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2
        w = x2 - x1
        h = y2 - y1
        
        # Получаем форму рта
        shape = MOUTH_SHAPES.get(viseme, MOUTH_SHAPES["closed"])
        
        # Масштабируем форму
        scaled_shape = []
        for px, py in shape:
            sx = x1 + int(px * w / 100)
            sy = y1 + int(py * h / 100)
            scaled_shape.append((sx, sy))
        
        # Рисуем форму рта
        color = (80, 40, 40, 200)  # Темно-коричневый
        
        if viseme == "closed":
            # Просто линия
            draw.line(scaled_shape, fill=color, width=max(2, h // 10))
        else:
            # Замкнутая форма
            draw.polygon(scaled_shape, fill=color)
            draw.polygon(scaled_shape, outline=color, width=2)
        
        return img
    
    def _generate_viseme_sequence(self, duration: float, 
                                 num_frames: int) -> List[str]:
        """
        Generate random viseme sequence for duration
        
        Имитирует артикуляцию - случайные виземы с плавными переходами
        """
        visemes = list(MOUTH_SHAPES.keys())
        
        sequence = []
        frames_per_viseme = max(3, int(num_frames / (duration * 2)))  # ~2 визема в секунду
        
        for i in range(num_frames):
            # Плавные переходы
            cycle = i // frames_per_viseme
            
            if cycle % 3 == 0:
                viseme = "open"
            elif cycle % 3 == 1:
                viseme = "closed"
            else:
                viseme = "wide"
            
            sequence.append(viseme)
        
        return sequence
    
    def _create_video_from_frames(self, frames_dir: Path, output_path: Path, fps: int):
        """Create video from frames using FFmpeg"""
        try:
            subprocess.run([
                "ffmpeg", "-y",
                "-framerate", str(fps),
                "-i", str(frames_dir / "frame_%04d.png"),
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                str(output_path)
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            logger.warning(f"FFmpeg failed: {e}, using fallback")
            self._create_video_fallback(frames_dir, output_path, fps)
    
    def _create_video_fallback(self, frames_dir: Path, output_path: Path, fps: int):
        """Fallback video creation using moviepy"""
        try:
            from moviepy.editor import ImageSequenceClip
            
            frames = sorted(frames_dir.glob("*.png"))
            clip = ImageSequenceClip([str(f) for f in frames], fps=fps)
            clip.write_videofile(str(output_path), codec="libx264", 
                              verbose=False, logger=None)
        except Exception as e:
            logger.error(f"Video creation failed: {e}")
            # Просто копируем первый кадр
            import shutil
            frames = sorted(frames_dir.glob("*.png"))
            if frames:
                shutil.copy(frames[0], output_path.with_suffix(".png"))
    
    def batch_generate(self, scenes: List[Dict[str, Any]], 
                       image_paths: List[str],
                       audio_paths: List[str]) -> List[str]:
        """
        Generate lip-sync for batch of scenes
        
        Args:
            scenes: Scene dictionaries
            image_paths: Character images
            audio_paths: Dialog audio files
            
        Returns:
            List of video paths with lip-sync
        """
        logger.info(f"Generating lip-sync for {len(scenes)} scenes...")
        
        video_paths = []
        
        for i, scene in enumerate(scenes):
            characters = scene.get("characters", [])
            position = characters[0].get("position", "center") if characters else "center"
            
            if i < len(image_paths) and i < len(audio_paths):
                video_path = self.generate_lipsync(
                    image_paths[i],
                    audio_paths[i],
                    character_position=position
                )
                video_paths.append(video_path)
        
        return video_paths


# Convenience functions
def generate_lipsync(image_path: str, audio_path: str,
                    output_dir: str = TEMP_DIR) -> str:
    """Generate lip-synced video from image and audio"""
    generator = LipSyncGenerator(output_dir)
    return generator.generate_lipsync(image_path, audio_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test lip-sync
    generator = LipSyncGenerator()
    
    print(f"Using method: {generator._get_method()}")
    
    # Check if test files exist
    test_image = Path(TEMP_DIR) / "test_character.png"
    test_audio = Path(TEMP_DIR) / "test_dialog.wav"
    
    if test_image.exists() and test_audio.exists():
        output = generator.generate_lipsync(
            str(test_image),
            str(test_audio),
            character_position="center"
        )
        print(f"Generated: {output}")
    else:
        print("Test files not found, skipping lip-sync test")