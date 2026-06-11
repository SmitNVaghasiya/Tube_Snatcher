# core/video_downloader.py - Enhanced video downloader
"""
Enhanced video downloader with progress tracking and better error handling
"""

import os
import yt_dlp
import asyncio
import tempfile
from pathlib import Path
from typing import Callable, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

from core.config import settings
from core.utils import clean_cookie_string

@dataclass
class DownloadResult:
    """Download result information"""
    success: bool
    filename: Optional[str] = None
    video_title: Optional[str] = None
    thumbnail: Optional[str] = None
    file_size: Optional[int] = None
    error: Optional[str] = None

class VideoDownloader:
    """Enhanced video downloader with async support"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    async def download_video(
        self, 
        url: str, 
        format_id: str, 
        directory: Path, 
        format_type: str = "mp4",
        cookies: Optional[str] = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> DownloadResult:
        """
        Download video asynchronously
        
        Args:
            url: Video URL
            format_id: Format ID to download
            directory: Download directory
            format_type: Output format type
            cookies: Optional cookies string in Netscape format
            progress_callback: Progress update callback
            
        Returns:
            DownloadResult with success status and details
        """
        try:
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._download_video_sync,
                url,
                format_id,
                directory,
                format_type,
                cookies,
                progress_callback
            )
            return result
            
        except Exception as e:
            print(f"❌ Async download error: {e}")
            return DownloadResult(
                success=False,
                error=f"Download failed: {str(e)}"
            )
    
    def _download_video_sync(
        self,
        url: str,
        format_id: str,
        directory: Path,
        format_type: str,
        cookies: Optional[str],
        progress_callback: Optional[Callable[[float], None]]
    ) -> DownloadResult:
        """Synchronous video download"""
        
        # Create output template
        output_template = str(directory / '%(title)s.%(ext)s')
        
        # Progress hook
        def progress_hook(d):
            if progress_callback and d['status'] == 'downloading':
                try:
                    if d.get('total_bytes'):
                        progress = (d.get('downloaded_bytes', 0) / d['total_bytes']) * 100
                    elif d.get('total_bytes_estimate'):
                        progress = (d.get('downloaded_bytes', 0) / d['total_bytes_estimate']) * 100
                    else:
                        progress = 0
                    
                    progress_callback(progress)
                except Exception:
                    pass
        
        cookie_file_path = None

        # Base yt-dlp options
        ydl_opts = {
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'progress_hooks': [progress_hook],
        }
        
        # Add cookies if provided
        if cookies and cookies.strip():
            # Create temporary cookie file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as cookie_file:
                cookie_file.write("# Netscape HTTP Cookie File\n")
                cookie_file.write(clean_cookie_string(cookies))
                cookie_file_path = cookie_file.name
            
            ydl_opts['cookiefile'] = cookie_file_path
        
        # Configure format-specific options
        if format_type == 'mp3':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        else:
            # Video download
            if format_id == 'best':
                ydl_opts['format'] = 'bestvideo+bestaudio/best'
            else:
                ydl_opts['format'] = format_id
            
            ydl_opts.update({
                'merge_output_format': 'mp4',
                'postprocessors': [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4',
                }],
            })
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return DownloadResult(
                        success=False,
                        error="Could not extract video information"
                    )
                
                video_title = info.get('title', 'Untitled')
                thumbnail = info.get('thumbnail', '')
                
                # Prepare filename
                filename = ydl.prepare_filename(info)
                if format_type == 'mp3':
                    filename = os.path.splitext(filename)[0] + '.mp3'
                
                # Download the video
                ydl.download([url])
                
                # Get file size
                file_size = None
                if os.path.exists(filename):
                    file_size = os.path.getsize(filename)
                
                return DownloadResult(
                    success=True,
                    filename=filename,
                    video_title=video_title,
                    thumbnail=thumbnail,
                    file_size=file_size
                )
                
        except yt_dlp.DownloadError as e:
            error_msg = str(e)
            print(f"❌ yt-dlp download error: {error_msg}")
            return DownloadResult(
                success=False,
                error=f"Download failed: {error_msg}"
            )
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Unexpected download error: {error_msg}")
            return DownloadResult(
                success=False,
                error=f"Unexpected error: {error_msg}"
            )
        
        finally:
            if cookie_file_path:
                try:
                    os.unlink(cookie_file_path)
                except OSError:
                    pass