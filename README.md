# Advanced Video Editing Pipeline

A powerful Python-based video editing pipeline for creating viral short-form content with AI-powered features.

## 🚀 Features

🎬 **Frame-accurate video trimming and concatenation**  
🎨 **Professional color grading** (+6 brightness, +15 contrast, +15 saturation, +15 brilliance, +50 sharpen)  
📱 **9:16 portrait transformation** with background blur effect  
🗣️ **AI-powered speech-to-text** using OpenAI Whisper  
🎯 **Submagic-style animated subtitles** with colorful word-level timing  
🤖 **Automated YouTube metadata generation** using GPT  
📊 **Batch processing** with CSV library management  

## 📦 Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install FFmpeg:**
   - Windows: Download from https://ffmpeg.org/download.html
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg`

3. **Set up OpenAI API (optional for metadata generation):**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

## 🎯 Quick Start

### Interactive Mode (Recommended)
```bash
python main.py --interactive
```
This will open file dialogs to select your video and output directory.

### Command Line Mode
```bash
# Basic usage with default time segments
python main.py -i input_video.mp4

# With custom time ranges
python main.py -i input_video.mp4 -t "[(00:02:24,00:03:00),(00:03:16,00:03:53)]"

# With configuration file
python main.py -i input_video.mp4 -c config/example_config.json

# With custom output directory
python main.py -i input_video.mp4 -o ./my_output --preset quality
```

## 💻 Output Files

- `final_video_TIMESTAMP_HASH.mp4`: Your processed short-form video
- `metadata_TIMESTAMP_HASH.json`: AI-generated YouTube metadata
- `video_library.csv`: CSV database of all processed videos
- `video_pipeline.log`: Detailed processing log

## 🛠️ Troubleshooting

### Import Errors
If you see "ModuleNotFoundError: No module named 'src.core'":
1. Make sure you're running from the VideoEditingPipeline directory
2. Check that all `__init__.py` files exist in src/ subdirectories

### FFmpeg Not Found
- Install FFmpeg and ensure it's in your system PATH
- Test with: `ffmpeg -version`

## 📈 YouTube Monetization Strategy

This pipeline is designed to help you create viral short-form content for:
- YouTube Shorts
- TikTok  
- Instagram Reels
- Facebook Reels

The AI-generated metadata includes SEO-optimized titles, descriptions, tags, and hashtags to maximize discoverability and engagement.

## 📄 License

This project is provided as-is for educational and commercial use.
