"""
AI-powered metadata generation for YouTube optimization
"""
import logging
import csv
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MetadataGenerator:
    """Generate YouTube metadata using AI"""

    def __init__(self, config):
        self.config = config
        self.openai_client = None

    def _get_openai_client(self):
        """Get OpenAI client lazily"""
        if self.openai_client is None:
            try:
                from openai import OpenAI
                self.openai_client = OpenAI()
                logger.info("OpenAI client initialized")
            except ImportError:
                logger.warning("OpenAI not installed. Install with: pip install openai")
                return None
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                return None
        return self.openai_client

    def generate_youtube_metadata(self, transcription: Dict[str, Any], video_path: Path) -> Optional[Dict[str, Any]]:
        """Generate YouTube metadata using AI"""
        client = self._get_openai_client()

        if not client:
            return self.generate_fallback_metadata(transcription, video_path)

        try:
            # Extract text from transcription
            full_text = transcription.get('text', '')
            if not full_text:
                # Fallback to segments
                segments = transcription.get('segments', [])
                full_text = ' '.join([seg.get('text', '') for seg in segments])

            # Limit text length for API
            text_sample = full_text[:4000] if len(full_text) > 4000 else full_text

            prompt = f"""
Based on this video transcript, generate YouTube metadata:

Transcript: "{text_sample}"

Generate:
1. A catchy title (max 100 characters)
2. SEO-optimized description (max 350 words)
3. 10 relevant tags
4. 10 trending hashtags

Format as JSON with keys: title, description, tags (array), hashtags (array)
Focus on viral, engaging content that will get views and engagement.
"""

            response = client.chat.completions.create(
                model=getattr(self.config.metadata, 'openai_model', 'gpt-4o-mini'),
                messages=[{"role": "user", "content": prompt}],
                temperature=getattr(self.config.metadata, 'openai_temperature', 0.6),
                max_tokens=getattr(self.config.metadata, 'openai_max_tokens', 1500)
            )

            # Parse response
            content = response.choices[0].message.content.strip()

            # Try to extract JSON from response
            import json
            import re

            # Look for JSON block in response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                metadata = json.loads(json_match.group())
            else:
                # Fallback parsing
                lines = content.split('\n')
                metadata = {
                    'title': next((line.split(':', 1)[1].strip() for line in lines if 'title' in line.lower()), f"Highlights - {video_path.stem}"),
                    'description': content[:350],
                    'tags': ['shorts', 'viral', 'trending', 'ai', 'video'],
                    'hashtags': ['#shorts', '#viral', '#trending', '#ai', '#video']
                }

            logger.info("Generated AI metadata successfully")
            return metadata

        except Exception as e:
            logger.warning(f"AI metadata generation failed: {e}, using fallback")
            return self.generate_fallback_metadata(transcription, video_path)

    def generate_fallback_metadata(self, transcription: Dict[str, Any], video_path: Path) -> Dict[str, Any]:
        """Generate fallback metadata without AI"""
        # Extract key words from transcription
        text = transcription.get('text', '')
        words = text.lower().split() if text else []

        # Simple keyword extraction
        common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
        keywords = [word for word in words if len(word) > 3 and word not in common_words][:10]

        metadata = {
            'title': f"Amazing Content - {video_path.stem}",
            'description': f"Check out this amazing video content! {text[:200]}..." if text else "Amazing short-form content created with AI video editing pipeline.",
            'tags': keywords if keywords else ['shorts', 'video', 'content', 'viral', 'trending'],
            'hashtags': ['#shorts', '#viral', '#trending', '#video', '#content', '#ai', '#editing', '#youtube', '#tiktok', '#reels']
        }

        logger.info("Generated fallback metadata")
        return metadata

    def append_to_csv_library(self, metadata: Dict[str, Any], video_path: Path):
        """Append video metadata to CSV library"""
        try:
            csv_path = self.config.output_dir / "video_library.csv"

            # Prepare row data
            row_data = {
                'filename': video_path.name,
                'title': metadata.get('title', ''),
                'description': metadata.get('description', '')[:200],  # Limit description
                'tags': ';'.join(metadata.get('tags', [])),
                'hashtags': ';'.join(metadata.get('hashtags', [])),
                'created_date': str(video_path.stat().st_mtime) if video_path.exists() else ''
            }

            # Check if file exists to write header
            write_header = not csv_path.exists()

            with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=row_data.keys())
                if write_header:
                    writer.writeheader()
                writer.writerow(row_data)

            logger.info(f"Appended to CSV library: {csv_path}")

        except Exception as e:
            logger.error(f"Failed to append to CSV library: {e}")
