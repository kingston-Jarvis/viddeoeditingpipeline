"""
Audio processing operations using Whisper
"""
import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
import subprocess

logger = logging.getLogger(__name__)

class AudioProcessor:
    """Audio processing and transcription using Whisper"""

    def __init__(self, config):
        self.config = config
        self.whisper_model = None

    def _load_whisper_model(self):
        """Load Whisper model lazily"""
        if self.whisper_model is None:
            try:
                import whisper
                model_name = getattr(self.config.whisper, 'model', 'base.en')
                self.whisper_model = whisper.load_model(model_name)
                logger.info(f"Loaded Whisper model: {model_name}")
            except ImportError:
                logger.error("Whisper not installed. Install with: pip install openai-whisper")
                return False
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                return False
        return True

    def extract_audio(self, video_path: Path, audio_path: Path) -> bool:
        """Extract audio from video file"""
        try:
            cmd = [
                "ffmpeg", "-y", "-i", str(video_path),
                "-vn", "-acodec", "pcm_s16le", "-ar", "16000",
                str(audio_path)
            ]
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Audio extracted to: {audio_path}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to extract audio: {e}")
            return False

    def transcribe_video(self, video_path: Path) -> Optional[Dict[str, Any]]:
        """Transcribe video using Whisper"""
        try:
            # Load Whisper model
            if not self._load_whisper_model():
                return None

            # Extract audio to temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
                audio_path = Path(temp_audio.name)

            if not self.extract_audio(video_path, audio_path):
                return None

            # Transcribe with word timestamps
            logger.info("Starting transcription...")
            result = self.whisper_model.transcribe(
                str(audio_path),
                language=getattr(self.config.whisper, 'language', None)
            )

            # Cleanup temp file
            audio_path.unlink(missing_ok=True)

            logger.info(f"Transcription completed: {len(result.get('segments', []))} segments")
            return result

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return None

    def get_audio_duration(self, video_path: Path) -> float:
        """Get audio duration from video file"""
        try:
            cmd = [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "csv=p=0", str(video_path)
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except Exception as e:
            logger.error(f"Failed to get audio duration: {e}")
            return 0.0
