"""
Video processing operations using FFmpeg for the Advanced Video Editing Pipeline.
-------------------------------------------------------------------------------
Features:
- Segment extraction with accurate timecode
- Segment concatenation
- Color grading with brightness, contrast, saturation, and sharpness
- Portrait 9:16 transformation with padding and format conversion
- Subtitle burn-in in final rendering
- Logging and structured error handling throughout
-------------------------------------------------------------------------------
"""

import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from utils.ffmpeg_utils import FFmpegUtils

logger = logging.getLogger(__name__)


class VideoProcessor:
    """
    Video processing operations using FFmpeg.
    """

    def __init__(self, config: Any):
        """
        Initialize VideoProcessor.
        Args:
            config: config object with pipeline settings.
        """
        self.config = config
        self.ffmpeg = FFmpegUtils()

    # -----------------------
    # SEGMENT EXTRACTION
    # -----------------------

    def extract_segment(
        self, input_video: Path, start_time: str, end_time: str, output: Path
    ) -> bool:
        """
        Extract a segment from a video using FFmpeg.
        Args:
            input_video: Path to input video file.
            start_time: Start time of the segment (HH:MM:SS).
            end_time: End time of the segment (HH:MM:SS).
            output: Output Path for the segment.
        Returns:
            True if segment extraction was successful, False otherwise.
        """
        try:
            cmd = [
                "ffmpeg", "-y", "-i", str(input_video),
                "-ss", start_time, "-to", end_time,
                "-c", "copy", str(output)
            ]
            logger.debug(f"Extract segment cmd: {' '.join(cmd)}")
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Extracted segment: {start_time} -> {end_time} ({output})")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to extract segment {start_time}-{end_time}: {e.stderr or e}")
            return False

    # -----------------------
    # SEGMENT CONCATENATION
    # -----------------------

    def concatenate_segments(
        self, segments: List[Path], output: Path
    ) -> bool:
        """
        Concatenate multiple video segments into a single file.
        Args:
            segments: List of Paths to segment files.
            output: Output Path for concatenated video.
        Returns:
            True if concatenation successful, False otherwise.
        """
        try:
            concat_file = output.parent / "concat_list.txt"
            with open(concat_file, 'w', encoding='utf-8') as f:
                for segment in segments:
                    f.write(f"file '{segment.as_posix()}'\n")
            cmd = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", str(concat_file), "-c", "copy", str(output)
            ]
            logger.debug(f"Concatenate segments cmd: {' '.join(cmd)}")
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Concatenated {len(segments)} segments to {output}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to concatenate segments: {e.stderr or e}")
            return False

    # -----------------------
    # COLOR GRADING & ENHANCEMENT
    # -----------------------

    def apply_color_grading(
        self, input_path: Path, output_path: Path, settings: Dict[str, float]
    ) -> bool:
        """
        Apply color grading and enhancement filters to a video.
        Args:
            input_path: Path to source video.
            output_path: Path to save enhanced video.
            settings: Dict with filters and values (brightness, contrast, saturation, sharpen).
        Returns:
            True if successful, False otherwise.
        """
        try:
            filters = []
            eq_filter = (
                f"eq=brightness={settings.get('brightness', 0)}:"
                f"contrast={settings.get('contrast', 1)}:"
                f"saturation={settings.get('saturation', 1)}"
            )
            filters.append(eq_filter)
            if settings.get('sharpen', 0) > 0:
                sharpen_filter = f"unsharp=7:7:{settings['sharpen']}:7:7:0"
                filters.append(sharpen_filter)
            filter_string = ",".join(filters)
            cmd = [
                "ffmpeg", "-y", "-i", str(input_path),
                "-vf", filter_string,
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
                "-c:a", "copy", str(output_path)
            ]
            logger.debug(f"Color grading cmd: {' '.join(cmd)}")
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info(f"Color grading applied: {output_path}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Color grading failed: {e.stderr or e}")
            return False

    # -----------------------
    # PORTRAIT TRANSFORMATION
    # -----------------------

    def transform_to_portrait(
        self, input_path: Path, output_path: Path, width: int, height: int
    ) -> bool:
        """
        Transform the video to a 9:16 portrait format with background blur or black padding.
        Args:
            input_path: Path to color-graded video.
            output_path: Where to save portrait video.
            width: Target width (eg. 1080).
            height: Target height (eg. 1920).
        Returns:
            True if successful, False otherwise.
        """
        try:
            filter_complex = (
                f"[0:v]scale=w={width}:h=-2,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,format=yuv420p[vout]"
            )
            cmd = [
                "ffmpeg", "-y", "-i", str(input_path),
                "-filter_complex", filter_complex,
                "-map", "[vout]", "-map", "0:a?",
                "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
                "-c:a", "aac", str(output_path)
            ]
            logger.debug(f"Portrait transformation cmd: {' '.join(cmd)}")
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Portrait transformation completed: {output_path}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Portrait transformation failed: {e.stderr or e}")
            return False

    # -----------------------
    # FINAL VIDEO RENDER WITH SUBTITLES
    # -----------------------

def render_final_video(self, video_path: Path, subtitle_path: Path, output_path: Path) -> bool:
    """Render final video with subtitles burned in"""
    try:
        subtitle_path_escaped = subtitle_path.as_posix()  # Fix path escape issue

        cmd = [
            "ffmpeg", "-y", "-i", str(video_path),
            "-vf", f"ass='{subtitle_path_escaped}'",
            "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
            "-c:a", "aac", "-b:a", "192k", str(output_path)
        ]
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"Final video rendered: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Final video rendering failed: {e}")
        return False

    # -----------------------
    # UTILITY: GET VIDEO INFO
    # -----------------------

    def get_video_info(self, video_path: Path) -> Optional[Dict[str, Any]]:
        """
        Uses FFprobe to get video information (duration, resolution, etc).
        Args:
            video_path: Path to the video file.
        Returns:
            Dict of information (if available) or None.
        """
        try:
            if hasattr(self.ffmpeg, "get_video_info"):
                return self.ffmpeg.get_video_info(video_path)
            return None
        except Exception as e:
            logger.warning(f"Video info extraction failed: {str(e)}")
            return None

    # -----------------------
    # UTILITY: ESTIMATE PROCESSING TIME
    # -----------------------
    def estimate_processing_time(self, video_duration: float, operations: List[str]) -> float:
        """
        Estimate processing time based on video length and operation types.
        Args:
            video_duration: Duration (seconds)
            operations: List of operation names
        Returns:
            processing_time: estimated seconds
        """
        factors = {
            'extract': 0.06,  # about 6% real-time
            'concat': 0.03,
            'color_grade': 0.18,
            'portrait_transform': 0.25,
            'subtitle_render': 0.33
        }
        total_factor = sum([factors.get(op, 0.1) for op in operations])
        return video_duration * total_factor

    # -----------------------
    # FILE CLEANUP (OPTIONAL)
    # -----------------------

    def cleanup_temp_files(self, temp_paths: List[Path]) -> None:
        """
        Delete all temporary files and logs from pipeline after completion.
        Args:
            temp_paths: List of file Paths.
        """
        for p in temp_paths:
            try:
                if p.exists():
                    p.unlink()
                    logger.info(f"Deleted temporary file: {p}")
            except Exception as e:
                logger.warning(f"Could not delete temp file {p}: {str(e)}")

# End of VideoProcessor
