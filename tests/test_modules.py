"""
Test suite for AI YouTube Agent modules.
Run with: pytest tests/test_modules.py -v
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings


class TestSettings:
    """Test configuration settings."""
    
    def test_settings_loaded(self):
        """Test that settings are loaded."""
        assert settings is not None
    
    def test_default_values(self):
        """Test default configuration values."""
        assert settings.video_duration_seconds == 60
        assert settings.video_width == 1080
        assert settings.video_height == 1920
        assert settings.video_fps == 30
    
    def test_paths(self):
        """Test path properties."""
        assert settings.base_dir.exists()
        assert isinstance(settings.output_path, Path)
        assert isinstance(settings.videos_path, Path)


class TestTrendingFetcher:
    """Test trending topics fetcher."""
    
    @patch('modules.trending_fetcher.TrendReq')
    def test_fetch_daily_trends(self, mock_pytrends):
        """Test fetching daily trends."""
        from modules.trending_fetcher import TrendingFetcher
        
        # Mock the trending searches response
        mock_instance = Mock()
        mock_pytrends.return_value = mock_instance
        
        import pandas as pd
        mock_df = pd.DataFrame({'0': ['Topic 1', 'Topic 2', 'Topic 3']})
        mock_instance.trending_searches.return_value = mock_df
        
        fetcher = TrendingFetcher()
        trends = fetcher.fetch_daily_trends(limit=3)
        
        assert len(trends) <= 3
        assert all('topic' in t for t in trends)


class TestTopicSelector:
    """Test topic selector."""
    
    def test_format_topics_list(self):
        """Test topic list formatting."""
        from modules.topic_selector import TopicSelector
        
        selector = TopicSelector.__new__(TopicSelector)
        
        topics = [
            {"rank": 1, "topic": "AI Technology"},
            {"rank": 2, "topic": "Space Exploration"},
        ]
        
        formatted = selector._format_topics_list(topics)
        
        assert "1. AI Technology" in formatted
        assert "2. Space Exploration" in formatted
    
    def test_parse_response(self):
        """Test response parsing."""
        from modules.topic_selector import TopicSelector
        
        selector = TopicSelector.__new__(TopicSelector)
        
        response = """SELECTED_TOPIC: AI Technology
REASON: This topic has high viral potential.
ANGLE: How AI is changing daily life
KEYWORDS: ai, technology, future, robots, automation
TONE: educational"""
        
        result = selector._parse_response(response)
        
        assert result["selected_topic"] == "AI Technology"
        assert "ai" in result["keywords"]
        assert result["tone"] == "educational"


class TestScriptGenerator:
    """Test script generator."""
    
    def test_clean_script(self):
        """Test script cleaning."""
        from modules.script_generator import ScriptGenerator
        
        generator = ScriptGenerator.__new__(ScriptGenerator)
        
        dirty_script = """**Bold text** and *italic*
        
        [Stage direction]
        
        (Another direction)
        
        Clean text here."""
        
        cleaned = generator._clean_script(dirty_script)
        
        assert "**" not in cleaned
        assert "[Stage direction]" not in cleaned
        assert "Clean text here" in cleaned


class TestSubtitleGenerator:
    """Test subtitle generator."""
    
    def test_split_into_chunks(self):
        """Test text chunking for subtitles."""
        from modules.subtitle_generator import SubtitleGenerator
        
        generator = SubtitleGenerator.__new__(SubtitleGenerator)
        
        text = "This is a test sentence. Here is another one. And a third."
        chunks = generator._split_into_chunks(text, max_chars_per_line=42, max_lines=2)
        
        assert len(chunks) > 0
        assert all(len(c) <= 84 for c in chunks)  # 42 * 2
    
    def test_calculate_timing(self):
        """Test timing calculation."""
        from modules.subtitle_generator import SubtitleGenerator
        
        generator = SubtitleGenerator.__new__(SubtitleGenerator)
        
        chunks = ["First chunk", "Second chunk", "Third chunk"]
        timed = generator._calculate_timing(chunks, total_duration=30.0)
        
        assert len(timed) == 3
        assert timed[0]["start_time"] == 0.0
        assert timed[-1]["end_time"] <= 30.0


class TestSEOGenerator:
    """Test SEO generator."""
    
    def test_parse_response(self):
        """Test SEO response parsing."""
        from modules.seo_generator import SEOGenerator
        
        generator = SEOGenerator.__new__(SEOGenerator)
        
        response = """TITLE: Amazing Facts About Space

DESCRIPTION:
Discover incredible facts about space that will blow your mind!
#space #facts #science

TAGS: space, facts, science, astronomy, universe"""
        
        result = generator._parse_response(response)
        
        assert "Amazing Facts" in result["title"]
        assert "space" in result["description"].lower()
        assert "space" in result["tags"]
    
    def test_validate_metadata(self):
        """Test metadata validation."""
        from modules.seo_generator import SEOGenerator
        
        generator = SEOGenerator.__new__(SEOGenerator)
        
        # Test with empty metadata
        metadata = {"title": "", "description": "", "tags": []}
        validated = generator._validate_metadata(metadata, "Test Topic")
        
        assert validated["title"] != ""
        assert validated["description"] != ""
        assert len(validated["tags"]) > 0


class TestHelpers:
    """Test helper utilities."""
    
    def test_generate_unique_id(self):
        """Test unique ID generation."""
        from utils.helpers import generate_unique_id
        
        id1 = generate_unique_id()
        id2 = generate_unique_id()
        
        assert id1 != id2
        assert len(id1) > 0
    
    def test_generate_unique_id_with_prefix(self):
        """Test unique ID with prefix."""
        from utils.helpers import generate_unique_id
        
        id_with_prefix = generate_unique_id("test")
        
        assert id_with_prefix.startswith("test_")
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        from utils.helpers import sanitize_filename
        
        dirty = 'Test: File/Name?With*Bad<Chars>'
        clean = sanitize_filename(dirty)
        
        assert ":" not in clean
        assert "/" not in clean
        assert "?" not in clean
        assert "*" not in clean
    
    def test_format_duration(self):
        """Test duration formatting."""
        from utils.helpers import format_duration
        
        assert format_duration(90) == "1:30"
        assert format_duration(3661) == "1:01:01"
        assert format_duration(45) == "0:45"
    
    def test_chunk_text(self):
        """Test text chunking."""
        from utils.helpers import chunk_text
        
        text = "This is a long text. " * 20
        chunks = chunk_text(text, max_chars=100)
        
        assert len(chunks) > 1
        assert all(len(c) <= 100 for c in chunks)
    
    def test_extract_keywords(self):
        """Test keyword extraction."""
        from utils.helpers import extract_keywords
        
        text = "Python programming language is great for automation and data science"
        keywords = extract_keywords(text, max_keywords=5)
        
        assert len(keywords) <= 5
        assert "python" in keywords or "programming" in keywords


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
