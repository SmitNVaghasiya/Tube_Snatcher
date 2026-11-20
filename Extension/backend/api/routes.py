# api/routes.py - API routes for the extension backend
"""
API routes for video downloading functionality
Separated from main app for better organization
"""

from fastapi import APIRouter, Form, HTTPException, Request
from typing import Optional
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone

from core.video_fetcher import VideoFetcher
from core.models import DownloadResponse, DownloadWithCookiesRequest
from core.config import settings
from core.auth import create_access_token
from core.utils import get_client_ip, get_user_agent, validate_youtube_url
from core.database import db_manager
from core.video_downloader import VideoDownloader

logger = logging.getLogger(__name__)

router = APIRouter()

# Authentication routes
@router.get("/auth/get-token")
async def get_auth_token(request: Request):
    """Generate authentication token for the extension"""
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    # Create token with client information
    token_data = {
        "sub": client_ip,
        "user_agent": user_agent,
        "type": "extension_access"
    }
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data=token_data, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": access_token_expires.seconds
    }

# Status route
@router.get("/status")
async def get_status():
    """Server health, used by the extension to detect the backend"""
    return {"status": "running", "timestamp": datetime.now(timezone.utc).isoformat()}

# Enhanced routes for cookie-enhanced functionality with playlist and audio support
@router.post("/fetch-details-with-cookies")
async def fetch_video_details_with_cookies(
    request: Request,
    download_request: DownloadWithCookiesRequest
):
    """
    Fetch video details with cookies for authentication (supports playlists and single videos)
    
    Args:
        url: YouTube video/playlist URL
        cookies: YouTube cookies in Netscape format
        format_type: Preferred format (mp4/mp3)
    
    Returns:
        dict: a video (type=video) or a playlist (type=playlist, with videos)
    """
    if not download_request.url.strip():
        raise HTTPException(status_code=400, detail="URL is required")
    
    if not download_request.cookies.strip():
        raise HTTPException(status_code=400, detail="Cookies are required")
    
    try:
        return await VideoFetcher().fetch_details(
            download_request.url, download_request.format_type, download_request.cookies
        )
    except Exception as e:
        logger.error(f"Error fetching video details with cookies: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch video details: {str(e)}"
        )

