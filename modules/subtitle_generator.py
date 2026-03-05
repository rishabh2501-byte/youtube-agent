"""
Subtitle Generator Module.
Generates SRT subtitles from script text with proper timing.
"""

import re
from pathlib import Path
from typing import Optional

from config import settings
from utils.logger import get_logger
from utils.helpers import generate_unique_id, format_timestamp_srt, chunk_text

logger = get_logger(__name__, settings.log_level, settings.log_file)


class SubtitleGenerator:
    """
    Generates SRT subtitle files from script text.
    Calculates timing based on speech rate and audio duration.
    """
    
    def __init__(self):
        """Initialize the SubtitleGenerator."""
        settings.subtitles_path.mkdir(parents=True, exist_ok=True)
        logger.info("SubtitleGenerator initialized")
    
    def generate_subtitles(
        self,
        script: str,
        audio_duration: float,
        output_filename: Optional[str] = None,
        max_chars_per_line: int = 42,
        max_lines: int = 2
    ) -> Path:
        """
        Generate SRT subtitles from script text.
        
        Args:
            script: The script text
            audio_duration: Total audio duration in seconds
            output_filename: Optional output filename
            max_chars_per_line: Maximum characters per subtitle line
            max_lines: Maximum lines per subtitle block
        
        Returns:
            Path to the generated SRT file
        """
        logger.info(f"Generating subtitles for {audio_duration:.1f}s audio")
        
        # Generate filename if not provided
        if not output_filename:
            output_filename = f"subtitles_{generate_unique_id()}.srt"
        
        output_path = settings.subtitles_path / output_filename
        
        # Split script into subtitle chunks
        chunks = self._split_into_chunks(script, max_chars_per_line, max_lines)
        
        # Calculate timing for each chunk
        timed_chunks = self._calculate_timing(chunks, audio_duration)
        
        # Generate SRT content
        srt_content = self._generate_srt_content(timed_chunks)
        
        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(srt_content)
        
        logger.info(f"Subtitles generated: {output_path} ({len(chunks)} blocks)")
        return output_path
    
    def _split_into_chunks(
        self,
        text: str,
        max_chars_per_line: int,
        max_lines: int
    ) -> list[str]:
        """
        Split text into subtitle-sized chunks.
        
        Args:
            text: Text to split
            max_chars_per_line: Max characters per line
            max_lines: Max lines per subtitle
        
        Returns:
            List of subtitle text chunks
        """
        max_chars = max_chars_per_line * max_lines
        
        # Clean the text
        text = text.strip()
        text = re.sub(r'\s+', ' ', text)
        
        # Split by sentences first
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If sentence itself is too long, split by clauses/phrases
            if len(sentence) > max_chars:
                # Split by commas, semicolons, or conjunctions
                parts = re.split(r'(?<=[,;])\s+|(?:\s+(?:and|but|or|so|then)\s+)', sentence)
                
                for part in parts:
                    part = part.strip()
                    if not part:
                        continue
                    
                    if len(current_chunk) + len(part) + 1 <= max_chars:
                        current_chunk += (" " + part if current_chunk else part)
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        
                        # If part is still too long, split by words
                        if len(part) > max_chars:
                            words = part.split()
                            current_chunk = ""
                            for word in words:
                                if len(current_chunk) + len(word) + 1 <= max_chars:
                                    current_chunk += (" " + word if current_chunk else word)
                                else:
                                    if current_chunk:
                                        chunks.append(current_chunk.strip())
                                    current_chunk = word
                        else:
                            current_chunk = part
            
            elif len(current_chunk) + len(sentence) + 1 <= max_chars:
                current_chunk += (" " + sentence if current_chunk else sentence)
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _calculate_timing(
        self,
        chunks: list[str],
        total_duration: float
    ) -> list[dict]:
        """
        Calculate start and end times for each subtitle chunk.
        
        Args:
            chunks: List of subtitle text chunks
            total_duration: Total audio duration in seconds
        
        Returns:
            List of dicts with text, start_time, end_time
        """
        if not chunks:
            return []
        
        # Calculate total character count for proportional timing
        total_chars = sum(len(chunk) for chunk in chunks)
        
        timed_chunks = []
        current_time = 0.0
        
        for chunk in chunks:
            # Calculate duration proportional to text length
            # Add minimum duration to ensure readability
            char_ratio = len(chunk) / total_chars
            duration = max(char_ratio * total_duration, 1.5)  # Min 1.5 seconds
            
            # Ensure we don't exceed total duration
            if current_time + duration > total_duration:
                duration = total_duration - current_time
            
            end_time = min(current_time + duration, total_duration)
            
            timed_chunks.append({
                "text": chunk,
                "start_time": current_time,
                "end_time": end_time,
            })
            
            current_time = end_time
        
        return timed_chunks
    
    def _generate_srt_content(self, timed_chunks: list[dict]) -> str:
        """
        Generate SRT file content from timed chunks.
        
        Args:
            timed_chunks: List of chunks with timing info
        
        Returns:
            SRT formatted string
        """
        srt_lines = []
        
        for i, chunk in enumerate(timed_chunks, 1):
            # Subtitle number
            srt_lines.append(str(i))
            
            # Timestamp line
            start_ts = format_timestamp_srt(chunk["start_time"])
            end_ts = format_timestamp_srt(chunk["end_time"])
            srt_lines.append(f"{start_ts} --> {end_ts}")
            
            # Text (wrap long lines)
            text = self._wrap_subtitle_text(chunk["text"], max_width=42)
            srt_lines.append(text)
            
            # Blank line between subtitles
            srt_lines.append("")
        
        return "\n".join(srt_lines)
    
    def _wrap_subtitle_text(self, text: str, max_width: int = 42) -> str:
        """
        Wrap subtitle text to fit within max width.
        
        Args:
            text: Text to wrap
            max_width: Maximum characters per line
        
        Returns:
            Wrapped text with newlines
        """
        if len(text) <= max_width:
            return text
        
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line) + len(word) + 1 <= max_width:
                current_line += (" " + word if current_line else word)
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # Limit to 2 lines
        return "\n".join(lines[:2])
    
    def generate_ass_subtitles(
        self,
        script: str,
        audio_duration: float,
        output_filename: Optional[str] = None,
        font_name: str = "Arial",
        font_size: int = 24,
        primary_color: str = "&H00FFFFFF",  # White
        outline_color: str = "&H00000000",  # Black
    ) -> Path:
        """
        Generate ASS (Advanced SubStation Alpha) subtitles with styling.
        
        Args:
            script: The script text
            audio_duration: Total audio duration in seconds
            output_filename: Optional output filename
            font_name: Font family name
            font_size: Font size
            primary_color: Text color in ASS format
            outline_color: Outline color in ASS format
        
        Returns:
            Path to the generated ASS file
        """
        logger.info("Generating styled ASS subtitles")
        
        if not output_filename:
            output_filename = f"subtitles_{generate_unique_id()}.ass"
        
        output_path = settings.subtitles_path / output_filename
        
        # Split and time the chunks
        chunks = self._split_into_chunks(script, 42, 2)
        timed_chunks = self._calculate_timing(chunks, audio_duration)
        
        # Generate ASS content
        ass_content = self._generate_ass_content(
            timed_chunks, font_name, font_size, primary_color, outline_color
        )
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(ass_content)
        
        logger.info(f"ASS subtitles generated: {output_path}")
        return output_path
    
    def _generate_ass_content(
        self,
        timed_chunks: list[dict],
        font_name: str,
        font_size: int,
        primary_color: str,
        outline_color: str
    ) -> str:
        """Generate ASS file content."""
        # ASS header
        header = f"""[Script Info]
Title: YouTube Video Subtitles
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font_name},{font_size},{primary_color},&H000000FF,{outline_color},&H80000000,-1,0,0,0,100,100,0,0,1,2,1,2,10,10,50,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        # Generate dialogue lines
        dialogues = []
        for chunk in timed_chunks:
            start = self._format_ass_time(chunk["start_time"])
            end = self._format_ass_time(chunk["end_time"])
            text = chunk["text"].replace("\n", "\\N")
            dialogues.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}")
        
        return header + "\n".join(dialogues)
    
    def _format_ass_time(self, seconds: float) -> str:
        """Format seconds to ASS timestamp (H:MM:SS.cc)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centis = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


if __name__ == "__main__":
    # Test the subtitle generator
    generator = SubtitleGenerator()
    
    test_script = """
    Did you know that honey never spoils? Archaeologists have found 3000-year-old honey 
    in Egyptian tombs that was still perfectly edible. The secret lies in honey's unique 
    chemistry. Its low moisture content and acidic pH create an environment where bacteria 
    simply cannot survive. So next time you see honey, remember you're looking at nature's 
    perfect preservative. If you found this interesting, hit that subscribe button!
    """
    
    srt_path = generator.generate_subtitles(test_script.strip(), audio_duration=45.0)
    print(f"\nSRT generated: {srt_path}")
    
    # Print content
    with open(srt_path, "r") as f:
        print(f"\nContent:\n{f.read()}")
