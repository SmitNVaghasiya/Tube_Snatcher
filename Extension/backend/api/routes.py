# api/routes.py - API routes for the extension backend
"""
API routes for video downloading functionality
Separated from main app for better organization
"""

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Optional
import os
from pathlib import Path
from datetime import datetime, timedelta
import yt_dlp
import tempfile

from core.video_fetcher import VideoFetcher
from core.models import DownloadRequest, VideoInfo, DownloadResponse, DownloadWithCookiesRequest
from core.config import settings
from core.auth import create_access_token, verify_token
from core.utils import get_client_ip, get_user_agent, validate_youtube_url, clean_cookie_string
from core.database import db_manager
from core.video_downloader import VideoDownloader

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

# Status and queue routes
@router.get("/status")
async def get_status(request: Request):
    """Get server status and basic info"""
    download_manager = request.app.state.download_manager
    
    return {
        "status": "running",
        "queue_size": len(download_manager.download_queue),
        "active_downloads": len(download_manager.active_downloads),
        "timestamp": download_manager.get_current_time()
    }

@router.get("/queue")
async def get_queue_status(request: Request):
    """Get detailed queue and active downloads status"""
    download_manager = request.app.state.download_manager
    return await download_manager.get_queue_status()

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
        VideoInfo or PlaylistInfo depending on URL type
    """
    if not download_request.url.strip():
        raise HTTPException(status_code=400, detail="URL is required")
    
    if not download_request.cookies.strip():
        raise HTTPException(status_code=400, detail="Cookies are required")
    
    try:
        # Create temporary cookie file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as cookie_file:
            cookie_file.write("# Netscape HTTP Cookie File\n")
            cookie_file.write(clean_cookie_string(download_request.cookies))
            cookie_file_path = cookie_file.name

        try:
            ydl_opts = {
                **settings.YTDL_DEFAULT_OPTS,
                'format': 'bestvideo+bestaudio/best' if download_request.format_type != 'mp3' else 'bestaudio/best',
                'merge_output_format': 'mp4' if download_request.format_type != 'mp3' else None,
                'cookiefile': cookie_file_path,
                'noplaylist': False,  # Allow playlist processing
                'extract_flat': True,  # Get playlist info without full metadata
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(download_request.url, download=False)
                
                if 'entries' in info:  # Playlist detected
                    # Process playlist
                    playlist_info = {
                        'type': 'playlist',
                        'title': info.get('title', 'Playlist'),
                        'thumbnail': info.get('thumbnails', [{}])[-1].get('url', '') if info.get('thumbnails') else '',
                        'video_count': info.get('playlist_count', len(info.get('entries', []))),
                        'videos': []
                    }
                    
                    # Get detailed info for each video in the playlist
                    for entry in info.get('entries', []):
                        video_opts = {
                            **settings.YTDL_DEFAULT_OPTS,
                            'format': 'bestvideo+bestaudio/best' if download_request.format_type != 'mp3' else 'bestaudio/best',
                            'cookiefile': cookie_file_path,
                            'noplaylist': True,
                        }
                        
                        try:
                            with yt_dlp.YoutubeDL(video_opts) as video_ydl:
                                video_info = video_ydl.extract_info(entry.get('url', entry.get('webpage_url')), download=False)
                                
                                # Process formats
                                formats = []
                                if 'formats' in video_info:
                                    for fmt in video_info['formats']:
                                        if 'storyboard' in fmt.get('format_note', '').lower():
                                            continue
                                        
                                        width = fmt.get('width')
                                        height = fmt.get('height')
                                        resolution = f"{width}x{height}" if width and height else 'Audio Only' if fmt.get('vcodec') == 'none' else 'N/A'
                                        filesize = fmt.get('filesize') or fmt.get('filesize_approx', 0)
                                        filesize_str = f"{round(filesize / (1024 * 1024), 2)} MB" if filesize else "Size Unknown"
                                        
                                        format_info = {
                                            'format_id': fmt.get('format_id'),
                                            'resolution': resolution,
                                            'filesize': filesize_str,
                                            'format_note': fmt.get('format_note', 'N/A'),
                                            'ext': fmt.get('ext', 'N/A')
                                        }
                                        formats.append(format_info)
                                
                                playlist_info['videos'].append({
                                    'title': video_info.get('title', 'Untitled'),
                                    'url': video_info.get('webpage_url', video_info.get('url')),
                                    'thumbnail': video_info.get('thumbnail', ''),
                                    'duration': video_info.get('duration', 0),
                                    'formats': formats
                                })
                        except Exception as e:
                            # Skip failed videos
                            continue
                    
                    return playlist_info
                    
                else:  # Single video
                    # Handle single video as before
                    formats = []
                    if 'formats' in info:
                        for fmt in info['formats']:
                            if 'storyboard' in fmt.get('format_note', '').lower():
                                continue
                            
                            width = fmt.get('width')
                            height = fmt.get('height')
                            resolution = f"{width}x{height}" if width and height else 'Audio Only' if fmt.get('vcodec') == 'none' else 'N/A'
                            filesize = fmt.get('filesize') or fmt.get('filesize_approx', 0)
                            filesize_str = f"{round(filesize / (1024 * 1024), 2)} MB" if filesize else "Size Unknown"
                            
                            format_info = {
                                'format_id': fmt.get('format_id'),
                                'resolution': resolution,
                                'filesize': filesize_str,
                                'format_note': fmt.get('format_note', 'N/A'),
                                'ext': fmt.get('ext', 'N/A')
                            }
                            formats.append(format_info)
                    
                    result = {
                        'type': 'video',
                        'title': info.get('title', 'Unknown Title'),
                        'thumbnail': info.get('thumbnail', ''),
                        'duration': info.get('duration', 0),
                        'formats': formats,
                        'uploader': info.get('uploader'),
                        'upload_date': info.get('upload_date'),
                        'view_count': info.get('view_count')
                    }
                    
                    return result
        
        finally:
            try:
                os.unlink(cookie_file_path)
            except:
                pass
        
    except Exception as e:
        print(f"❌ Error fetching video details with cookies: {e}")
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
    
    try:
        # Log the download attempt
        download_record = {
            "video_url": download_request.url,
            "ip_address": client_ip,
            "user_agent": user_agent,
            "download_timestamp": datetime.utcnow(),
            "success": False,
            "format_type": download_request.format_type,
            "format_id": download_request.format_id
        }
        
        # Initialize video downloader with cookies
        downloader = VideoDownloader()
        download_manager = request.app.state.download_manager
        download_dir = settings.get_download_directory(download_request.download_location)
        
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
        print(f"❌ Error downloading video with cookies: {e}")
        
        # Log failed download to database
        download_record = {
            "video_url": download_request.url,
            "ip_address": client_ip,
            "user_agent": user_agent,
            "download_timestamp": datetime.utcnow(),
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
        
        # Create temporary cookie file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as cookie_file:
            cookie_file.write("# Netscape HTTP Cookie File\n")
            cookie_file.write(clean_cookie_string(cookies))
            cookie_file_path = cookie_file.name

        try:
            ydl_opts = {
                **settings.YTDL_DEFAULT_OPTS,
                'format': 'bestvideo+bestaudio/best' if format_type != 'mp3' else 'bestaudio/best',
                'cookiefile': cookie_file_path,
                'noplaylist': False,  # We want to download the playlist
                'outtmpl': f'{settings.get_download_directory(download_location)}/%(playlist)s/%(playlist_index)03d - %(title)s.%(ext)s' if format_type != 'mp3' else f'{settings.get_download_directory(download_location)}/%(playlist)s/%(playlist_index)03d - %(title)s.%(ext)s',
            }
            
            if format_type == 'mp3':
                ydl_opts.update({
                    'extractaudio': True,
                    'audioformat': 'mp3',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                })
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(playlist_url, download=True)
                
                playlist_title = info.get('title', 'Playlist')
                
                # Log successful download to database
                download_record = {
                    "video_url": playlist_url,
                    "video_title": f"Playlist: {playlist_title}",
                    "ip_address": client_ip,
                    "user_agent": user_agent,
                    "download_timestamp": datetime.utcnow(),
                    "success": True,
                    "format_type": format_type,
                    "format_id": "playlist"
                }
                await db_manager.log_download(download_record)
                
                return DownloadResponse(
                    success=True,
                    message=f"Playlist '{playlist_title}' downloaded successfully ({info.get('playlist_count', 0)} videos)",
                    task_id="playlist_download",
                    queue_position=0,
                    estimated_wait_time="0 seconds",
                    download_location=str(settings.get_download_directory(download_location)),
                    video_title=playlist_title
                )
        
        finally:
            try:
                os.unlink(cookie_file_path)
            except:
                pass
    
    except Exception as e:
        print(f"❌ Error downloading playlist: {e}")
        
        # Log failed download to database
        download_record = {
            "video_url": playlist_url,
            "video_title": "Playlist Download",
            "ip_address": client_ip,
            "user_agent": user_agent,
            "download_timestamp": datetime.utcnow(),
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

# Analytics routes
@router.get("/analytics")
async def get_analytics():
    """Get download analytics"""
    analytics = await db_manager.get_analytics()
    return analytics

# Legacy routes (preserving existing functionality)
@router.post("/fetch-details")
async def fetch_video_details(
    url: str = Form(...),
    format_type: str = Form(default="mp4")
) -> VideoInfo:
    """
    Fetch video details including available formats
    
    Args:
        url: YouTube video URL
        format_type: Preferred format (mp4/mp3)
    
    Returns:
        VideoInfo: Video details with available formats
    """
    if not url.strip():
        raise HTTPException(status_code=400, detail="URL is required")
    
    try:
        fetcher = VideoFetcher()
        result = await fetcher.fetch_video_info(url, format_type)
        
        if not result:
            raise HTTPException(
                status_code=404, 
                detail="Could not fetch video details. Please check the URL."
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching video details: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to fetch video details: {str(e)}"
        )

@router.post("/download")
async def queue_download(
    request: Request,
    url: str = Form(...),
    format_id: str = Form(...),
    format_type: str = Form(default="mp4"),
    download_location: Optional[str] = Form(default=None)
) -> DownloadResponse:
    """
    Queue a video for download
    
    Args:
        url: YouTube video URL
        format_id: Selected format ID
        format_type: Download format (mp4/mp3)
        download_location: Custom download directory (optional)
    
    Returns:
        DownloadResponse: Download task details
    """
    if not url.strip() or not format_id.strip():
        raise HTTPException(
            status_code=400, 
            detail="URL and format_id are required"
        )
    
    # Validate download location if provided
    if download_location and download_location.strip() != "default":
        if not _validate_download_location(download_location):
            raise HTTPException(
                status_code=400,
                detail="Invalid download location. Directory must be writable."
            )
    
    try:
        download_manager = request.app.state.download_manager
        
        download_request = DownloadRequest(
            url=url.strip(),
            format_id=format_id.strip(),
            format_type=format_type,
            download_location=download_location
        )
        
        task_id = await download_manager.add_to_queue(download_request)
        queue_position = len(download_manager.download_queue)
        
        return DownloadResponse(
            success=True,
            message="Download queued successfully",
            task_id=task_id,
            queue_position=queue_position,
            estimated_wait_time="1-3 minutes",
            download_location=download_location or "default"
        )
        
    except Exception as e:
        print(f"❌ Error queuing download: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue download: {str(e)}"
        )

@router.get("/task/{task_id}")
async def get_task_status(request: Request, task_id: str):
    """Get status of a specific download task"""
    download_manager = request.app.state.download_manager
    task = download_manager.get_task_by_id(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": task.id,
        "status": task.status,
        "progress": task.progress,
        "filename": task.filename,
        "error": task.error,
        "created_at": task.created_at.isoformat(),
        "start_time": task.start_time.isoformat() if task.start_time else None,
        "completion_time": task.completion_time.isoformat() if task.completion_time else None
    }

@router.delete("/task/{task_id}")
async def cancel_task(request: Request, task_id: str):
    """Cancel a queued or active download task"""
    download_manager = request.app.state.download_manager
    success = await download_manager.cancel_task(task_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Task not found or cannot be cancelled")
    
    return {"message": "Task cancelled successfully", "task_id": task_id}

@router.post("/clear-queue")
async def clear_download_queue(request: Request):
    """Clear all queued downloads (not active ones)"""
    download_manager = request.app.state.download_manager
    cleared_count = await download_manager.clear_queue()
    
    return {
        "message": f"Cleared {cleared_count} queued downloads",
        "cleared_count": cleared_count
    }

@router.get("/history")
async def get_download_history(request: Request, limit: int = 50):
    """Get download history"""
    download_manager = request.app.state.download_manager
    history = await download_manager.get_download_history(limit)
    
    return {
        "history": history,
        "total_count": len(history)
    }

@router.get("/download-locations")
async def get_common_download_locations():
    """Get common download locations for the frontend"""
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
    
    return {"locations": valid_locations}

def _validate_download_location(location: str) -> bool:
    """Validate if download location is writable"""
    try:
        path = Path(location)
        
        # Create directory if it doesn't exist
        path.mkdir(parents=True, exist_ok=True)
        
        # Test write permissions
        test_file = path / ".test_write"
        test_file.write_text("test")
        test_file.unlink()
        
        return True
        
    except Exception as e:
        print(f"⚠️  Invalid download location {location}: {e}")
        return False