@router.post("/download-with-cookies")
async def download_video_with_cookies(
    request: Request,
    download_request: DownloadWithCookiesRequest
) -> DownloadResponse:
    """
    Download video with cookies for authentication (supports single videos and playlist items)
    
    Args:
        url: YouTube video URL
        cookies: YouTube cookies in Netscape format
        format_id: Selected format ID
        format_type: Download format (mp4/mp3)
    
    Returns:
        DownloadResponse: Download result
    """
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    if not download_request.url.strip():
        raise HTTPException(status_code=400, detail="URL is required")
    
    if not download_request.cookies.strip():
        raise HTTPException(status_code=400, detail="Cookies are required")
    
    # Validate URL
    if not validate_youtube_url(download_request.url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL provided")

    download_dir_resolved = _resolve_download_location(download_request.download_location)
    
    try:
        # Log the download attempt
        download_record = {
            "video_url": download_request.url,
            "ip_address": client_ip,
            "user_agent": user_agent,
            "download_timestamp": datetime.now(timezone.utc),
            "success": False,
            "format_type": download_request.format_type,
            "format_id": download_request.format_id
        }
        
        # Initialize video downloader with cookies
        downloader = VideoDownloader()
        download_dir = download_dir_resolved
        
        # Download the video with cookies
        result = await downloader.download_video(
            url=download_request.url,
            format_id=download_request.format_id,
            directory=download_dir,
            format_type=download_request.format_type,
            cookies=download_request.cookies
        )
        
        if result.success:
            download_record["success"] = True
            download_record["video_title"] = result.video_title
            download_record["error_message"] = None
            
            # Log successful download to database
            await db_manager.log_download(download_record)
            
            return DownloadResponse(
                success=True,
                message=f"Video '{result.video_title}' downloaded successfully",
                task_id="direct_download",
                queue_position=0,
                estimated_wait_time="0 seconds",
                download_location=str(download_dir),
                video_title=result.video_title
            )
        else:
            download_record["error_message"] = result.error
            
            # Log failed download to database
            await db_manager.log_download(download_record)
            
            raise HTTPException(
                status_code=400,
                detail=f"Download failed: {result.error}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading video with cookies: {e}")
        
        # Log failed download to database
        download_record = {
            "video_url": download_request.url,
            "ip_address": client_ip,
            "user_agent": user_agent,
            "download_timestamp": datetime.now(timezone.utc),
            "success": False,
            "error_message": str(e),
            "format_type": download_request.format_type,
            "format_id": download_request.format_id
        }
        await db_manager.log_download(download_record)
        
        raise HTTPException(
            status_code=500,
            detail=f"Download failed: {str(e)}"
        )

# Playlist-specific download route
@router.post("/download-playlist")
async def download_playlist_with_cookies(
    request: Request,
    playlist_url: str = Form(...),
    format_type: str = Form(default="mp4"),
    download_location: Optional[str] = Form(default=None)
):
    """
    Download an entire playlist with cookies
    
    Args:
        playlist_url: YouTube playlist URL
        format_type: Download format (mp4/mp3)
        download_location: Custom download directory (optional)
    """
    client_ip = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    if not playlist_url.strip():
        raise HTTPException(status_code=400, detail="Playlist URL is required")
    
    # Validate URL
    if not validate_youtube_url(playlist_url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL provided")

    download_dir_resolved = _resolve_download_location(download_location)
    
    # For playlist downloads, we'll need to extract the cookies from the request body
    # We'll assume they're sent in a specific way for this endpoint
    
    try:
        # Extract cookies from request body (would be sent as form data)
        body_bytes = await request.body()
        body_str = body_bytes.decode()
        import re
        # This is a simplified extraction - in practice you'd handle this better
        cookies_match = re.search(r'cookies=([^&]*)', body_str)
        cookies = cookies_match.group(1) if cookies_match else ""
        cookies = cookies.replace('%0A', '\n').replace('%09', '\t')  # Unescape newlines and tabs
        
        if not cookies.strip():
            raise HTTPException(status_code=400, detail="Cookies are required")
        
        download_dir = download_dir_resolved
        playlist_title, video_count = await VideoDownloader().download_playlist(
            playlist_url, download_dir, format_type, cookies
        )

        await db_manager.log_download({
            "video_url": playlist_url,
            "video_title": f"Playlist: {playlist_title}",
            "ip_address": client_ip,
            "user_agent": user_agent,
            "download_timestamp": datetime.now(timezone.utc),
            "success": True,
            "format_type": format_type,
            "format_id": "playlist"
        })

        return DownloadResponse(
            success=True,
            message=f"Playlist '{playlist_title}' downloaded successfully ({video_count} videos)",
            task_id="playlist_download",
            queue_position=0,
            estimated_wait_time="0 seconds",
            download_location=str(download_dir),
            video_title=playlist_title
        )

    except Exception as e:
        logger.error(f"Error downloading playlist: {e}")
        
        # Log failed download to database
        download_record = {
            "video_url": playlist_url,
            "video_title": "Playlist Download",
            "ip_address": client_ip,
            "user_agent": user_agent,
            "download_timestamp": datetime.now(timezone.utc),
            "success": False,
            "error_message": str(e),
            "format_type": format_type,
            "format_id": "playlist"
        }
        await db_manager.log_download(download_record)
        
        raise HTTPException(
            status_code=500,
            detail=f"Playlist download failed: {str(e)}"
        )

@router.get("/history")
async def get_download_history(limit: int = 50):
    """Get download history (from the download log in MongoDB)"""
    history = await db_manager.get_recent_downloads(limit)
    
    return {
        "history": history,
        "total_count": len(history)
    }

def _download_locations() -> list:
    """Locations the server offers (and the only ones it will write to)"""
    home = Path.home()
    
    locations = [
        {
            "name": "Default (TubeSnatcher)",
            "path": str(settings.DEFAULT_DOWNLOAD_DIR),
            "is_default": True
        },
        {
            "name": "Downloads Folder",
            "path": str(home / "Downloads"),
            "is_default": False
        },
        {
            "name": "Desktop",
            "path": str(home / "Desktop"),
            "is_default": False
        },
        {
            "name": "Documents",
            "path": str(home / "Documents"),
            "is_default": False
        },
        {
            "name": "Videos",
            "path": str(home / "Videos"),
            "is_default": False
        }
    ]
    
    # Filter out locations that don't exist
    valid_locations = []
    for location in locations:
        try:
            path = Path(location["path"])
            if path.exists() or location["is_default"]:
                valid_locations.append(location)
        except Exception:
            continue
    
    return valid_locations

@router.get("/download-locations")
async def get_common_download_locations():
    """Get common download locations for the frontend"""
    return {"locations": _download_locations()}

def _resolve_download_location(location: Optional[str]) -> Path:
    """Map a client-supplied location to a server-side directory; arbitrary paths are rejected."""
    if not location or location.strip() in ("", "default"):
        return settings.DEFAULT_DOWNLOAD_DIR
    wanted = location.strip()
    for loc in _download_locations():
        if wanted in (loc["name"], loc["path"]):
            return Path(loc["path"])
    raise HTTPException(status_code=400, detail="Unknown download location")

