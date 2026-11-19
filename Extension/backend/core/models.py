# core/models.py - Data models and schemas
"""
Pydantic models for request/response schemas and internal data structures
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import time

class TaskStatus(str, Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class FormatInfo(BaseModel):
    """Video format information"""
    format_id: str
    resolution: str
    filesize: str
    format_note: str = "N/A"
    ext: str
    bitrate: Optional[int] = None
    fps: Optional[int] = None

class VideoInfo(BaseModel):
    """Video information response"""
    type: str = "video"
    title: str
    thumbnail: str = ""
    duration: int = 0
    formats: List[FormatInfo] = []
    uploader: Optional[str] = None
    upload_date: Optional[str] = None
    view_count: Optional[int] = None

class PlaylistInfo(BaseModel):
    """Playlist information response"""
    type: str = "playlist"
    title: str
    thumbnail: str = ""
    video_count: int
    videos: List[Dict[str, Any]] = []  # Changed to Dict to support flexible video data

class DownloadRequest(BaseModel):
    """Download request schema"""
    url: str = Field(..., min_length=1, description="Video URL")
    format_id: str = Field(..., min_length=1, description="Format ID to download")
    format_type: str = Field(default="mp4", description="Output format type")
    download_location: Optional[str] = Field(default=None, description="Custom download location")
    cookies: Optional[str] = Field(default=None, description="YouTube cookies in Netscape format")
    
    @validator('url')
    def validate_url(cls, v):
        if not v.strip():
            raise ValueError('URL cannot be empty')
        return v.strip()
    
    @validator('format_type')
    def validate_format_type(cls, v):
        allowed_formats = ['mp4', 'mp3', 'webm', 'mkv']
        if v.lower() not in allowed_formats:
            raise ValueError(f'Format must be one of: {allowed_formats}')
        return v.lower()

class DownloadWithCookiesRequest(BaseModel):
    """Download request schema with cookies"""
    url: str = Field(..., min_length=1, description="Video URL")
    format_id: str = Field(default="best", description="Format ID to download")
    format_type: str = Field(default="mp4", description="Output format type")
    cookies: str = Field(..., min_length=1, description="YouTube cookies in Netscape format")
    download_location: Optional[str] = Field(default=None, description="Custom download location")

class DownloadResponse(BaseModel):
    """Download response schema"""
    success: bool
    message: str
    task_id: str
    queue_position: int
    estimated_wait_time: str
    download_location: str
    video_title: Optional[str] = None

class DownloadTask:
    """Internal download task class"""
    
    def __init__(self, request: DownloadRequest):
        self.id = f"task_{int(time.time() * 1000)}"
        self.url = request.url
        self.format_id = request.format_id
        self.format_type = request.format_type
        self.download_location = request.download_location
        self.cookies = request.cookies  # Add cookies support
        self.status = TaskStatus.QUEUED
        self.progress = 0
        self.filename = None
        self.error = None
        self.start_time = None
        self.completion_time = None
        self.created_at = datetime.now()
        self.video_title = None
        self.thumbnail = None
        self.file_size = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for API responses"""
        return {
            "id": self.id,
            "url": self.url,
            "format_id": self.format_id,
            "format_type": self.format_type,
            "status": self.status.value,
            "progress": self.progress,
            "filename": self.filename,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "completion_time": self.completion_time.isoformat() if self.completion_time else None,
            "video_title": self.video_title,
            "thumbnail": self.thumbnail,
            "file_size": self.file_size,
            "download_location": self.download_location
        }

class QueueStatus(BaseModel):
    """Queue status response"""
    total_queue_size: int
    active_downloads: int
    queued_downloads: List[Dict[str, Any]]
    active_tasks: List[Dict[str, Any]]
    server_uptime: str