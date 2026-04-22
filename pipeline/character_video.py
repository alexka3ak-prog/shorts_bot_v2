"""
Character Video Generator - Enhanced video generation with character animation

Creates video with:
- Character positioning in frame
- Dialog audio
- Burned-in subtitles
- FFmpeg processing
"""
import os
import json
import logging
import subprocess
from typing import List, Dict, Any
from pathlib import Path
from PIL import Image

try:
    from config import TEMP_DIR, OUTPUT_DIR, SCENE_DURATION, FFMPEG_PATH
except ImportError:
    TEMP_DIR = "/workspace/project/shorts_bot_v2/output/temp"
    OUTPUT_DIR = "/workspace/project/shorts_bot_v2/output"
    SCENE_DURATION = 4.0
    FFMPEG_PATH = r"C:\ai-project\ffmpeg\bin\ffmpeg.exe"

logger = logging.getLogger(__name__)


class CharacterVideoGenerator:
    """Generate video with characters and dialogs"""
    
    def __init__(self, output_dir: str = TEMP_DIR):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.ffmpeg_path = Path(FFMPEG_PATH)
        self.has_ffmpeg = self._check_ffmpeg()
        logger.info(f"CharacterVideoGenerator: FFmpeg={self.has_ffmpeg}")
    
    def _check_ffmpeg(self) -> bool:
        try:
            subprocess.run([str(self.ffmpeg_path), "-version"], capture_output=True, timeout=5)
            return True
        except:
            return False
    
    def generate_scene_video(self, 
                    scene: Dict[str, Any],
                    image_path: str,
                    dialog_audio_paths: List[str] = None,
                    output_path: str = None) -> str:
        """Generate scene video with audio and subtitles"""
        if output_path is None:
            scene_id = scene.get("scene_id", 1)
            output_path = self.temp_dir / f"scene_{scene_id:03d}_video.mp4"
        else:
            output_path = Path(output_path)
        
        duration = scene.get("duration", SCENE_DURATION)
        dialogs = scene.get("dialogs", [])
        
        # Generate video from image
        if self.has_ffmpeg:
            self._generate_ffmpeg(image_path, output_path, duration, dialog_audio_paths)
        else:
            self._generate_fallback(image_path, output_path, duration)
        
        # Add subtitles
        if dialogs and self.has_ffmpeg:
            video_with_subs = str(output_path).replace(".mp4", "_sub.mp4")
            self.add_subtitles(str(output_path), video_with_subs, dialogs, duration)
            if os.path.exists(video_with_subs):
                os.replace(video_with_subs, str(output_path))
        
        return str(output_path)
    
    def _generate_ffmpeg(self, image_path: str, output_path: Path,
                   duration: float, audio_paths: List = None):
        """Generate video using FFmpeg"""
        if audio_paths and any(Path(a).exists() for a in audio_paths if a):
            valid_audio = [a for a in audio_paths if a and Path(a).exists()]
            if valid_audio:
                # Combine audio files
                audio_list = self.temp_dir / "audio_list.txt"
                with open(audio_list, "w") as f:
                    for a in valid_audio:
                        f.write(f"file '{a}'\n")
                
                combined = self.temp_dir / "combined_audio.mp3"
                subprocess.run([
                    str(self.ffmpeg_path), "-y", "-f", "concat", "-safe", "0",
                    "-i", str(audio_list), "-c", "copy", str(combined)
                ], capture_output=True)
                
                subprocess.run([
                    str(self.ffmpeg_path), "-y",
                    "-loop", "1", "-i", image_path,
                    "-i", str(combined),
                    "-c:v", "libx264", "-tune", "stillimage",
                    "-preset", "fast", "-crf", "18",
                    "-t", str(duration), "-r", "30",
                    "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "128k",
                    "-shortest", str(output_path)
                ], capture_output=True)
                return
        
        # No audio
        subprocess.run([
            str(self.ffmpeg_path), "-y",
            "-loop", "1", "-i", image_path,
            "-c:v", "libx264", "-tune", "stillimage",
            "-preset", "fast", "-crf", "18",
            "-t", str(duration), "-r", "30",
            "-pix_fmt", "yuv420p", str(output_path)
        ], capture_output=True)
    
    def _generate_fallback(self, image_path: str, output_path: Path, duration: float):
        import shutil
        output_path = output_path.with_suffix(".png")
        shutil.copy(image_path, output_path)
    
    def add_subtitles(self, video_path: str, output_path: str,
                    dialogs: List[Dict], duration: float) -> str:
        """Add burned-in subtitles"""
        if not self.has_ffmpeg:
            return video_path
        
        filters = []
        for dialog in dialogs:
            text = dialog.get("text", "")
            start = dialog.get("start_time", 0)
            character = dialog.get("character", "")
            
            if not text:
                continue
            
            text_len = len(text)
            end = min(start + max(2.0, text_len / 3.0), duration)
            
            escaped = text.replace("'", "\\'").replace(":", "\\:")
            display = f"{character}: {escaped}" if character else escaped
            
            filters.append(
                f"drawtext=text='{display}':"
                f"fontsize=24:fontcolor=white:"
                f"x=(w-text_w)/2:y=h-60:"
                f"borderw=2:bordercolor=black:"
                f"enable='between(t,{start},{end})'"
            )
        
        if not filters:
            return video_path
        
        try:
            subprocess.run([
                str(self.ffmpeg_path), "-y", "-i", video_path,
                "-vf", ",".join(filters),
                "-c:a", "copy", output_path
            ], capture_output=True, check=True)
            return output_path
        except Exception as e:
            logger.warning(f"Subtitle failed: {e}")
            return video_path


def generate_character_video(scene: Dict, image_path: str,
                        audio_paths: List[str] = None,
                        output_dir: str = TEMP_DIR) -> str:
    generator = CharacterVideoGenerator(output_dir)
    return generator.generate_scene_video(scene, image_path, audio_paths)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    gen = CharacterVideoGenerator()
    print(f"FFmpeg: {gen.has_ffmpeg}")