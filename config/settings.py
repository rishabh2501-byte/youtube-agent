"""
Configuration settings for AI YouTube Agent.
Loads environment variables and provides centralized configuration.
"""

import os
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # ==========================================================================
    # LLM Configuration
    # ==========================================================================
    groq_api_key: str = Field(default="", description="Groq API key")
    openai_api_key: str = Field(default="", description="OpenAI API key")
    llm_provider: Literal["groq", "openai"] = Field(
        default="groq", 
        description="Preferred LLM provider"
    )
    
    # ==========================================================================
    # Text-to-Speech Configuration
    # ==========================================================================
    elevenlabs_api_key: str = Field(default="", description="ElevenLabs API key")
    elevenlabs_voice_id: str = Field(
        default="21m00Tcm4TlvDq8ikWAM", 
        description="ElevenLabs voice ID"
    )
    openai_tts_voice: str = Field(default="onyx", description="OpenAI TTS voice")
    tts_provider: Literal["elevenlabs", "openai"] = Field(
        default="elevenlabs", 
        description="Preferred TTS provider"
    )
    
    # ==========================================================================
    # Stock Footage Configuration
    # ==========================================================================
    pexels_api_key: str = Field(default="", description="Pexels API key")
    
    # ==========================================================================
    # Image Generation Configuration
    # ==========================================================================
    image_generator: Literal["dalle", "stable_diffusion"] = Field(
        default="dalle", 
        description="Preferred image generator"
    )
    stability_api_key: str = Field(default="", description="Stability AI API key")
    
    # ==========================================================================
    # Instagram Configuration
    # ==========================================================================
    instagram_username: str = Field(default="", description="Instagram username")
    instagram_password: str = Field(default="", description="Instagram password")
    upload_to_instagram: bool = Field(default=False, description="Also upload to Instagram")
    
    # ==========================================================================
    # YouTube API Configuration
    # ==========================================================================
    youtube_client_secrets_file: str = Field(
        default="credentials/client_secrets.json",
        description="Path to YouTube OAuth client secrets"
    )
    youtube_token_file: str = Field(
        default="credentials/youtube_token.json",
        description="Path to YouTube OAuth token"
    )
    youtube_category_id: str = Field(
        default="24", 
        description="YouTube video category ID"
    )
    youtube_privacy_status: Literal["public", "private", "unlisted"] = Field(
        default="public", 
        description="YouTube video privacy status"
    )
    
    # ==========================================================================
    # Video Configuration
    # ==========================================================================
    video_duration_seconds: int = Field(
        default=60, 
        description="Target video duration in seconds"
    )
    video_width: int = Field(default=1080, description="Video width in pixels")
    video_height: int = Field(default=1920, description="Video height in pixels")
    video_fps: int = Field(default=30, description="Video frame rate")
    
    # ==========================================================================
    # Trending Configuration
    # ==========================================================================
    trending_region: str = Field(
        default="US", 
        description="Region for trending topics"
    )
    trending_topics_count: int = Field(
        default=20, 
        description="Number of trending topics to fetch"
    )
    
    # ==========================================================================
    # Output Configuration
    # ==========================================================================
    output_dir: str = Field(default="output", description="Output directory")
    keep_intermediate_files: bool = Field(
        default=False, 
        description="Keep intermediate files"
    )
    
    # ==========================================================================
    # Scheduler Configuration
    # ==========================================================================
    schedule_time: str = Field(
        default="09:00", 
        description="Daily schedule time (HH:MM)"
    )
    timezone: str = Field(default="UTC", description="Timezone for scheduler")
    
    # ==========================================================================
    # Logging Configuration
    # ==========================================================================
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: str = Field(
        default="logs/youtube_agent.log", 
        description="Log file path"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def base_dir(self) -> Path:
        """Get the base directory of the project."""
        return Path(__file__).parent.parent
    
    @property
    def output_path(self) -> Path:
        """Get the output directory path."""
        return self.base_dir / self.output_dir
    
    @property
    def videos_path(self) -> Path:
        """Get the videos output directory."""
        return self.output_path / "videos"
    
    @property
    def audio_path(self) -> Path:
        """Get the audio output directory."""
        return self.output_path / "audio"
    
    @property
    def thumbnails_path(self) -> Path:
        """Get the thumbnails output directory."""
        return self.output_path / "thumbnails"
    
    @property
    def subtitles_path(self) -> Path:
        """Get the subtitles output directory."""
        return self.output_path / "subtitles"
    
    @property
    def credentials_path(self) -> Path:
        """Get the credentials directory."""
        return self.base_dir / "credentials"
    
    @property
    def logs_path(self) -> Path:
        """Get the logs directory."""
        return self.base_dir / "logs"
    
    def ensure_directories(self) -> None:
        """Create all required directories if they don't exist."""
        directories = [
            self.output_path,
            self.videos_path,
            self.audio_path,
            self.thumbnails_path,
            self.subtitles_path,
            self.credentials_path,
            self.logs_path,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
