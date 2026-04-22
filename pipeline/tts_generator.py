"""
TTS Generator - LOCAL Piper TTS
"""
import os
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from config import USE_LOCAL_TTS, PIPER_PATH, PIPER_MODEL, TEMP_DIR
except ImportError:
    USE_LOCAL_TTS = True
    PIPER_PATH = r"C:\ai-project\piper\piper.exe"
    PIPER_MODEL = r"C:\ai-project\piper\en_US-lessac-piper.onnx"
    TEMP_DIR = "/workspace/project/shorts_bot_v2/output/temp"

logger = logging.getLogger(__name__)


class TTSGenerator:
    def __init__(self, output_dir: str = TEMP_DIR):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.piper_path = Path(PIPER_PATH)
        self.piper_model = Path(PIPER_MODEL)
        self.piper_available = self._check_piper()
        logger.info(f"TTS: Piper={self.piper_available}")

    def _check_piper(self) -> bool:
        return self.piper_path.exists() and self.piper_model.exists()

    def generate_speech(self, text: str, character_name: str,
                    output_filename: str = None,
                    voice_settings: Dict = None) -> Optional[str]:
        if not text or not text.strip():
            return None

        text = text.strip()
        if output_filename is None:
            safe_name = character_name.replace(" ", "_")[:15]
            safe_text = text[:15].replace(" ", "_")
            output_filename = f"tts_{safe_name}_{safe_text}.wav"

        output_path = self.output_dir / output_filename

        if self.piper_available:
            try:
                return self._generate_piper(text, output_path)
            except Exception as e:
                logger.warning(f"Piper failed: {e}")

        return self._create_silent(output_path)

    def _generate_piper(self, text: str, output_path: Path) -> str:
        cmd = [str(self.piper_path), "--model", str(self.piper_model), "--output_file", str(output_path)]
        subprocess.run(cmd, input=text.encode("utf-8"), capture_output=True)

        if output_path.exists():
            return str(output_path)
        return self._create_silent(output_path)

    def _create_silent(self, output_path: Path, duration: float = 2.0) -> str:
        import wave
        sample_rate = 22050
        num_samples = int(sample_rate * duration)

        with wave.open(str(output_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b"\x00" * (num_samples * 2))

        return str(output_path)

    def generate_all_dialogs(self, dialogs: List[Dict[str, Any]]) -> Dict[int, List[str]]:
        logger.info(f"Generating {len(dialogs)} dialogs...")
        audio_by_scene = {}

        for i, dialog in enumerate(dialogs):
            character = dialog.get("character", "narrator")
            text = dialog.get("text", "")
            scene_id = dialog.get("scene_id", 1)

            if not text:
                continue

            safe_char = character.replace(" ", "_")[:10]
            safe_text = text[:10].replace(" ", "_")
            filename = f"dialog_{scene_id}_{i}_{safe_char}_{safe_text}.wav"

            audio_path = self.generate_speech(text, character, filename)

            if audio_path:
                if scene_id not in audio_by_scene:
                    audio_by_scene[scene_id] = []
                audio_by_scene[scene_id].append(audio_path)

        return audio_by_scene


def generate_speech(text: str, character_name: str, output_dir: str = TEMP_DIR) -> Optional[str]:
    generator = TTSGenerator(output_dir)
    return generator.generate_speech(text, character_name)


if __name__ == "__main__":
    tts = TTSGenerator()
    print(f"Piper available: {tts.piper_available}")
