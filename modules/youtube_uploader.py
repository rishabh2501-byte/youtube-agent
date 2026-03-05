"""
YouTube Uploader Module.
Uploads videos to YouTube using the YouTube Data API v3.
"""

import os
import pickle
import time
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from config import settings
from utils.logger import get_logger
from utils.helpers import retry_with_backoff

logger = get_logger(__name__, settings.log_level, settings.log_file)

# YouTube API scopes
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# Retry settings for resumable uploads
MAX_RETRIES = 10
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]


class YouTubeUploader:
    """
    Uploads videos to YouTube using the Data API v3.
    Handles OAuth authentication and resumable uploads.
    """
    
    def __init__(self):
        """Initialize the YouTubeUploader."""
        self.credentials = None
        self.youtube = None
        
        # Paths for credentials
        self.client_secrets_path = settings.base_dir / settings.youtube_client_secrets_file
        self.token_path = settings.base_dir / settings.youtube_token_file
        
        logger.info("YouTubeUploader initialized")
    
    def authenticate(self) -> bool:
        """
        Authenticate with YouTube API using OAuth 2.0.
        
        Returns:
            True if authentication successful, False otherwise
        """
        logger.info("Authenticating with YouTube API")
        
        try:
            # Check for existing token
            if self.token_path.exists():
                with open(self.token_path, "rb") as token_file:
                    self.credentials = pickle.load(token_file)
            
            # Refresh or get new credentials
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    logger.info("Refreshing expired credentials")
                    self.credentials.refresh(Request())
                else:
                    logger.info("Getting new credentials via OAuth flow")
                    
                    if not self.client_secrets_path.exists():
                        logger.error(f"Client secrets file not found: {self.client_secrets_path}")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.client_secrets_path),
                        SCOPES
                    )
                    self.credentials = flow.run_local_server(port=8080)
                
                # Save credentials for future use
                self.token_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.token_path, "wb") as token_file:
                    pickle.dump(self.credentials, token_file)
            
            # Build YouTube API client
            self.youtube = build("youtube", "v3", credentials=self.credentials)
            
            logger.info("YouTube authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"YouTube authentication failed: {e}")
            return False
    
    def upload_video(
        self,
        video_path: Path,
        title: str,
        description: str,
        tags: list[str],
        category_id: Optional[str] = None,
        privacy_status: Optional[str] = None,
        thumbnail_path: Optional[Path] = None
    ) -> Optional[str]:
        """
        Upload a video to YouTube.
        
        Args:
            video_path: Path to the video file
            title: Video title
            description: Video description
            tags: List of video tags
            category_id: YouTube category ID
            privacy_status: Privacy status (public, private, unlisted)
            thumbnail_path: Optional path to thumbnail image
        
        Returns:
            Video ID if successful, None otherwise
        """
        if not self.youtube:
            if not self.authenticate():
                return None
        
        logger.info(f"Uploading video: {title}")
        
        category_id = category_id or settings.youtube_category_id
        privacy_status = privacy_status or settings.youtube_privacy_status
        
        # Prepare video metadata
        body = {
            "snippet": {
                "title": title[:100],  # Max 100 chars
                "description": description[:5000],  # Max 5000 chars
                "tags": tags[:500],  # Max 500 tags
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            }
        }
        
        # Create media upload
        media = MediaFileUpload(
            str(video_path),
            mimetype="video/mp4",
            resumable=True,
            chunksize=1024 * 1024  # 1MB chunks
        )
        
        try:
            # Execute upload with retry logic
            video_id = self._resumable_upload(body, media)
            
            if video_id:
                logger.info(f"Video uploaded successfully: {video_id}")
                
                # Upload thumbnail if provided
                if thumbnail_path and thumbnail_path.exists():
                    self._upload_thumbnail(video_id, thumbnail_path)
                
                return video_id
            
            return None
            
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return None
    
    def _resumable_upload(self, body: dict, media: MediaFileUpload) -> Optional[str]:
        """
        Execute resumable upload with retry logic.
        
        Args:
            body: Video metadata
            media: Media file upload object
        
        Returns:
            Video ID if successful, None otherwise
        """
        request = self.youtube.videos().insert(
            part=",".join(body.keys()),
            body=body,
            media_body=media
        )
        
        response = None
        retry = 0
        
        while response is None:
            try:
                logger.info("Uploading chunk...")
                status, response = request.next_chunk()
                
                if status:
                    progress = int(status.progress() * 100)
                    logger.info(f"Upload progress: {progress}%")
                    
            except HttpError as e:
                if e.resp.status in RETRIABLE_STATUS_CODES:
                    retry += 1
                    if retry > MAX_RETRIES:
                        logger.error("Max retries exceeded")
                        return None
                    
                    sleep_time = 2 ** retry
                    logger.warning(f"Retriable error, sleeping {sleep_time}s...")
                    time.sleep(sleep_time)
                else:
                    raise
        
        return response.get("id")
    
    def _upload_thumbnail(self, video_id: str, thumbnail_path: Path) -> bool:
        """
        Upload a custom thumbnail for a video.
        
        Args:
            video_id: YouTube video ID
            thumbnail_path: Path to thumbnail image
        
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Uploading thumbnail for video: {video_id}")
        
        try:
            media = MediaFileUpload(
                str(thumbnail_path),
                mimetype="image/png"
            )
            
            self.youtube.thumbnails().set(
                videoId=video_id,
                media_body=media
            ).execute()
            
            logger.info("Thumbnail uploaded successfully")
            return True
            
        except HttpError as e:
            logger.error(f"Thumbnail upload error: {e}")
            return False
    
    def get_video_status(self, video_id: str) -> Optional[dict]:
        """
        Get the processing status of an uploaded video.
        
        Args:
            video_id: YouTube video ID
        
        Returns:
            Status dictionary or None
        """
        if not self.youtube:
            if not self.authenticate():
                return None
        
        try:
            response = self.youtube.videos().list(
                part="status,processingDetails",
                id=video_id
            ).execute()
            
            if response.get("items"):
                item = response["items"][0]
                return {
                    "privacy_status": item["status"]["privacyStatus"],
                    "upload_status": item["status"]["uploadStatus"],
                    "processing_status": item.get("processingDetails", {}).get("processingStatus"),
                }
            
            return None
            
        except HttpError as e:
            logger.error(f"Error getting video status: {e}")
            return None
    
    def update_video_metadata(
        self,
        video_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[list[str]] = None
    ) -> bool:
        """
        Update metadata for an existing video.
        
        Args:
            video_id: YouTube video ID
            title: New title (optional)
            description: New description (optional)
            tags: New tags (optional)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.youtube:
            if not self.authenticate():
                return False
        
        logger.info(f"Updating metadata for video: {video_id}")
        
        try:
            # Get current video data
            response = self.youtube.videos().list(
                part="snippet",
                id=video_id
            ).execute()
            
            if not response.get("items"):
                logger.error("Video not found")
                return False
            
            snippet = response["items"][0]["snippet"]
            
            # Update fields
            if title:
                snippet["title"] = title[:100]
            if description:
                snippet["description"] = description[:5000]
            if tags:
                snippet["tags"] = tags[:500]
            
            # Execute update
            self.youtube.videos().update(
                part="snippet",
                body={
                    "id": video_id,
                    "snippet": snippet
                }
            ).execute()
            
            logger.info("Metadata updated successfully")
            return True
            
        except HttpError as e:
            logger.error(f"Error updating metadata: {e}")
            return False
    
    def delete_video(self, video_id: str) -> bool:
        """
        Delete a video from YouTube.
        
        Args:
            video_id: YouTube video ID
        
        Returns:
            True if successful, False otherwise
        """
        if not self.youtube:
            if not self.authenticate():
                return False
        
        logger.info(f"Deleting video: {video_id}")
        
        try:
            self.youtube.videos().delete(id=video_id).execute()
            logger.info("Video deleted successfully")
            return True
            
        except HttpError as e:
            logger.error(f"Error deleting video: {e}")
            return False
    
    def get_channel_info(self) -> Optional[dict]:
        """
        Get information about the authenticated channel.
        
        Returns:
            Channel info dictionary or None
        """
        if not self.youtube:
            if not self.authenticate():
                return None
        
        try:
            response = self.youtube.channels().list(
                part="snippet,statistics",
                mine=True
            ).execute()
            
            if response.get("items"):
                item = response["items"][0]
                return {
                    "id": item["id"],
                    "title": item["snippet"]["title"],
                    "description": item["snippet"]["description"],
                    "subscriber_count": item["statistics"].get("subscriberCount"),
                    "video_count": item["statistics"].get("videoCount"),
                    "view_count": item["statistics"].get("viewCount"),
                }
            
            return None
            
        except HttpError as e:
            logger.error(f"Error getting channel info: {e}")
            return None


if __name__ == "__main__":
    # Test the YouTube uploader
    uploader = YouTubeUploader()
    
    print("YouTubeUploader initialized")
    print(f"Client secrets path: {uploader.client_secrets_path}")
    print(f"Token path: {uploader.token_path}")
    
    # Test authentication (requires valid credentials)
    # if uploader.authenticate():
    #     info = uploader.get_channel_info()
    #     if info:
    #         print(f"\nChannel: {info['title']}")
    #         print(f"Subscribers: {info['subscriber_count']}")
