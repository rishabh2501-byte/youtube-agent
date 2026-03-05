"""
Stock Footage Fetcher Module.
Fetches relevant stock videos from Pexels API.
"""

import os
import time
from pathlib import Path
from typing import Optional

import requests

from config import settings
from utils.logger import get_logger
from utils.helpers import generate_unique_id, sanitize_filename, retry_with_backoff

logger = get_logger(__name__, settings.log_level, settings.log_file)


class StockFootageFetcher:
    """
    Fetches stock video footage from Pexels API.
    Downloads videos based on keywords for video production.
    """
    
    PEXELS_API_URL = "https://api.pexels.com/videos/search"
    PIXABAY_API_URL = "https://pixabay.com/api/videos/"
    
    # Fallback keywords that always have good footage
    FALLBACK_KEYWORDS = [
        "nature", "landscape", "ocean", "mountains", "forest", "sunset",
        "city", "travel", "sky", "clouds", "water", "beach", "stars",
        "earth", "planet", "aerial", "drone", "timelapse", "abstract"
    ]
    
    def __init__(self):
        """Initialize the StockFootageFetcher."""
        self.api_key = settings.pexels_api_key
        self.pixabay_key = getattr(settings, 'pixabay_api_key', '')
        self.headers = {"Authorization": self.api_key}
        
        # Create temp directory for downloaded footage
        self.footage_dir = settings.output_path / "footage"
        self.footage_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("StockFootageFetcher initialized")
    
    def search_videos(
        self,
        query: str,
        per_page: int = 10,
        orientation: str = "portrait",
        size: str = "medium"
    ) -> list[dict]:
        """
        Search for videos on Pexels or Pixabay.
        
        Args:
            query: Search query
            per_page: Number of results per page
            orientation: Video orientation (landscape, portrait, square)
            size: Video size (large, medium, small)
        
        Returns:
            List of video metadata dictionaries
        """
        # Try Pexels first if API key exists
        if self.api_key:
            videos = self._search_pexels(query, per_page, orientation, size)
            if videos:
                return videos
        
        # Fallback to Pixabay (free, more reliable)
        return self._search_pixabay(query, per_page)
    
    def _search_pexels(self, query: str, per_page: int, orientation: str, size: str) -> list[dict]:
        """Search Pexels API."""
        logger.info(f"Searching Pexels for: {query}")
        
        params = {
            "query": query,
            "per_page": per_page,
            "orientation": orientation,
            "size": size,
        }
        
        try:
            response = requests.get(
                self.PEXELS_API_URL,
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            videos = data.get("videos", [])
            
            logger.info(f"Found {len(videos)} videos for query: {query}")
            
            return [self._parse_video_data(v) for v in videos]
            
        except Exception as e:
            logger.error(f"Pexels error: {e}")
            return []
    
    def _search_pixabay(self, query: str, per_page: int = 10) -> list[dict]:
        """Search Pixabay API (free, no key required for limited use)."""
        logger.info(f"Searching Pixabay for: {query}")
        
        # Pixabay free API key (public demo key)
        pixabay_key = self.pixabay_key or "25921830-87ed2f8b9e5e92f0e64648d8b"
        
        params = {
            "key": pixabay_key,
            "q": query,
            "video_type": "film",
            "per_page": per_page,
        }
        
        try:
            response = requests.get(self.PIXABAY_API_URL, params=params)
            response.raise_for_status()
            
            data = response.json()
            videos = data.get("hits", [])
            
            logger.info(f"Found {len(videos)} videos on Pixabay for: {query}")
            
            return [self._parse_pixabay_video(v) for v in videos]
            
        except Exception as e:
            logger.error(f"Pixabay error: {e}")
            return []
    
    def _parse_pixabay_video(self, video: dict) -> dict:
        """Parse Pixabay video data."""
        videos = video.get("videos", {})
        # Prefer medium quality for balance of size/quality
        best = videos.get("medium", videos.get("small", videos.get("tiny", {})))
        
        return {
            "id": video.get("id"),
            "url": video.get("pageURL"),
            "duration": video.get("duration", 10),
            "width": best.get("width"),
            "height": best.get("height"),
            "download_url": best.get("url"),
            "quality": "medium",
            "user": video.get("user"),
        }
    
    def _parse_video_data(self, video: dict) -> dict:
        """Parse Pexels video data into a cleaner format."""
        # Get the best quality video file
        video_files = video.get("video_files", [])
        
        # Sort by quality (prefer HD)
        hd_files = [f for f in video_files if f.get("quality") == "hd"]
        sd_files = [f for f in video_files if f.get("quality") == "sd"]
        
        best_file = (hd_files or sd_files or video_files)[0] if video_files else {}
        
        return {
            "id": video.get("id"),
            "url": video.get("url"),
            "duration": video.get("duration"),
            "width": best_file.get("width"),
            "height": best_file.get("height"),
            "download_url": best_file.get("link"),
            "quality": best_file.get("quality"),
            "user": video.get("user", {}).get("name"),
        }
    
    @retry_with_backoff(max_attempts=3, min_wait=1, max_wait=10)
    def download_video(
        self,
        video_data: dict,
        filename: Optional[str] = None
    ) -> Optional[Path]:
        """
        Download a video from Pexels.
        
        Args:
            video_data: Video metadata from search_videos
            filename: Optional custom filename
        
        Returns:
            Path to downloaded video file or None if failed
        """
        download_url = video_data.get("download_url")
        if not download_url:
            logger.error("No download URL in video data")
            return None
        
        video_id = video_data.get("id", generate_unique_id())
        filename = filename or f"footage_{video_id}.mp4"
        output_path = self.footage_dir / filename
        
        logger.info(f"Downloading video: {video_id}")
        
        try:
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            return None
    
    def fetch_footage_for_keywords(
        self,
        keywords: list[str],
        videos_per_keyword: int = 3,
        total_duration_needed: float = 60.0
    ) -> list[Path]:
        """
        Fetch footage for multiple keywords until duration is met.
        
        Args:
            keywords: List of search keywords
            videos_per_keyword: Max videos to fetch per keyword
            total_duration_needed: Total video duration needed in seconds
        
        Returns:
            List of paths to downloaded video files
        """
        logger.info(f"Fetching footage for keywords: {keywords}")
        
        downloaded_paths = []
        total_duration = 0.0
        
        # Try original keywords first
        for keyword in keywords:
            if total_duration >= total_duration_needed:
                break
            
            # Search for videos
            videos = self.search_videos(keyword, per_page=videos_per_keyword)
            
            for video in videos:
                if total_duration >= total_duration_needed:
                    break
                
                # Download the video
                path = self.download_video(video)
                if path:
                    downloaded_paths.append(path)
                    total_duration += video.get("duration", 10)
                
                # Rate limiting
                time.sleep(0.5)
        
        # If no footage found, use fallback keywords (these always work)
        if not downloaded_paths or total_duration < total_duration_needed:
            logger.warning("Using fallback keywords to ensure video has footage")
            import random
            fallback_keywords = random.sample(self.FALLBACK_KEYWORDS, min(5, len(self.FALLBACK_KEYWORDS)))
            
            for keyword in fallback_keywords:
                if total_duration >= total_duration_needed:
                    break
                
                videos = self.search_videos(keyword, per_page=videos_per_keyword)
                
                for video in videos:
                    if total_duration >= total_duration_needed:
                        break
                    
                    path = self.download_video(video)
                    if path:
                        downloaded_paths.append(path)
                        total_duration += video.get("duration", 10)
                    
                    time.sleep(0.5)
        
        logger.info(f"Downloaded {len(downloaded_paths)} videos, total duration: {total_duration:.1f}s")
        return downloaded_paths
    
    def get_video_duration(self, video_path: Path) -> float:
        """
        Get the duration of a video file.
        
        Args:
            video_path: Path to video file
        
        Returns:
            Duration in seconds
        """
        try:
            from moviepy.editor import VideoFileClip
            
            with VideoFileClip(str(video_path)) as clip:
                return clip.duration
                
        except Exception as e:
            logger.error(f"Error getting video duration: {e}")
            return 0.0
    
    def cleanup_footage(self, paths: list[Path]) -> None:
        """
        Clean up downloaded footage files.
        
        Args:
            paths: List of file paths to delete
        """
        for path in paths:
            try:
                if path.exists():
                    path.unlink()
                    logger.debug(f"Deleted: {path}")
            except Exception as e:
                logger.warning(f"Could not delete {path}: {e}")
    
    def search_by_topic(
        self,
        topic: str,
        angle: str,
        additional_keywords: Optional[list[str]] = None
    ) -> list[dict]:
        """
        Search for videos based on topic and angle.
        Generates relevant search queries automatically.
        
        Args:
            topic: Main topic
            angle: Specific angle or perspective
            additional_keywords: Extra keywords to include
        
        Returns:
            List of video metadata
        """
        # Generate search queries from topic and angle
        queries = [topic]
        
        # Add words from angle
        angle_words = [w for w in angle.split() if len(w) > 3]
        queries.extend(angle_words[:3])
        
        # Add additional keywords
        if additional_keywords:
            queries.extend(additional_keywords)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for q in queries:
            q_lower = q.lower()
            if q_lower not in seen:
                seen.add(q_lower)
                unique_queries.append(q)
        
        all_videos = []
        for query in unique_queries[:5]:  # Limit to 5 queries
            videos = self.search_videos(query, per_page=5)
            all_videos.extend(videos)
            time.sleep(0.3)  # Rate limiting
        
        return all_videos


if __name__ == "__main__":
    # Test the stock footage fetcher
    fetcher = StockFootageFetcher()
    
    # Search for videos
    videos = fetcher.search_videos("nature sunset", per_page=3)
    
    print("\n=== Search Results ===")
    for video in videos:
        print(f"ID: {video['id']}, Duration: {video['duration']}s, Quality: {video['quality']}")
    
    # Download first video
    if videos:
        path = fetcher.download_video(videos[0])
        if path:
            print(f"\nDownloaded: {path}")
            duration = fetcher.get_video_duration(path)
            print(f"Duration: {duration:.2f}s")
