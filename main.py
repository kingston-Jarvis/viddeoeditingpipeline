#!/usr/bin/env python3
"""
Advanced Video Editing Pipeline for Short-Form Content
=====================================================

This pipeline processes raw video into viral short-form content with:
- Frame-accurate trimming and concatenation
- Professional color grading and enhancement  
- 9:16 portrait transformation with background blur
- AI-powered speech-to-text with Submagic-style subtitles
- Automated metadata generation for YouTube optimization
- Interactive file selection for user-friendly operation

Author: Advanced Video Pipeline
Version: 2.0.1
"""
import os
import argparse
import sys
import json
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Any
import tempfile
import shutil
from datetime import datetime
import hashlib

# Add project root to Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

import os
print("Using VideoProcessor from:", __import__('core.video_processor').__file__)

# Import our custom modules
from core.video_processor import VideoProcessor
from core.audio_processor import AudioProcessor  
from core.subtitle_generator import SubtitleGenerator
from core.metadata_generator import MetadataGenerator
# from utils.file_utils import FileUtils
from utils.time_utils import TimeUtils
from utils.ffmpeg_utils import FFmpegUtils
from models.video_config import VideoConfig, ProcessingConfig
from config.settings import Settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('video_pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def select_video_file() -> str:
    """Interactive video file selection"""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()  # Hide main window
        root.attributes('-topmost', True)  # Bring to front

        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[
                ("Video Files", "*.mp4 *.mkv *.mov *.avi *.flv *.webm *.m4v"),
                ("MP4 Files", "*.mp4"),
                ("All Files", "*.*")
            ]
        )

        root.destroy()
        return file_path

    except ImportError:
        print("Tkinter not available. Please provide video path manually.")
        return input("Enter video file path: ").strip()


def select_output_directory() -> str:
    """Interactive output directory selection"""
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        folder_path = filedialog.askdirectory(
            title="Select Output Directory"
        )

        root.destroy()
        return folder_path if folder_path else str(Path.cwd() / "output")

    except ImportError:
        print("Tkinter not available. Using default output directory.")
        return str(Path.cwd() / "output")


