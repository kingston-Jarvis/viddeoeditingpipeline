"""
Subtitle generation using Whisper transcription and pysubs2 styling
"""
import logging
import random
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class SubtitleGenerator:
    """Generate Submagic-style subtitles from transcription"""

    def __init__(self, config):
        self.config = config

    def create_submagic_style_subtitles(self, transcription: Dict[str, Any], subtitle_path: Path) -> bool:
        """Create colorful animated subtitles in Submagic style"""
        try:
            import pysubs2
            from pysubs2 import SSAFile, SSAEvent, SSAStyle, Color

            # Create subtitle file
            subs = SSAFile()

            # Define Submagic-style colors
            colors = [
                "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
                "#DDA0DD", "#FFB6C1", "#87CEEB", "#F0E68C", "#FFA07A"
            ]

            # Create base style
            base_style = SSAStyle(
                fontname=getattr(self.config.subtitles, 'font_name', 'Anton'),
                fontsize=getattr(self.config.subtitles, 'font_size', 52),
                primarycolor=Color(255, 255, 255),
                outline=2,
                backcolor=Color(0, 0, 0, 128),
                bold=True
            )
            subs.styles["magic"] = base_style

            # Process each segment and word
            for segment in transcription.get('segments', []):
                for word_info in segment.get('words', []):
                    start_time = int(word_info['start'] * 1000)  # Convert to milliseconds
                    end_time = int(word_info['end'] * 1000)
                    word = word_info['word'].strip()

                    if not word:
                        continue

                    # Random color for each word
                    color = random.choice(colors)
                    # Convert hex to BGR for ASS format
                    color_bgr = color[5:3:-1] + color[3:1:-1] + color[1:0:-1] if len(color) == 7 else "FFFFFF"

                    # Create subtitle event with color
                    text = f"{{\c&H{color_bgr}&}}{word}"

                    event = SSAEvent(
                        start=start_time,
                        end=end_time,
                        text=text,
                        style="magic"
                    )
                    subs.append(event)

            # Save subtitle file
            subs.save(str(subtitle_path))
            logger.info(f"Created Submagic-style subtitles: {subtitle_path}")
            return True

        except ImportError:
            logger.error("pysubs2 not installed. Install with: pip install pysubs2")
            return False
        except Exception as e:
            logger.error(f"Failed to create subtitles: {e}")
            return False

    def create_simple_subtitles(self, transcription: Dict[str, Any], subtitle_path: Path) -> bool:
        """Create simple SRT subtitles as fallback"""
        try:
            with open(subtitle_path, 'w', encoding='utf-8') as f:
                subtitle_index = 1
                for segment in transcription.get('segments', []):
                    start_time = self._format_time(segment['start'])
                    end_time = self._format_time(segment['end'])
                    text = segment['text'].strip()

                    f.write(f"{subtitle_index}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{text}\n\n")
                    subtitle_index += 1

            logger.info(f"Created simple subtitles: {subtitle_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create simple subtitles: {e}")
            return False

    def _format_time(self, seconds: float) -> str:
        """Format time for SRT format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
