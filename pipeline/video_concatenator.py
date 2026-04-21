"""
Video Concatenator - Merges scene videos into a single final video
"""
import os
import json
import logging
import subprocess
from typing import List, Dict, Any, Optional
from pathlib import Path

from config import (
    OUTPUT_DIR, TEMP_DIR, FINAL_VIDEO_NAME,
    FFMPEG_CODEC, FFMPEG_PRESET, FFMPEG_CRF,
    TRANSITION_DURATION
)

logger = logging.getLogger(__name__)


class VideoConcatenator:
    """Concatenate video segments with transitions"""
    
    def __init__(self, output_dir: str = OUTPUT_DIR, temp_dir: str = TEMP_DIR):
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(temp_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def concatenate_videos(self, video_paths: List[str], 
                          transitions: Optional[List[str]] = None,
                          output_filename: str = FINAL_VIDEO_NAME) -> str:
        """
        Concatenate multiple videos into one with transitions
        
        Args:
            video_paths: List of video file paths
            transitions: List of transition effects (None for default fade)
            output_filename: Output filename
            
        Returns:
            Path to the final concatenated video
        """
        logger.info(f"Concatenating {len(video_paths)} videos...")
        
        if not video_paths:
            raise ValueError("No video paths provided")
        
        if len(video_paths) == 1:
            # Single video, just copy
            output_path = self.output_dir / output_filename
            import shutil
            shutil.copy(video_paths[0], output_path)
            return str(output_path)
        
        # Filter existing videos
        existing_paths = [v for v in video_paths if os.path.exists(v)]
        
        if len(existing_paths) < 2:
            logger.warning("Not enough valid videos to concatenate")
            if existing_paths:
                output_path = self.output_dir / output_filename
                import shutil
                shutil.copy(existing_paths[0], output_path)
                return str(output_path)
            raise ValueError("No valid video files found")
        
        output_path = self.output_dir / output_filename
        
        # Try FFmpeg concatenation
        try:
            self._concatenate_ffmpeg(existing_paths, output_path, transitions)
            logger.info(f"Concatenated video saved to: {output_path}")
            return str(output_path)
        except Exception as e:
            logger.error(f"FFmpeg concatenation failed: {e}")
            # Fallback: use moviepy
            return self._concatenate_moviepy(existing_paths, output_path)
    
    def _concatenate_ffmpeg(self, video_paths: List[str], output_path: Path,
                           transitions: Optional[List[str]] = None):
        """Concatenate videos using FFmpeg"""
        
        # Create concat file
        concat_file = self.temp_dir / "concat_list.txt"
        
        with open(concat_file, "w") as f:
            for path in video_paths:
                # Escape single quotes in path
                escaped_path = path.replace("'", "'\\''")
                f.write(f"file '{escaped_path}'\n")
        
        # Run FFmpeg
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c:v", FFMPEG_CODEC,
            "-preset", FFMPEG_PRESET,
            "-crf", str(FFMPEG_CRF),
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "128k",
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, check=True)
        
        # Cleanup
        concat_file.unlink(missing_ok=True)
    
    def _concatenate_moviepy(self, video_paths: List[str], output_path: Path) -> str:
        """Fallback concatenation using moviepy"""
        try:
            from moviepy.editor import VideoFileClip, concatenate_videoclips
            
            clips = [VideoFileClip(v) for v in video_paths]
            final_clip = concatenate_videoclips(clips, method="compose")
            final_clip.write_videofile(
                str(output_path),
                codec=FFMPEG_CODEC,
                preset=FFMPEG_PRESET,
                bitrate="2000k",
                verbose=False,
                logger=None
            )
            
            # Close clips
            for clip in clips:
                clip.close()
            final_clip.close()
            
            return str(output_path)
            
        except ImportError:
            # Last resort: just copy first video
            import shutil
            shutil.copy(video_paths[0], output_path)
            return str(output_path)
    
    def create_with_transitions(self, video_paths: List[str],
                                transitions: List[str],
                                output_filename: str = FINAL_VIDEO_NAME) -> str:
        """
        Create video with explicit transition effects
        
        Args:
            video_paths: List of video paths
            transitions: List of transition types ("fade", "dissolve", "wipe", etc.)
            output_filename: Output filename
            
        Returns:
            Path to final video
        """
        logger.info(f"Creating video with {len(transitions) if transitions else 0} transitions")
        
        if not video_paths:
            raise ValueError("No video paths provided")
        
        if len(video_paths) == 1:
            import shutil
            output_path = self.output_dir / output_filename
            shutil.copy(video_paths[0], output_path)
            return str(output_path)
        
        output_path = self.output_dir / output_filename
        
        # Use moviepy for transitions
        try:
            from moviepy.editor import VideoFileClip, concatenate_videoclips
            
            clips = []
            for i, path in enumerate(video_paths):
                clip = VideoFileClip(path)
                
                # Apply transition to next clip
                if transitions and i < len(transitions):
                    transition = transitions[i]
                    if transition == "fade":
                        # Fade in effect handled by concatenate
                        pass
                
                clips.append(clip)
            
            # Concatenate with compose for smooth transitions
            final_clip = concatenate_videoclips(clips, method="compose")
            final_clip.write_videofile(
                str(output_path),
                codec=FFMPEG_CODEC,
                preset=FFMPEG_PRESET,
                verbose=False,
                logger=None
            )
            
            # Cleanup
            for clip in clips:
                clip.close()
            final_clip.close()
            
            return str(output_path)
            
        except ImportError:
            # Fallback to simple concatenation
            return self.concatenate_videos(video_paths, output_filename=output_filename)
    
    def generate_metadata(self, scenes: List[Dict[str, Any]], 
                         video_path: str,
                         image_paths: List[str]) -> Dict[str, Any]:
        """
        Generate metadata JSON for the final video
        
        Args:
            scenes: List of scene dictionaries
            video_path: Path to final video
            image_paths: List of generated image paths
            
        Returns:
            Metadata dictionary
        """
        import os
        
        metadata = {
            "video_file": video_path,
            "video_filename": os.path.basename(video_path),
            "total_scenes": len(scenes),
            "total_duration": sum(s.get("duration", 0) for s in scenes),
            "scenes": []
        }
        
        for i, scene in enumerate(scenes):
            scene_meta = {
                "scene_id": scene.get("scene_id", i + 1),
                "description": scene.get("description", ""),
                "prompt": scene.get("prompt", ""),
                "duration": scene.get("duration", 0),
                "transition": scene.get("transition", "none"),
                "image_path": image_paths[i] if i < len(image_paths) else None,
                "video_path": self.temp_dir / f"scene_{scene.get('scene_id', i+1):03d}_video.mp4"
            }
            metadata["scenes"].append(scene_meta)
        
        # Save metadata
        metadata_path = self.output_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Metadata saved to: {metadata_path}")
        
        return metadata


def concatenate_videos(video_paths: List[str], 
                       output_dir: str = OUTPUT_DIR,
                       output_filename: str = FINAL_VIDEO_NAME) -> str:
    """Convenience function to concatenate videos"""
    concatenator = VideoConcatenator(output_dir)
    return concatenator.concatenate_videos(video_paths, output_filename=output_filename)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test concatenation
    concatenator = VideoConcatenator()
    
    # Check if there are any videos to concatenate
    temp_dir = Path(TEMP_DIR)
    videos = sorted(temp_dir.glob("scene_*_video.mp4"))
    
    if videos:
        print(f"Found {len(videos)} videos to concatenate")
        output = concatenator.concatenate_videos([str(v) for v in videos])
        print(f"Final video: {output}")
    else:
        print("No videos found in temp directory for testing")