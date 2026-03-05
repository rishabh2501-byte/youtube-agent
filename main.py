"""
AI YouTube Agent - Main Orchestrator
Coordinates all modules to create and upload videos automatically.
"""

import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import settings
from utils.logger import get_logger
from utils.helpers import generate_unique_id, sanitize_filename

from modules.trending_fetcher import TrendingFetcher
from modules.topic_selector import TopicSelector
from modules.script_generator import ScriptGenerator
from modules.tts_engine import TTSEngine
from modules.stock_footage import StockFootageFetcher
from modules.video_generator import VideoGenerator
from modules.subtitle_generator import SubtitleGenerator
from modules.thumbnail_generator import ThumbnailGenerator
from modules.seo_generator import SEOGenerator
from modules.youtube_uploader import YouTubeUploader

logger = get_logger(__name__, settings.log_level, settings.log_file)


class YouTubeAgent:
    """
    Main orchestrator for the AI YouTube Agent.
    Coordinates all modules to create and upload videos automatically.
    """
    
    def __init__(self):
        """Initialize the YouTube Agent with all modules."""
        logger.info("=" * 60)
        logger.info("Initializing AI YouTube Agent")
        logger.info("=" * 60)
        
        # Ensure all directories exist
        settings.ensure_directories()
        
        # Initialize all modules
        self.trending_fetcher = TrendingFetcher()
        self.topic_selector = TopicSelector()
        self.script_generator = ScriptGenerator()
        self.tts_engine = TTSEngine()
        self.stock_fetcher = StockFootageFetcher()
        self.video_generator = VideoGenerator()
        self.subtitle_generator = SubtitleGenerator()
        self.thumbnail_generator = ThumbnailGenerator()
        self.seo_generator = SEOGenerator()
        self.youtube_uploader = YouTubeUploader()
        
        # Session tracking
        self.session_id = generate_unique_id("session")
        self.session_data = {}
        
        logger.info(f"Session ID: {self.session_id}")
        logger.info("All modules initialized successfully")
    
    def run(self, upload: bool = True, cleanup: bool = True) -> Optional[dict]:
        """
        Run the complete video creation and upload pipeline.
        
        Args:
            upload: Whether to upload to YouTube (set False for testing)
            cleanup: Whether to clean up intermediate files
        
        Returns:
            Dictionary with results or None if failed
        """
        logger.info("=" * 60)
        logger.info("Starting video creation pipeline")
        logger.info(f"Upload enabled: {upload}")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # Step 1: Fetch trending topics
            logger.info("\n[Step 1/10] Fetching trending topics...")
            topics = self.trending_fetcher.fetch_daily_trends()
            
            if not topics:
                logger.error("No trending topics found")
                return None
            
            logger.info(f"Found {len(topics)} trending topics")
            self.session_data["topics"] = topics
            
            # Step 2: Select best topic
            logger.info("\n[Step 2/10] Selecting best topic...")
            topic_analysis = self.topic_selector.select_topic(topics)
            
            selected_topic = topic_analysis["selected_topic"]
            angle = topic_analysis.get("angle", f"Interesting facts about {selected_topic}")
            keywords = topic_analysis.get("keywords", [selected_topic])
            tone = topic_analysis.get("tone", "educational")
            
            logger.info(f"Selected topic: {selected_topic}")
            logger.info(f"Angle: {angle}")
            self.session_data["topic_analysis"] = topic_analysis
            
            # Step 3: Generate script
            logger.info("\n[Step 3/10] Generating video script...")
            script_data = self.script_generator.generate_script(
                topic=selected_topic,
                angle=angle,
                tone=tone,
                duration_seconds=settings.video_duration_seconds
            )
            
            script = script_data["script"]
            logger.info(f"Script generated: {script_data['word_count']} words")
            logger.info(f"Estimated duration: {script_data['estimated_duration_seconds']:.1f}s")
            self.session_data["script_data"] = script_data
            
            # Step 4: Generate audio narration
            logger.info("\n[Step 4/10] Generating audio narration...")
            audio_filename = f"narration_{sanitize_filename(selected_topic)}.mp3"
            audio_path = self.tts_engine.generate_audio(script, audio_filename)
            
            audio_duration = self.tts_engine.get_audio_duration(audio_path)
            logger.info(f"Audio generated: {audio_duration:.1f}s")
            self.session_data["audio_path"] = audio_path
            self.session_data["audio_duration"] = audio_duration
            
            # Step 5: Fetch stock footage
            logger.info("\n[Step 5/10] Fetching stock footage...")
            footage_paths = self.stock_fetcher.fetch_footage_for_keywords(
                keywords=keywords,
                videos_per_keyword=3,
                total_duration_needed=audio_duration + 10  # Extra buffer
            )
            
            logger.info(f"Downloaded {len(footage_paths)} footage clips")
            self.session_data["footage_paths"] = footage_paths
            
            # Step 6: Generate subtitles
            logger.info("\n[Step 6/10] Generating subtitles...")
            subtitle_filename = f"subtitles_{sanitize_filename(selected_topic)}.srt"
            subtitle_path = self.subtitle_generator.generate_subtitles(
                script=script,
                audio_duration=audio_duration,
                output_filename=subtitle_filename
            )
            
            logger.info(f"Subtitles generated: {subtitle_path}")
            self.session_data["subtitle_path"] = subtitle_path
            
            # Step 7: Generate video
            logger.info("\n[Step 7/10] Generating video...")
            video_filename = f"video_{sanitize_filename(selected_topic)}.mp4"
            video_path = self.video_generator.generate_video_with_ffmpeg(
                footage_paths=footage_paths,
                audio_path=audio_path,
                subtitle_path=subtitle_path,
                output_filename=video_filename
            )
            
            logger.info(f"Video generated: {video_path}")
            self.session_data["video_path"] = video_path
            
            # Step 8: Generate thumbnail
            logger.info("\n[Step 8/10] Generating thumbnail...")
            thumbnail_path = self.thumbnail_generator.generate_thumbnail_with_text(
                topic=selected_topic,
                style="vibrant"
            )
            
            logger.info(f"Thumbnail generated: {thumbnail_path}")
            self.session_data["thumbnail_path"] = thumbnail_path
            
            # Step 9: Generate SEO metadata
            logger.info("\n[Step 9/10] Generating SEO metadata...")
            seo_metadata = self.seo_generator.generate_metadata(
                topic=selected_topic,
                angle=angle,
                script=script
            )
            
            logger.info(f"Title: {seo_metadata['title']}")
            logger.info(f"Tags: {len(seo_metadata['tags'])} tags generated")
            self.session_data["seo_metadata"] = seo_metadata
            
            # Step 10: Upload to YouTube
            video_id = None
            if upload:
                logger.info("\n[Step 10/10] Uploading to YouTube...")
                video_id = self.youtube_uploader.upload_video(
                    video_path=video_path,
                    title=seo_metadata["title"],
                    description=seo_metadata["description"],
                    tags=seo_metadata["tags"],
                    thumbnail_path=thumbnail_path
                )
                
                if video_id:
                    logger.info(f"Video uploaded successfully!")
                    logger.info(f"Video ID: {video_id}")
                    logger.info(f"URL: https://www.youtube.com/watch?v={video_id}")
                else:
                    logger.warning("Video upload failed")
            else:
                logger.info("\n[Step 10/10] Skipping upload (upload=False)")
            
            self.session_data["video_id"] = video_id
            
            # Cleanup intermediate files
            if cleanup and not settings.keep_intermediate_files:
                logger.info("\nCleaning up intermediate files...")
                self._cleanup_files(footage_paths)
            
            # Calculate total time
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Prepare results
            results = {
                "session_id": self.session_id,
                "topic": selected_topic,
                "angle": angle,
                "video_path": str(video_path),
                "thumbnail_path": str(thumbnail_path),
                "video_id": video_id,
                "video_url": f"https://www.youtube.com/watch?v={video_id}" if video_id else None,
                "title": seo_metadata["title"],
                "duration_seconds": audio_duration,
                "processing_time_seconds": duration,
                "timestamp": datetime.now().isoformat(),
            }
            
            logger.info("\n" + "=" * 60)
            logger.info("Pipeline completed successfully!")
            logger.info(f"Total processing time: {duration:.1f} seconds")
            logger.info("=" * 60)
            
            return results
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            logger.error(traceback.format_exc())
            return None
    
    def _cleanup_files(self, footage_paths: list[Path]) -> None:
        """Clean up intermediate files."""
        # Clean up downloaded footage
        self.stock_fetcher.cleanup_footage(footage_paths)
        
        # Clean up audio if not keeping
        if "audio_path" in self.session_data:
            try:
                self.session_data["audio_path"].unlink()
            except Exception:
                pass
    
    def run_dry(self) -> Optional[dict]:
        """
        Run the pipeline without uploading (dry run for testing).
        
        Returns:
            Dictionary with results or None if failed
        """
        return self.run(upload=False, cleanup=False)
    
    def create_video_from_topic(
        self,
        topic: str,
        angle: Optional[str] = None,
        upload: bool = True
    ) -> Optional[dict]:
        """
        Create a video from a specific topic (skip trending fetch).
        
        Args:
            topic: Topic for the video
            angle: Optional specific angle
            upload: Whether to upload to YouTube
        
        Returns:
            Dictionary with results or None if failed
        """
        logger.info(f"Creating video for custom topic: {topic}")
        
        # Create a mock topic analysis
        topic_analysis = {
            "selected_topic": topic,
            "angle": angle or f"Fascinating facts about {topic}",
            "keywords": [topic] + topic.lower().split()[:4],
            "tone": "educational",
        }
        
        return self.run_with_topic(topic_analysis, upload=upload)
    
    def run_with_topic(self, topic_analysis: dict, upload: bool = True, cleanup: bool = True) -> Optional[dict]:
        """
        Run the pipeline with a pre-selected topic (skips trending fetch and topic selection).
        
        Args:
            topic_analysis: Dictionary with selected_topic, angle, keywords, tone
            upload: Whether to upload to YouTube
            cleanup: Whether to clean up intermediate files
        
        Returns:
            Dictionary with results or None if failed
        """
        logger.info("=" * 60)
        logger.info("Starting video creation pipeline (custom topic)")
        logger.info(f"Upload enabled: {upload}")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        try:
            selected_topic = topic_analysis["selected_topic"]
            angle = topic_analysis.get("angle", f"Interesting facts about {selected_topic}")
            keywords = topic_analysis.get("keywords", [selected_topic])
            tone = topic_analysis.get("tone", "educational")
            
            logger.info(f"Topic: {selected_topic}")
            logger.info(f"Angle: {angle}")
            self.session_data["topic_analysis"] = topic_analysis
            
            # Step 3: Generate script
            logger.info("\n[Step 1/8] Generating video script...")
            script_data = self.script_generator.generate_script(
                topic=selected_topic,
                angle=angle,
                tone=tone,
                duration_seconds=settings.video_duration_seconds
            )
            
            script = script_data["script"]
            logger.info(f"Script generated: {script_data['word_count']} words")
            logger.info(f"Estimated duration: {script_data['estimated_duration_seconds']:.1f}s")
            self.session_data["script_data"] = script_data
            
            # Step 4: Generate audio narration
            logger.info("\n[Step 2/8] Generating audio narration...")
            audio_filename = f"narration_{sanitize_filename(selected_topic)}.mp3"
            audio_path = self.tts_engine.generate_audio(script, audio_filename)
            
            audio_duration = self.tts_engine.get_audio_duration(audio_path)
            logger.info(f"Audio generated: {audio_duration:.1f}s")
            self.session_data["audio_path"] = audio_path
            self.session_data["audio_duration"] = audio_duration
            
            # Step 5: Fetch stock footage
            logger.info("\n[Step 3/8] Fetching stock footage...")
            footage_paths = self.stock_fetcher.fetch_footage_for_keywords(
                keywords=keywords,
                videos_per_keyword=3,
                total_duration_needed=audio_duration + 10
            )
            
            logger.info(f"Downloaded {len(footage_paths)} footage clips")
            self.session_data["footage_paths"] = footage_paths
            
            # Step 6: Generate subtitles
            logger.info("\n[Step 4/8] Generating subtitles...")
            subtitle_filename = f"subtitles_{sanitize_filename(selected_topic)}.srt"
            subtitle_path = self.subtitle_generator.generate_subtitles(
                script=script,
                audio_duration=audio_duration,
                output_filename=subtitle_filename
            )
            
            logger.info(f"Subtitles generated: {subtitle_path}")
            self.session_data["subtitle_path"] = subtitle_path
            
            # Step 7: Generate video
            logger.info("\n[Step 5/8] Generating video...")
            video_filename = f"video_{sanitize_filename(selected_topic)}.mp4"
            video_path = self.video_generator.generate_video_with_ffmpeg(
                footage_paths=footage_paths,
                audio_path=audio_path,
                subtitle_path=subtitle_path,
                output_filename=video_filename
            )
            
            logger.info(f"Video generated: {video_path}")
            self.session_data["video_path"] = video_path
            
            # Step 8: Generate thumbnail
            logger.info("\n[Step 6/8] Generating thumbnail...")
            thumbnail_path = self.thumbnail_generator.generate_thumbnail_with_text(
                topic=selected_topic,
                style="vibrant"
            )
            
            logger.info(f"Thumbnail generated: {thumbnail_path}")
            self.session_data["thumbnail_path"] = thumbnail_path
            
            # Step 9: Generate SEO metadata
            logger.info("\n[Step 7/8] Generating SEO metadata...")
            seo_metadata = self.seo_generator.generate_metadata(
                topic=selected_topic,
                angle=angle,
                script=script
            )
            
            logger.info(f"Title: {seo_metadata['title']}")
            logger.info(f"Tags: {len(seo_metadata['tags'])} tags generated")
            self.session_data["seo_metadata"] = seo_metadata
            
            # Step 10: Upload to YouTube
            video_id = None
            if upload:
                logger.info("\n[Step 8/8] Uploading to YouTube...")
                video_id = self.youtube_uploader.upload_video(
                    video_path=video_path,
                    title=seo_metadata["title"],
                    description=seo_metadata["description"],
                    tags=seo_metadata["tags"],
                    thumbnail_path=thumbnail_path
                )
                
                if video_id:
                    logger.info(f"Video uploaded successfully!")
                    logger.info(f"Video ID: {video_id}")
                    logger.info(f"URL: https://www.youtube.com/watch?v={video_id}")
                else:
                    logger.warning("Video upload failed")
            else:
                logger.info("\n[Step 8/8] Skipping upload (upload=False)")
            
            self.session_data["video_id"] = video_id
            
            # Cleanup intermediate files
            if cleanup and not settings.keep_intermediate_files:
                logger.info("\nCleaning up intermediate files...")
                self._cleanup_files(footage_paths)
            
            # Calculate total time
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Prepare results
            results = {
                "session_id": self.session_id,
                "topic": selected_topic,
                "angle": angle,
                "video_path": str(video_path),
                "thumbnail_path": str(thumbnail_path),
                "video_id": video_id,
                "video_url": f"https://www.youtube.com/watch?v={video_id}" if video_id else None,
                "title": seo_metadata["title"],
                "duration_seconds": audio_duration,
                "processing_time_seconds": duration,
                "timestamp": datetime.now().isoformat(),
            }
            
            logger.info("\n" + "=" * 60)
            logger.info("Pipeline completed successfully!")
            logger.info(f"Total processing time: {duration:.1f} seconds")
            logger.info("=" * 60)
            
            return results
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            logger.error(traceback.format_exc())
            return None


def main():
    """Main entry point for the YouTube Agent."""
    import argparse
    
    parser = argparse.ArgumentParser(description="AI YouTube Agent")
    parser.add_argument(
        "--no-upload",
        action="store_true",
        help="Skip YouTube upload (dry run)"
    )
    parser.add_argument(
        "--topic",
        type=str,
        help="Use a specific topic instead of trending"
    )
    parser.add_argument(
        "--keep-files",
        action="store_true",
        help="Keep intermediate files"
    )
    
    args = parser.parse_args()
    
    # Create and run agent
    agent = YouTubeAgent()
    
    if args.topic:
        results = agent.create_video_from_topic(
            topic=args.topic,
            upload=not args.no_upload
        )
    else:
        results = agent.run(
            upload=not args.no_upload,
            cleanup=not args.keep_files
        )
    
    if results:
        print("\n" + "=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print(f"Topic: {results['topic']}")
        print(f"Title: {results['title']}")
        print(f"Video: {results['video_path']}")
        if results.get("video_url"):
            print(f"YouTube URL: {results['video_url']}")
        print(f"Processing Time: {results['processing_time_seconds']:.1f}s")
    else:
        print("\nPipeline failed. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
