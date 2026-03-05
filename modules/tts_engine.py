"""
Text-to-Speech Engine Module.
Converts scripts to natural speech using ElevenLabs, OpenAI TTS, or gTTS (free).
"""

import os
from pathlib import Path
from typing import Optional

import requests
import openai
from gtts import gTTS

from config import settings
from utils.logger import get_logger
from utils.helpers import generate_unique_id, sanitize_filename

logger = get_logger(__name__, settings.log_level, settings.log_file)


class TTSEngine:
    """
    Text-to-Speech engine supporting ElevenLabs and OpenAI TTS.
    Converts text scripts to audio files.
    """
    
    # ElevenLabs API endpoint
    ELEVENLABS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialize the TTS Engine.
        
        Args:
            provider: TTS provider ('elevenlabs', 'openai', or 'gtts')
        """
        self.provider = provider or settings.tts_provider
        
        # Auto-fallback to gtts if no API keys configured
        if self.provider == "openai" and not settings.openai_api_key:
            logger.warning("No OpenAI API key, falling back to gTTS (free)")
            self.provider = "gtts"
        elif self.provider == "elevenlabs" and not settings.elevenlabs_api_key:
            logger.warning("No ElevenLabs API key, falling back to gTTS (free)")
            self.provider = "gtts"
        
        if self.provider == "openai":
            self.client = openai.OpenAI(api_key=settings.openai_api_key)
        
        # Ensure output directory exists
        settings.audio_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"TTSEngine initialized with provider: {self.provider}")
    
    def generate_audio(
        self,
        text: str,
        output_filename: Optional[str] = None,
        voice_id: Optional[str] = None
    ) -> Path:
        """
        Generate audio from text.
        
        Args:
            text: Text to convert to speech
            output_filename: Optional filename for the output
            voice_id: Optional voice ID (provider-specific)
        
        Returns:
            Path to the generated audio file
        """
        logger.info(f"Generating audio with {self.provider}")
        
        # Generate output filename if not provided
        if not output_filename:
            output_filename = f"audio_{generate_unique_id()}.mp3"
        
        output_path = settings.audio_path / output_filename
        
        try:
            if self.provider == "elevenlabs":
                self._generate_elevenlabs(text, output_path, voice_id)
            elif self.provider == "openai":
                self._generate_openai(text, output_path, voice_id)
            else:  # gtts
                self._generate_gtts(text, output_path)
            
            logger.info(f"Audio generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating audio: {e}")
            raise
    
    def _generate_elevenlabs(
        self,
        text: str,
        output_path: Path,
        voice_id: Optional[str] = None
    ) -> None:
        """Generate audio using ElevenLabs API."""
        voice_id = voice_id or settings.elevenlabs_voice_id
        
        url = f"{self.ELEVENLABS_API_URL}/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": settings.elevenlabs_api_key,
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"ElevenLabs API error: {response.status_code} - {response.text}")
        
        with open(output_path, "wb") as f:
            f.write(response.content)
    
    def _generate_openai(
        self,
        text: str,
        output_path: Path,
        voice: Optional[str] = None
    ) -> None:
        """Generate audio using OpenAI TTS API."""
        voice = voice or settings.openai_tts_voice
        
        response = self.client.audio.speech.create(
            model="tts-1-hd",
            voice=voice,
            input=text,
            response_format="mp3"
        )
        
        response.stream_to_file(str(output_path))
    
    def _generate_gtts(self, text: str, output_path: Path) -> None:
        """Generate audio using Google Text-to-Speech (free)."""
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(str(output_path))
    
    def get_audio_duration(self, audio_path: Path) -> float:
        """
        Get the duration of an audio file in seconds.
        
        Args:
            audio_path: Path to the audio file
        
        Returns:
            Duration in seconds
        """
        try:
            from moviepy.editor import AudioFileClip
            
            with AudioFileClip(str(audio_path)) as audio:
                return audio.duration
                
        except Exception as e:
            logger.error(f"Error getting audio duration: {e}")
            # Estimate based on text length if we can't read the file
            return 60.0
    
    def split_long_text(self, text: str, max_chars: int = 5000) -> list[str]:
        """
        Split long text into chunks for API limits.
        
        Args:
            text: Text to split
            max_chars: Maximum characters per chunk
        
        Returns:
            List of text chunks
        """
        if len(text) <= max_chars:
            return [text]
        
        # Split by sentences
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 <= max_chars:
                current_chunk += (" " + sentence if current_chunk else sentence)
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def generate_audio_with_chunks(
        self,
        text: str,
        output_filename: Optional[str] = None
    ) -> Path:
        """
        Generate audio from long text by splitting into chunks.
        
        Args:
            text: Text to convert (can be longer than API limits)
            output_filename: Optional filename for the output
        
        Returns:
            Path to the combined audio file
        """
        chunks = self.split_long_text(text)
        
        if len(chunks) == 1:
            return self.generate_audio(text, output_filename)
        
        logger.info(f"Splitting text into {len(chunks)} chunks")
        
        # Generate audio for each chunk
        chunk_paths = []
        for i, chunk in enumerate(chunks):
            chunk_filename = f"chunk_{i}_{generate_unique_id()}.mp3"
            chunk_path = self.generate_audio(chunk, chunk_filename)
            chunk_paths.append(chunk_path)
        
        # Combine audio files
        output_filename = output_filename or f"audio_{generate_unique_id()}.mp3"
        output_path = settings.audio_path / output_filename
        
        self._combine_audio_files(chunk_paths, output_path)
        
        # Clean up chunk files
        for chunk_path in chunk_paths:
            try:
                chunk_path.unlink()
            except Exception:
                pass
        
        return output_path
    
    def _combine_audio_files(self, audio_paths: list[Path], output_path: Path) -> None:
        """Combine multiple audio files into one."""
        from moviepy.editor import AudioFileClip, concatenate_audioclips
        
        clips = [AudioFileClip(str(path)) for path in audio_paths]
        combined = concatenate_audioclips(clips)
        combined.write_audiofile(str(output_path), logger=None)
        
        # Close clips
        for clip in clips:
            clip.close()
        combined.close()
    
    @staticmethod
    def list_elevenlabs_voices() -> list[dict]:
        """
        List available ElevenLabs voices.
        
        Returns:
            List of voice dictionaries with id and name
        """
        url = "https://api.elevenlabs.io/v1/voices"
        headers = {"xi-api-key": settings.elevenlabs_api_key}
        
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"ElevenLabs API error: {response.status_code}")
        
        voices = response.json().get("voices", [])
        return [{"id": v["voice_id"], "name": v["name"]} for v in voices]


if __name__ == "__main__":
    # Test the TTS engine
    engine = TTSEngine()
    
    test_text = """
    Did you know that honey never spoils? 
    Archaeologists have found 3000-year-old honey in Egyptian tombs that was still perfectly edible.
    The secret lies in honey's unique chemistry... low moisture content and acidic pH create an environment 
    where bacteria simply cannot survive.
    """
    
    audio_path = engine.generate_audio(test_text.strip(), "test_audio.mp3")
    print(f"\nAudio generated: {audio_path}")
    
    duration = engine.get_audio_duration(audio_path)
    print(f"Duration: {duration:.2f} seconds")
