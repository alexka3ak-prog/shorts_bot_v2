"""
AutoVideo Pipeline - Automated video generation system
"""

from .script_generator import (
    generate_script, 
    validate_script,
    extract_characters_from_script,
    extract_all_dialogs
)
from .image_generator import ImageGenerator, generate_image
from .video_generator import VideoGenerator, generate_video
from .video_concatenator import VideoConcatenator, concatenate_videos
from .comfyui_video import ComfyUIVideoGenerator, generate_video_via_comfyui
from .ltx_video import LTXVideoGenerator, generate_video
from .simple_video import SimpleVideoGenerator, generate_simple_video
from .tts_generator import TTSGenerator, generate_speech
from .lipsync_generator import LipSyncGenerator, generate_lipsync
from .character_video import CharacterVideoGenerator, generate_character_video
from .ltx_video import LTXVideoGenerator, generate_video

__all__ = [
    # Script generation
    "generate_script",
    "validate_script", 
    "extract_characters_from_script",
    "extract_all_dialogs",
    # Image generation
    "ImageGenerator",
    "generate_image",
    # Video generation
    "VideoGenerator", 
    "generate_video",
    "ComfyUIVideoGenerator",
    "generate_video_via_comfyui",
    "SimpleVideoGenerator",
    "generate_simple_video",
    "LTXVideoGenerator",  # NEW - LTX 2.3
    "CharacterVideoGenerator", 
    "generate_character_video",
    # Video composition
    "VideoConcatenator",
    "concatenate_videos",
    # TTS / Audio
    "TTSGenerator",
    "generate_speech",
    # Lip-sync
    "LipSyncGenerator",
    "generate_lipsync",
]