class VideoEditingPipeline:
    """Main pipeline orchestrator that coordinates all video processing operations."""

    def __init__(self, config: VideoConfig):
        """Initialize the pipeline with configuration."""
        self.config = config
        self.settings = Settings()
        self.temp_dir = None

        # Initialize processors
        self.video_processor = VideoProcessor(config)
        self.audio_processor = AudioProcessor(config)
        self.subtitle_generator = SubtitleGenerator(config)
        self.metadata_generator = MetadataGenerator(config)

        # Utilities
        # self.file_utils = FileUtils()
        self.time_utils = TimeUtils()
        self.ffmpeg_utils = FFmpegUtils()

        logger.info(f"Pipeline initialized with config: {config.source_video}")

    def __enter__(self):
        """Context manager entry - setup temp directory."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="video_pipeline_"))
        logger.info(f"Created temporary directory: {self.temp_dir}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup temp directory."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            logger.info(f"Cleaned up temporary directory: {self.temp_dir}")

    def validate_inputs(self) -> bool:
        """Validate all input parameters and dependencies."""
        logger.info("Validating pipeline inputs...")

        # Check source video exists
        if not self.config.source_video.exists():
            logger.error(f"Source video not found: {self.config.source_video}")
            return False

        # Check FFmpeg availability
        if not self.ffmpeg_utils.check_ffmpeg_available():
            logger.error("FFmpeg not available in system PATH")
            print("Please install FFmpeg: https://ffmpeg.org/download.html")
            return False

        # Validate time ranges
        for i, (start, end) in enumerate(self.config.time_ranges):
            if not self.time_utils.validate_time_format(start):
                logger.error(f"Invalid start time format in range {i}: {start}")
                return False
            if not self.time_utils.validate_time_format(end):
                logger.error(f"Invalid end time format in range {i}: {end}")
                return False

            start_seconds = self.time_utils.time_to_seconds(start)
            end_seconds = self.time_utils.time_to_seconds(end)

            if start_seconds >= end_seconds:
                logger.error(f"Invalid time range {i}: start >= end ({start} >= {end})")
                return False

        # Check output directory
        self.config.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Input validation completed successfully")
        return True

    def extract_segments(self) -> Path:
        """Extract and concatenate video segments based on time ranges."""
        logger.info("Starting segment extraction...")

        segment_files = []

        # Extract each segment
        for i, (start_time, end_time) in enumerate(self.config.time_ranges):
            segment_path = self.temp_dir / f"segment_{i:03d}.mkv"

            logger.info(f"Extracting segment {i+1}/{len(self.config.time_ranges)}: {start_time} to {end_time}")

            success = self.video_processor.extract_segment(
                self.config.source_video,
                start_time,
                end_time,
                segment_path
            )

            if success:
                segment_files.append(segment_path)
            else:
                logger.error(f"Failed to extract segment {i}: {start_time} to {end_time}")
                raise RuntimeError(f"Segment extraction failed for range {i}")

        # Concatenate all segments
        concatenated_path = self.temp_dir / "concatenated.mkv"
        success = self.video_processor.concatenate_segments(segment_files, concatenated_path)

        if not success:
            raise RuntimeError("Failed to concatenate video segments")

        logger.info(f"Successfully extracted and concatenated {len(segment_files)} segments")
        return concatenated_path

    def apply_color_grading(self, input_path: Path) -> Path:
        """Apply color grading and enhancement filters."""
        logger.info("Applying color grading and enhancement...")

        output_path = self.temp_dir / "color_graded.mkv"

        # Apply the specific color grading requested
        color_settings = {
            'brightness': 0.06,    # +6
            'contrast': 1.15,      # +15%  
            'saturation': 1.15,    # +15%
            'brilliance': 0.15,    # +15 (using curves filter)
            'sharpen': 1.0         # +50 (using unsharp filter)
        }

        success = self.video_processor.apply_color_grading(
            input_path, 
            output_path, 
            color_settings
        )

        if not success:
            raise RuntimeError("Color grading failed")

        logger.info("Color grading completed successfully")
        return output_path

    def transform_to_portrait(self, input_path: Path) -> Path:
        """Transform video to 9:16 portrait with background blur effect."""
        logger.info("Transforming to portrait format with background blur...")

        output_path = self.temp_dir / "portrait.mkv"

        success = self.video_processor.transform_to_portrait(
            input_path,
            output_path,
            self.config.processing.target_width,
            self.config.processing.target_height
        )

        if not success:
            raise RuntimeError("Portrait transformation failed")

        logger.info("Portrait transformation completed successfully")
        return output_path

    def generate_transcription(self, input_path: Path) -> Dict[str, Any]:
        """Generate transcription with word-level timestamps."""
        logger.info("Generating transcription using Whisper...")

        transcription = self.audio_processor.transcribe_video(input_path)

        if not transcription:
            logger.warning("Transcription failed, creating dummy transcription")
            transcription = {
                'text': 'Video content transcription not available.',
                'segments': []
            }

        # Save transcription to temp file for reference
        transcription_path = self.temp_dir / "transcription.json"
        with open(transcription_path, 'w', encoding='utf-8') as f:
            json.dump(transcription, f, indent=2, ensure_ascii=False)

        logger.info(f"Transcription completed with {len(transcription.get('segments', []))} segments")
        return transcription

    def create_subtitles(self, transcription: Dict[str, Any]) -> Path:
        """Create Submagic-style subtitles from transcription."""
        logger.info("Creating Submagic-style subtitles...")

        subtitle_path = self.temp_dir / "subtitles.ass"

        success = self.subtitle_generator.create_submagic_style_subtitles(
            transcription,
            subtitle_path
        )

        if not success:
            # Fallback to simple subtitles
            logger.warning("Submagic-style subtitles failed, creating simple subtitles")
            subtitle_path = self.temp_dir / "subtitles.srt"
            success = self.subtitle_generator.create_simple_subtitles(
                transcription,
                subtitle_path
            )

        if not success:
            raise RuntimeError("Subtitle generation failed")

        logger.info("Subtitles created successfully")
        return subtitle_path

    def render_final_video(self, video_path: Path, subtitle_path: Path) -> Path:
        """Render the final video with subtitles burned in."""
        logger.info("Rendering final video with subtitles...")

        # Generate unique output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        source_hash = hashlib.md5(str(self.config.source_video).encode()).hexdigest()[:8]
        final_filename = f"final_video_{timestamp}_{source_hash}.mp4"

        output_path = self.config.output_dir / final_filename

        success = self.video_processor.render_final_video(
            video_path,
            subtitle_path,
            output_path
        )

        if not success:
            raise RuntimeError("Final video rendering failed")

        logger.info(f"Final video rendered successfully: {output_path}")
        return output_path

    def generate_metadata(self, transcription: Dict[str, Any], final_video_path: Path) -> Dict[str, Any]:
        """Generate AI-powered metadata for YouTube optimization."""
        logger.info("Generating AI-powered metadata...")

        metadata = self.metadata_generator.generate_youtube_metadata(
            transcription,
            final_video_path
        )

        if not metadata:
            logger.warning("Metadata generation failed, using fallback")
            metadata = self.metadata_generator.generate_fallback_metadata(
                transcription,
                final_video_path
            )

        # Save metadata to JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        source_hash = hashlib.md5(str(self.config.source_video).encode()).hexdigest()[:8]
        metadata_filename = f"metadata_{timestamp}_{source_hash}.json"

        metadata_path = self.config.output_dir / metadata_filename
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        # Append to CSV library
        self.metadata_generator.append_to_csv_library(metadata, final_video_path)

        logger.info(f"Metadata generated and saved: {metadata_path}")
        return metadata

    def process(self) -> Tuple[Path, Dict[str, Any]]:
        """Execute the complete video processing pipeline."""
        logger.info("Starting complete video processing pipeline...")

        try:
            # Validate inputs
            if not self.validate_inputs():
                raise RuntimeError("Input validation failed")

            # Step 1: Extract and concatenate segments
            concatenated_video = self.extract_segments()

            # Step 2: Apply color grading
            color_graded_video = self.apply_color_grading(concatenated_video)

            # Step 3: Transform to portrait
            portrait_video = self.transform_to_portrait(color_graded_video)

            # Step 4: Generate transcription
            transcription = self.generate_transcription(portrait_video)

            # Step 5: Create subtitles
            subtitle_file = self.create_subtitles(transcription)

            # Step 6: Render final video
            final_video = self.render_final_video(portrait_video, subtitle_file)

            # Step 7: Generate metadata
            metadata = self.generate_metadata(transcription, final_video)

            logger.info("Pipeline completed successfully!")
            return final_video, metadata

        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            raise


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Advanced Video Editing Pipeline for Short-Form Content",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '-i', '--input',
        type=Path,
        help='Input video file path (or use --interactive)'
    )

    parser.add_argument(
        '-t', '--timings',
        type=str,
        help='Time ranges as Python list string or JSON file path'
    )

    parser.add_argument(
        '-c', '--config',
        type=Path,
        help='Configuration JSON file path'
    )

    parser.add_argument(
        '-o', '--output-dir',
        type=Path,
        help='Output directory (or use --interactive)'
    )

    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Use interactive file selection dialogs'
    )

    parser.add_argument(
        '--preset',
        choices=['fast', 'balanced', 'quality'],
        default='balanced',
        help='Processing preset (default: balanced)'
    )

    parser.add_argument(
        '--no-gpu',
        action='store_true',
        help='Disable GPU acceleration'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    return parser.parse_args()


def load_time_ranges(timings_input: str) -> List[Tuple[str, str]]:
    """Load time ranges from various input formats."""
    # Check if it's a file path
    if Path(timings_input).exists():
        with open(timings_input, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif 'time_ranges' in data:
                return data['time_ranges']

    # Try to parse as Python literal
    try:
        import ast
        parsed = ast.literal_eval(timings_input)
        if isinstance(parsed, list):
            return parsed
    except (ValueError, SyntaxError):
        pass

    # Try to parse as JSON
    try:
        parsed = json.loads(timings_input)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass

    raise ValueError(f"Could not parse time ranges from: {timings_input}")


def main():
    """Main entry point."""
    args = parse_arguments()

    # Setup logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Handle interactive mode
        if args.interactive or not args.input:
            print("🎬 Advanced Video Editing Pipeline")
            print("=" * 40)

            if not args.input:
                print("Please select input video file:")
                input_video = select_video_file()
                if not input_video:
                    print("No video file selected. Exiting.")
                    sys.exit(1)
                args.input = Path(input_video)

            if not args.output_dir:
                print("Please select output directory:")
                output_dir = select_output_directory()
                args.output_dir = Path(output_dir)

        # Ensure we have required inputs
        if not args.input:
            logger.error("Input video file is required")
            sys.exit(1)

        # Load time ranges
        if args.config:
            # Load from config file
            with open(args.config, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            time_ranges = config_data.get('time_ranges', [])
        elif args.timings:
            time_ranges = load_time_ranges(args.timings)
        else:
            # Default time ranges from the original request
            print("Using default time ranges...")
            time_ranges = [
                ("00:02:24", "00:03:00"),
                ("00:03:16", "00:03:53"),
                ("00:04:00", "00:04:40"),
                ("00:05:00", "00:05:30"),
                ("00:06:00", "00:06:45"),
                ("00:07:10", "00:07:50"),
                ("00:08:05", "00:08:40"),
                ("00:09:00", "00:09:40"),
                ("00:10:00", "00:10:30"),
                ("00:11:00", "00:11:40")
            ]

        if not time_ranges:
            logger.error("No time ranges provided")
            sys.exit(1)

        # Set default output directory if not provided
        if not args.output_dir:
            args.output_dir = Path("output")

        # Create processing configuration
        processing_config = ProcessingConfig(
            preset=args.preset,
            use_gpu=not args.no_gpu,
            temp_dir=None
        )

        # Create video configuration
        video_config = VideoConfig(
            source_video=args.input,
            time_ranges=time_ranges,
            output_dir=args.output_dir,
            processing=processing_config
        )

        # Print configuration summary
        print(f"\n📹 Source Video: {video_config.source_video}")
        print(f"🎯 Time Ranges: {len(time_ranges)} segments")
        print(f"📂 Output Directory: {video_config.output_dir}")
        print(f"⚙️  Preset: {args.preset}")
        print(f"🚀 GPU Acceleration: {'Enabled' if not args.no_gpu else 'Disabled'}")
        print(f"\n🔄 Starting processing...")

        # Run pipeline
        with VideoEditingPipeline(video_config) as pipeline:
            final_video, metadata = pipeline.process()

            print(f"\n✅ Processing completed successfully!")
            print(f"📹 Final video: {final_video}")
            print(f"📊 Metadata: {video_config.output_dir / 'metadata_*.json'}")
            print(f"📚 Library: {video_config.output_dir / 'video_library.csv'}")
            print(f"\n🎉 Your viral short-form content is ready!")

    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        print(f"\n❌ Error: {str(e)}")
        print("Check the log file for more details: video_pipeline.log")
        sys.exit(1)


if __name__ == "__main__":
    main()
