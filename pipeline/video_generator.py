"""
Video Generator - Uses LTX 2.3 to generate videos from images

Локальный запуск:
- Без GPU используется базовый аниматор (zoom, pan эффекты)
- С GPU можно использовать модели типа AnimateDiff или zeroscope
"""
import os
import json
import logging
import time
import requests
from typing import List, Dict, Any, Optional
from pathlib import Path
import subprocess

from config import (
    LTX_API_KEY, LTX_API_URL,
    SCENE_DURATION, OUTPUT_DIR, TEMP_DIR,
    USE_LOCAL_LTX
)

logger = logging.getLogger(__name__)


class VideoGenerator:
    """Generate videos using LTX 2.3"""
    
    def __init__(self, output_dir: str = TEMP_DIR):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.api_key = LTX_API_KEY
        self.api_url = LTX_API_URL
    
    def generate_video(self, image_path: str, prompt: str, scene_id: int, 
                       duration: float = SCENE_DURATION) -> str:
        """
        Generate a video from an image using LTX 2.3
        
        Args:
            image_path: Path to the source image
            prompt: Motion/video generation prompt
            scene_id: Scene identifier
            duration: Video duration in seconds
            
        Returns:
            Path to the generated video
        """
        logger.info(f"Generating video for scene {scene_id}: {prompt[:50]}...")
        
        output_path = self.output_dir / f"scene_{scene_id:03d}_video.mp4"
        
        # Try API first, fallback to local generation
        if self.api_key:
            try:
                self._generate_via_api(image_path, prompt, output_path, duration)
                logger.info(f"Generated video via API: {output_path}")
                return str(output_path)
            except Exception as e:
                logger.warning(f"LTX API generation failed: {e}, using local fallback")
        
        # Fallback: Generate video locally
        self._generate_local(image_path, prompt, output_path, duration)
        logger.info(f"Generated local video: {output_path}")
        return str(output_path)
    
    def _generate_via_api(self, image_path: str, prompt: str, 
                          output_path: Path, duration: float):
        """Generate video using LTX 2.3 API"""
        # LTX API typically uses multipart/form-data
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        with open(image_path, "rb") as img_file:
            files = {
                "image": img_file,
            }
            data = {
                "prompt": prompt,
                "duration": int(duration),
                "fps": 24,
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                files=files,
                data=data,
                timeout=300
            )
        
        response.raise_for_status()
        
        # Save the video (API returns video content)
        with open(output_path, "wb") as f:
            f.write(response.content)
    
    def _generate_local(self, image_path: str, prompt: str,
                        output_path: Path, duration: float):
        """
        Generate video locally using FFmpeg and image processing
        In production, this would use a local LTX model or alternative
        """
        from PIL import Image
        import numpy as np
        
        # Load the image
        img = Image.open(image_path)
        img = img.convert("RGB")
        
        # Get dimensions
        width, height = img.size
        
        # Generate frames with subtle animation
        fps = 24
        total_frames = int(duration * fps)
        
        # Create output directory for frames
        frames_dir = output_path.parent / f"frames_{output_path.stem}"
        frames_dir.mkdir(exist_ok=True)
        
        # Generate animated frames
        np.random.seed(hash(prompt) % (2**32))
        
        for frame_idx in range(total_frames):
            frame = img.copy()
            pixels = np.array(frame)
            
            # Add subtle motion/pulse effect
            progress = frame_idx / total_frames
            
            # Subtle brightness variation
            brightness = 1.0 + 0.05 * np.sin(progress * 2 * np.pi)
            pixels = np.clip(pixels * brightness, 0, 255).astype(np.uint8)
            
            # Subtle zoom
            zoom_factor = 1.0 + 0.02 * np.sin(progress * np.pi)
            
            if zoom_factor != 1.0:
                h, w = pixels.shape[:2]
                new_h, new_w = int(h * zoom_factor), int(w * zoom_factor)
                
                from PIL import Image as PILImage
                zoomed = PILImage.fromarray(pixels)
                zoomed = zoomed.resize((new_w, new_h), PILImage.LANCZOS)
                
                # Crop or pad to original size
                if zoom_factor > 1:
                    # Center crop
                    start_h = (new_h - h) // 2
                    start_w = (new_w - w) // 2
                    pixels = np.array(zoomed)[start_h:start_h+h, start_w:start_w+w]
                else:
                    # Pad
                    new_img = np.zeros((h, w, 3), dtype=np.uint8)
                    start_h = (h - new_h) // 2
                    start_w = (w - new_w) // 2
                    new_img[start_h:start_h+new_h, start_w:start_w+new_w] = np.array(zoomed)
                    pixels = new_img
            
            # Add subtle color shift
            shift = int(5 * np.sin(progress * np.pi))
            if shift > 0:
                pixels[:, :, 0] = np.clip(pixels[:, :, 0] + shift, 0, 255)
            
            # Save frame
            frame_img = Image.fromarray(pixels)
            frame_img.save(frames_dir / f"frame_{frame_idx:04d}.png")
        
        # Use FFmpeg to create video from frames
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-framerate", str(fps),
            "-i", str(frames_dir / "frame_%04d.png"),
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            str(output_path)
        ]
        
        try:
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            logger.warning(f"FFmpeg failed: {e.stderr.decode() if e.stderr else ''}")
            # Create a simple video without FFmpeg
            self._create_simple_video(frames_dir, output_path, fps)
        
        # Cleanup frames
        import shutil
        shutil.rmtree(frames_dir)
    
    def _create_simple_video(self, frames_dir: Path, output_path: Path, fps: int):
        """Create video using moviepy as fallback"""
        try:
            from moviepy.editor import ImageSequenceClip
            
            frames = sorted(frames_dir.glob("*.png"))
            clip = ImageSequenceClip([str(f) for f in frames], fps=fps)
            clip.write_videofile(str(output_path), codec="libx264", 
                               verbose=False, logger=None)
        except ImportError:
            # Last resort: just copy the first frame as video placeholder
            frames = sorted(frames_dir.glob("*.png"))
            if frames:
                import shutil
                shutil.copy(frames[0], output_path.with_suffix(".png"))
                logger.warning("Created placeholder, no video generation available")
    
    def generate_all_videos(self, scenes: List[Dict[str, Any]], 
                            image_paths: List[str]) -> List[str]:
        """
        Generate videos for all scenes
        
        Args:
            scenes: List of scene dictionaries
            image_paths: List of corresponding image paths
            
        Returns:
            List of video file paths
        """
        logger.info(f"Generating {len(scenes)} videos...")
        
        video_paths = []
        for i, (scene, image_path) in enumerate(zip(scenes, image_paths)):
            # Validate and fix scene
            if isinstance(scene, str):
                scene = {"scene_id": i+1, "prompt": scene}
            
            scene_id = scene.get("scene_id", i+1)
            if scene_id == 0:
                scene_id = i + 1
                
            prompt = scene.get("prompt", "")
            duration = scene.get("duration", SCENE_DURATION)
            
            video_path = self.generate_video(image_path, prompt, scene_id, duration)
            video_paths.append(video_path)
        
        logger.info(f"Generated {len(video_paths)} videos")
        return video_paths


def generate_video(image_path: str, prompt: str, scene_id: int,
                   output_dir: str = TEMP_DIR, duration: float = SCENE_DURATION) -> str:
    """Convenience function to generate a single video"""
    generator = VideoGenerator(output_dir)
    return generator.generate_video(image_path, prompt, scene_id, duration)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test video generation
    generator = VideoGenerator()
    
    # Use placeholder image path
    test_image = "/workspace/project/output/temp/scene_001_image.png"
    
    if os.path.exists(test_image):
        video_path = generator.generate_video(
            test_image, 
            "Slow camera movement, cinematic lighting",
            scene_id=1,
            duration=3.0
        )
        print(f"Generated video: {video_path}")
    else:
        print("Test image not found, skipping video generation test")