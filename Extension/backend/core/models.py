# core/models.py - Data models and schemas
"""
Pydantic models for request/response schemas and internal data structures
"""

from pydantic import BaseModel, Field
from typing import Optional

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
