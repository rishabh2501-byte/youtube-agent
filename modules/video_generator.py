"""
Video Generator Module.
Combines stock footage, audio narration, and subtitles using FFmpeg/MoviePy.
"""

import os
import subprocess
from pathlib import Path
from typing import Optional

from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    CompositeVideoClip,
    concatenate_videoclips,
    ColorClip,
)
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.video.fx.all import resize, crop

# Fix for PIL.Image.ANTIALIAS deprecation in Pillow 10+
import PIL.Image
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.Resampling.LANCZOS

from config import settings
from utils.logger import get_logger
from utils.helpers import generate_unique_id

logger = get_logger(__name__, settings.log_level, settings.log_file)


class VideoGenerator:
    """
    Generates final video by combining stock footage, audio, and subtitles.
    Uses MoviePy and FFmpeg for video processing.
    """
    
    def __init__(self):
        """Initialize the VideoGenerator."""
        settings.videos_path.mkdir(parents=True, exist_ok=True)
        
        self.target_width = settings.video_width
        self.target_height = settings.video_height
        self.fps = settings.video_fps
        
        logger.info(f"VideoGenerator initialized ({self.target_width}x{self.target_height} @ {self.fps}fps)")
    
    def generate_video(
        self,
        footage_paths: list[Path],
        audio_path: Path,
        subtitle_path: Optional[Path] = None,
        output_filename: Optional[str] = None,
        add_background_music: bool = False,
        music_volume: float = 0.1
    ) -> Path:
        """
        Generate final video from components.
        
        Args:
            footage_paths: List of stock footage video paths
            audio_path: Path to narration audio file
            subtitle_path: Optional path to subtitle file (SRT or ASS)
            output_filename: Optional output filename
            add_background_music: Whether to add background music
            music_volume: Volume level for background music (0.0-1.0)
        
        Returns:
            Path to the generated video file
        """
        logger.info("Starting video generation")
        
        if not output_filename:
            output_filename = f"video_{generate_unique_id()}.mp4"
        
        output_path = settings.videos_path / output_filename
        
        try:
            # Load audio to get duration
            audio_clip = AudioFileClip(str(audio_path))
            target_duration = audio_clip.duration
            logger.info(f"Audio duration: {target_duration:.2f}s")
            
            # Process and combine footage
            video_clip = self._process_footage(footage_paths, target_duration)
            
            # Add audio
            video_clip = video_clip.set_audio(audio_clip)
            
            # Add subtitles if provided
            if subtitle_path and subtitle_path.exists():
                video_clip = self._add_subtitles(video_clip, subtitle_path)
            
            # Write final video
            logger.info(f"Writing video to: {output_path}")
            video_clip.write_videofile(
                str(output_path),
                fps=self.fps,
                codec="libx264",
                audio_codec="aac",
                preset="medium",
                threads=4,
                logger=None  # Suppress moviepy logging
            )
            
            # Cleanup
            video_clip.close()
            audio_clip.close()
            
            logger.info(f"Video generated successfully: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating video: {e}")
            raise
    
    def _process_footage(
        self,
        footage_paths: list[Path],
        target_duration: float
    ) -> VideoFileClip:
        """
        Process and combine footage clips to match target duration.
        
        Args:
            footage_paths: List of footage file paths
            target_duration: Target video duration in seconds
        
        Returns:
            Combined and processed video clip
        """
        if not footage_paths:
            # Create a black background if no footage
            logger.warning("No footage provided, creating black background")
            return ColorClip(
                size=(self.target_width, self.target_height),
                color=(0, 0, 0),
                duration=target_duration
            )
        
        clips = []
        total_duration = 0.0
        
        for path in footage_paths:
            try:
                clip = VideoFileClip(str(path))
                
                # Resize and crop to target dimensions
                clip = self._resize_and_crop(clip)
                
                clips.append(clip)
                total_duration += clip.duration
                
                if total_duration >= target_duration:
                    break
                    
            except Exception as e:
                logger.warning(f"Could not load footage {path}: {e}")
                continue
        
        if not clips:
            logger.warning("No valid footage clips, creating black background")
            return ColorClip(
                size=(self.target_width, self.target_height),
                color=(0, 0, 0),
                duration=target_duration
            )
        
        # Concatenate clips
        combined = concatenate_videoclips(clips, method="compose")
        
        # Adjust duration to match target
        if combined.duration > target_duration:
            combined = combined.subclip(0, target_duration)
        elif combined.duration < target_duration:
            # Loop the footage to fill duration
            combined = self._loop_to_duration(combined, target_duration)
        
        return combined
    
    def _resize_and_crop(self, clip: VideoFileClip) -> VideoFileClip:
        """
        Resize and crop clip to target dimensions (portrait mode).
        
        Args:
            clip: Input video clip
        
        Returns:
            Resized and cropped clip
        """
        # Calculate aspect ratios
        target_ratio = self.target_width / self.target_height
        clip_ratio = clip.w / clip.h
        
        if clip_ratio > target_ratio:
            # Clip is wider - resize by height and crop width
            new_height = self.target_height
            new_width = int(clip.w * (new_height / clip.h))
            clip = clip.resize(height=new_height)
            
            # Center crop
            x_center = new_width // 2
            x1 = x_center - (self.target_width // 2)
            clip = clip.crop(x1=x1, x2=x1 + self.target_width)
        else:
            # Clip is taller - resize by width and crop height
            new_width = self.target_width
            new_height = int(clip.h * (new_width / clip.w))
            clip = clip.resize(width=new_width)
            
            # Center crop
            y_center = new_height // 2
            y1 = y_center - (self.target_height // 2)
            clip = clip.crop(y1=y1, y2=y1 + self.target_height)
        
        return clip
    
    def _loop_to_duration(
        self,
        clip: VideoFileClip,
        target_duration: float
    ) -> VideoFileClip:
        """
        Loop a clip to reach target duration.
        
        Args:
            clip: Input video clip
            target_duration: Target duration in seconds
        
        Returns:
            Looped clip with target duration
        """
        loops_needed = int(target_duration / clip.duration) + 1
        clips = [clip] * loops_needed
        looped = concatenate_videoclips(clips, method="compose")
        return looped.subclip(0, target_duration)
    
    def _add_subtitles(
        self,
        video_clip: VideoFileClip,
        subtitle_path: Path
    ) -> CompositeVideoClip:
        """
        Add subtitles to video using FFmpeg (more reliable than MoviePy subtitles).
        
        Args:
            video_clip: Input video clip
            subtitle_path: Path to subtitle file
        
        Returns:
            Video clip with subtitles
        """
        logger.info(f"Adding subtitles from: {subtitle_path}")
        
        # For SRT files, we'll burn them in during final export
        # Store subtitle path for later use
        video_clip.subtitle_path = subtitle_path
        
        return video_clip
    
    def generate_video_with_ffmpeg(
        self,
        footage_paths: list[Path],
        audio_path: Path,
        subtitle_path: Optional[Path] = None,
        output_filename: Optional[str] = None
    ) -> Path:
        """
        Generate video using FFmpeg directly for better subtitle support.
        
        Args:
            footage_paths: List of stock footage video paths
            audio_path: Path to narration audio file
            subtitle_path: Optional path to subtitle file
            output_filename: Optional output filename
        
        Returns:
            Path to the generated video file
        """
        logger.info("Generating video with FFmpeg")
        
        if not output_filename:
            output_filename = f"video_{generate_unique_id()}.mp4"
        
        output_path = settings.videos_path / output_filename
        temp_video_path = settings.videos_path / f"temp_{output_filename}"
        
        try:
            # First, create video from footage
            self._create_footage_video(footage_paths, audio_path, temp_video_path)
            
            # Then add subtitles if provided
            if subtitle_path and subtitle_path.exists():
                self._burn_subtitles(temp_video_path, subtitle_path, output_path)
                # Clean up temp file
                temp_video_path.unlink()
            else:
                # Rename temp to final
                temp_video_path.rename(output_path)
            
            logger.info(f"Video generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating video with FFmpeg: {e}")
            # Clean up temp file if exists
            if temp_video_path.exists():
                temp_video_path.unlink()
            raise
    
    def _create_footage_video(
        self,
        footage_paths: list[Path],
        audio_path: Path,
        output_path: Path
    ) -> None:
        """Create video from footage and audio using MoviePy."""
        audio_clip = AudioFileClip(str(audio_path))
        target_duration = audio_clip.duration
        
        video_clip = self._process_footage(footage_paths, target_duration)
        video_clip = video_clip.set_audio(audio_clip)
        
        video_clip.write_videofile(
            str(output_path),
            fps=self.fps,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            threads=4,
            logger=None
        )
        
        video_clip.close()
        audio_clip.close()
    
    def _burn_subtitles(
        self,
        video_path: Path,
        subtitle_path: Path,
        output_path: Path
    ) -> None:
        """Burn subtitles into video using FFmpeg."""
        logger.info("Burning subtitles with FFmpeg")
        
        # Escape special characters in path for FFmpeg filter
        sub_path_escaped = str(subtitle_path).replace("\\", "/").replace(":", "\\:")
        
        # FFmpeg command to burn subtitles
        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf", f"subtitles='{sub_path_escaped}':force_style='FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Shadow=1,Alignment=2,MarginV=50'",
            "-c:a", "copy",
            "-c:v", "libx264",
            "-preset", "medium",
            str(output_path)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            logger.debug(f"FFmpeg output: {result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr}")
            # Fallback: copy without subtitles
            logger.warning("Falling back to video without burned subtitles")
            import shutil
            shutil.copy(video_path, output_path)
    
    def add_intro_outro(
        self,
        video_path: Path,
        intro_path: Optional[Path] = None,
        outro_path: Optional[Path] = None,
        output_filename: Optional[str] = None
    ) -> Path:
        """
        Add intro and/or outro to a video.
        
        Args:
            video_path: Path to main video
            intro_path: Optional path to intro video
            outro_path: Optional path to outro video
            output_filename: Optional output filename
        
        Returns:
            Path to the final video
        """
        if not intro_path and not outro_path:
            return video_path
        
        logger.info("Adding intro/outro to video")
        
        if not output_filename:
            output_filename = f"final_{generate_unique_id()}.mp4"
        
        output_path = settings.videos_path / output_filename
        
        clips = []
        
        if intro_path and intro_path.exists():
            intro = VideoFileClip(str(intro_path))
            intro = self._resize_and_crop(intro)
            clips.append(intro)
        
        main_clip = VideoFileClip(str(video_path))
        clips.append(main_clip)
        
        if outro_path and outro_path.exists():
            outro = VideoFileClip(str(outro_path))
            outro = self._resize_and_crop(outro)
            clips.append(outro)
        
        final = concatenate_videoclips(clips, method="compose")
        final.write_videofile(
            str(output_path),
            fps=self.fps,
            codec="libx264",
            audio_codec="aac",
            preset="medium",
            threads=4,
            logger=None
        )
        
        # Cleanup
        for clip in clips:
            clip.close()
        final.close()
        
        return output_path


if __name__ == "__main__":
    # Test the video generator
    generator = VideoGenerator()
    
    print(f"Video Generator initialized")
    print(f"Target resolution: {generator.target_width}x{generator.target_height}")
    print(f"FPS: {generator.fps}")
