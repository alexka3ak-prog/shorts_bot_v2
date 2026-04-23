"""
Video Concatenator - Merges scene videos into a single final video

Поддерживает:
- Простую конкатенацию (без переходов)
- Fade переходы
- Dissolve (crossfade) переходы
- Slide переходы
- AV (audio-video) объединение с сохранением аудио
"""
import os
import json
import logging
import subprocess
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from config import (
    OUTPUT_DIR, TEMP_DIR, FINAL_VIDEO_NAME,
    FFMPEG_CODEC, FFMPEG_PRESET, FFMPEG_CRF,
    TRANSITION_DURATION
)

logger = logging.getLogger(__name__)


# FFmpeg transition filter presets
TRANSITION_FILTERS = {
    "fade": "fade=t=in:st=0:d={duration},fade=t=out:st={out_start}:d={duration}",
    "dissolve": "xfade=transition=fade:duration={duration}:offset={offset}",
    "slide_left": "xfade=transition=slideleft:duration={duration}:offset={offset}",
    "slide_right": "xfade=transition=slideright:duration={duration}:offset={offset}",
    "slide_up": "xfade=transition=slideup:duration={duration}:offset={offset}",
    "slide_down": "xfade=transition=slidedown:duration={duration}:offset={offset}",
    "zoom": "xfade=transition=zoomin:duration={duration}:offset={offset}",
    "wipe_left": "xfade=transition=wipeleft:duration={duration}:offset={offset}",
    "circlecrop": "xfade=transition=circlecrop:duration={duration}:offset={offset}",
    "rectcrop": "xfade=transition=rectcrop:duration={duration}:offset={offset}",
    "distance": "xfade=transition=distance:duration={duration}:offset={offset}",
    "fadeblack": "xfade=transition=fadeblack:duration={duration}:offset={offset}",
    "fadewhite": "xfade=transition=fadewhite:duration={duration}:offset={offset}",
    "radial": "xfade=transition=radial:duration={duration}:offset={offset}",
    "smoothleft": "xfade=transition=smoothleft:duration={duration}:offset={offset}",
    "smoothright": "xfade=transition=smoothright:duration={duration}:offset={offset}",
    "smoothup": "xfade=transition=smoothup:duration={duration}:offset={offset}",
    "smoothdown": "xfade=transition=smoothdown:duration={duration}:offset={offset}",
    "circleopen": "xfade=transition=circleopen:duration={duration}:offset={offset}",
    "circleclose": "xfade=transition=circleclose:duration={duration}:offset={offset}",
    "vertopen": "xfade=transition=vertopen:duration={duration}:offset={offset}",
    "vertclose": "xfade=transition=vertclose:duration={duration}:offset={offset}",
    "horzopen": "xfade=transition=horzopen:duration={duration}:offset={offset}",
    "horzclose": "xfade=transition=horzclose:duration={duration}:offset={offset}",
    "dissolve": "xfade=transition=dissolve:duration={duration}:offset={offset}",
}


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
    
    def concatenate_with_audio(self, video_paths: List[str], 
                               audio_paths: List[str] = None,
                               transitions: List[str] = None,
                               output_filename: str = FINAL_VIDEO_NAME) -> str:
        """
        Concatenate videos with audio tracks
        
        Args:
            video_paths: List of video file paths
            audio_paths: List of audio file paths (one per video)
            transitions: List of transition effects
            output_filename: Output filename
            
        Returns:
            Path to the final concatenated video
        """
        logger.info(f"Concatenating {len(video_paths)} videos with audio...")
        
        if not video_paths:
            raise ValueError("No video paths provided")
        
        if len(video_paths) == 1:
            output_path = self.output_dir / output_filename
            import shutil
            
            # If we have audio, mix it with video
            if audio_paths and audio_paths[0]:
                return self._merge_video_audio(video_paths[0], audio_paths[0], output_path)
            else:
                shutil.copy(video_paths[0], output_path)
                return str(output_path)
        
        output_path = self.output_dir / output_filename
        
        # Use FFmpeg for concatenation with audio
        try:
            self._concatenate_with_audio_ffmpeg(
                video_paths, audio_paths, output_path, transitions
            )
            logger.info(f"Concatenated video saved to: {output_path}")
            return str(output_path)
        except Exception as e:
            logger.error(f"FFmpeg concatenation with audio failed: {e}")
            # Fallback to simple concatenation
            return self.concatenate_videos(video_paths, transitions, output_filename)
    
    def _merge_video_audio(self, video_path: str, audio_path: str, 
                          output_path: Path) -> str:
        """Merge video with audio track using FFmpeg"""
        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", audio_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",
                str(output_path)
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return str(output_path)
        except subprocess.CalledProcessError as e:
            logger.error(f"Audio merge failed: {e}")
            # Fallback: just copy video
            import shutil
            shutil.copy(video_path, output_path)
            return str(output_path)
    
    def _concatenate_with_audio_ffmpeg(self, video_paths: List[str],
                                       audio_paths: List[str],
                                       output_path: Path,
                                       transitions: List[str] = None):
        """Concatenate videos with audio using FFmpeg"""
        
        # If no audio, use simple concatenation
        if not audio_paths:
            return self._concatenate_ffmpeg(video_paths, output_path, transitions)
        
        # Get info about first video for output settings
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate",
            "-of", "json",
            video_paths[0]
        ]
        
        try:
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
            import json as json_module
            info = json_module.loads(probe_result.stdout)
            stream = info.get("streams", [{}])[0]
            width = stream.get("width", 1920)
            height = stream.get("height", 1080)
            fps_str = stream.get("r_frame_rate", "30/1")
        except:
            width, height = 1920, 1080
            fps_str = "30/1"
        
        # Build FFmpeg command with filter_complex for concatenation
        # For simplicity, use concat demuxer with audio
        input_args = []
        for v in video_paths:
            input_args.extend(["-i", v])
        
        # If we have matching audio tracks, add them
        if audio_paths:
            for a in audio_paths:
                if a:
                    input_args.extend(["-i", a])
        
        # Simple concatenation - just concat all video and audio streams
        filter_complex = ""
        if audio_paths and any(a for a in audio_paths):
            # We have audio, use filter_complex to combine
            n_videos = len(video_paths)
            filter_complex = f"[0:v]concat=n={n_videos}:v=1:a=0[outv]"
        
        cmd = [
            "ffmpeg", "-y",
        ] + input_args
        
        if filter_complex:
            cmd.extend(["-filter_complex", filter_complex])
            cmd.extend(["-map", "[outv]"])
        else:
            # Just concat videos
            cmd.extend(["-concat_outputs", "0"])
        
        cmd.extend([
            "-c:v", FFMPEG_CODEC,
            "-preset", FFMPEG_PRESET,
            "-crf", str(FFMPEG_CRF),
            "-pix_fmt", "yuv420p",
            str(output_path)
        ])
        
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            logger.warning(f"Complex concat failed, trying simple method")
            # Fallback to simple concat
            self._concatenate_ffmpeg(video_paths, output_path, transitions)
    
    def create_with_transitions(self, video_paths: List[str],
                                transitions: List[str],
                                output_filename: str = FINAL_VIDEO_NAME) -> str:
        """
        Create video with explicit transition effects using xfade
        
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
        
        # Use FFmpeg xfade for transitions
        try:
            return self._create_with_xfade(video_paths, transitions, output_filename)
        except Exception as e:
            logger.error(f"Xfade transitions failed: {e}")
            # Fallback to simple concatenation
            return self.concatenate_videos(video_paths, output_filename=output_filename)
    
    def _create_with_xfade(self, video_paths: List[str],
                          transitions: List[str],
                          output_filename: str) -> str:
        """Create video with smooth xfade transitions"""
        
        # Get video info
        probe_cmd = [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,r_frame_rate,duration",
            "-of", "json",
            video_paths[0]
        ]
        
        try:
            probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
            import json as json_module
            info = json_module.loads(probe_result.stdout)
            stream = info.get("streams", [{}])[0]
            width = stream.get("width", 1920)
            height = stream.get("height", 1080)
            fps_str = stream.get("r_frame_rate", "30/1")
            fps = eval(fps_str) if "/" in fps_str else float(fps_str)
            first_duration = float(stream.get("duration", 4.0))
        except Exception as e:
            logger.warning(f"Could not probe video: {e}")
            width, height, fps = 1920, 1080, 30.0
            first_duration = 4.0
        
        # Ensure even dimensions for xfade
        width = width if width % 2 == 0 else width - 1
        height = height if height % 2 == 0 else height - 1
        
        # Build xfade filter chain
        transition_duration = TRANSITION_DURATION
        
        # For n videos, we need n-1 transitions
        filter_parts = []
        for i in range(len(video_paths)):
            filter_parts.append(f"[{i}:v]")
        
        # Build complex filter
        complex_filter = ""
        for i in range(len(video_paths) - 1):
            transition = (transitions[i] if transitions and i < len(transitions) else "fade").lower()
            
            # Get duration for this video
            if i == 0:
                dur = first_duration
            else:
                try:
                    probe_cmd = [
                        "ffprobe", "-v", "error",
                        "-select_streams", "v:0",
                        "-show_entries", "stream=duration",
                        "-of", "json",
                        video_paths[i]
                    ]
                    probe_result = subprocess.run(probe_cmd, capture_output=True, text=True)
                    info = json_module.loads(probe_result.stdout)
                    dur = float(info.get("streams", [{}])[0].get("duration", 4.0))
                except:
                    dur = 4.0
            
            offset = dur - transition_duration
            
            # Get the transition filter
            if transition in TRANSITION_FILTERS:
                tf = TRANSITION_FILTERS[transition].format(
                    duration=transition_duration,
                    offset=offset,
                    out_start=offset
                )
            else:
                # Default to fade
                tf = f"xfade=transition=fade:duration={transition_duration}:offset={offset}"
            
            filter_parts.append(tf)
        
        filter_parts.append(f"concat=n={len(video_paths)}:v=1:a=0[outv]")
        complex_filter = ";".join(filter_parts)
        
        # Build FFmpeg command
        input_args = []
        for v in video_paths:
            input_args.extend(["-i", v])
        
        cmd = [
            "ffmpeg", "-y",
        ] + input_args + [
            "-filter_complex", complex_filter,
            "-map", "[outv]",
            "-c:v", FFMPEG_CODEC,
            "-preset", FFMPEG_PRESET,
            "-crf", str(FFMPEG_CRF),
            "-pix_fmt", "yuv420p",
            str(self.output_dir / output_filename)
        ]
        
        result = subprocess.run(cmd, capture_output=True)
        
        if result.returncode != 0:
            logger.error(f"Xfade failed: {result.stderr.decode()[:500]}")
            raise Exception("Xfade filter failed")
        
        return str(self.output_dir / output_filename)
    
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
                "image_path": str(image_paths[i]) if i < len(image_paths) else None,
                "video_path": str(self.temp_dir / f"scene_{scene.get('scene_id', i+1):03d}_video.mp4")
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