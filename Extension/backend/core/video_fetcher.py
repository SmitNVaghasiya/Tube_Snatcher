# core/video_fetcher.py - Video information fetcher
"""
Enhanced video information fetcher with better error handling and format processing
"""

import yt_dlp
import asyncio
import tempfile
import os
from typing import Optional, Dict, List, Any
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from core.models import VideoInfo, FormatInfo
from core.config import settings
from core.utils import clean_cookie_string

class VideoFetcher:
    """Enhanced video information fetcher"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=3)
    
    async def fetch_video_info(self, url: str, format_type: str = "mp4", cookies: Optional[str] = None) -> Optional[VideoInfo]:
        """
        Fetch video information asynchronously
        
        Args:
            url: Video URL
            format_type: Preferred format type
            cookies: Optional cookies string in Netscape format
            
        Returns:
            VideoInfo or None if failed
        """
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor, 
                self._fetch_video_info_sync, 
                url, 
                format_type,
                cookies
            )
            return result
        except Exception as e:
            print(f"❌ Error in async fetch: {e}")
            return None
    
    def _fetch_video_info_sync(self, url: str, format_type: str, cookies: Optional[str]) -> Optional[VideoInfo]:
        """Synchronous video info fetching"""
        
        ydl_opts = {
            **settings.YTDL_DEFAULT_OPTS,
            'format': self._get_format_selector(format_type),
            'merge_output_format': 'mp4' if format_type != 'mp3' else None,
        }
        
        # Add cookies if provided
        if cookies and cookies.strip():
            # Create temporary cookie file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as cookie_file:
                cookie_file.write("# Netscape HTTP Cookie File\n")
                cookie_file.write(clean_cookie_string(cookies))
                cookie_file_path = cookie_file.name
            
            ydl_opts['cookiefile'] = cookie_file_path
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    return None
                
                # Handle playlists (return first video only for extension)
                if 'entries' in info:
                    if info['entries']:
                        info = info['entries'][0]
                    else:
                        return None
                
                # Process formats
                formats = self._process_formats(info.get('formats', []))
                
                result = VideoInfo(
                    title=info.get('title', 'Unknown Title'),
                    thumbnail=self._get_best_thumbnail(info.get('thumbnails', [])),
                    duration=info.get('duration', 0),
                    formats=formats,
                    uploader=info.get('uploader'),
                    upload_date=info.get('upload_date'),
                    view_count=info.get('view_count')
                )
                
                return result
                
        except Exception as e:
            print(f"❌ Error fetching video info: {e}")
            return None
        finally:
            # Clean up temporary cookie file if it was created
            if cookies and cookies.strip():
                try:
                    os.unlink(cookie_file_path)
                except:
                    pass  # It's OK if we can't delete the temp file
    
    def _process_formats(self, raw_formats: List[Dict]) -> List[FormatInfo]:
        """Process and filter video formats"""
        formats = []
        seen_resolutions = set()
        
        # Sort formats by quality (resolution and filesize)
        sorted_formats = sorted(
            raw_formats,
            key=lambda x: (
                x.get('height', 0) or 0,
                x.get('width', 0) or 0,
                x.get('filesize', 0) or x.get('filesize_approx', 0) or 0
            ),
            reverse=True
        )
        
        for fmt in sorted_formats:
            # Skip irrelevant formats
            if self._should_skip_format(fmt):
                continue
            
            resolution = self._get_resolution_string(fmt)
            
            # Avoid duplicate resolutions (keep the best one)
            if resolution in seen_resolutions:
                continue
            
            seen_resolutions.add(resolution)
            
            filesize_str = self._calculate_filesize_string(fmt)
            
            format_info = FormatInfo(
                format_id=fmt.get('format_id', 'unknown'),
                resolution=resolution,
                filesize=filesize_str,
                format_note=fmt.get('format_note', 'N/A'),
                ext=fmt.get('ext', 'N/A'),
                bitrate=fmt.get('tbr'),
                fps=fmt.get('fps')
            )
            
            formats.append(format_info)
        
        return formats
    
    def _should_skip_format(self, fmt: Dict) -> bool:
        """Check if format should be skipped"""
        format_note = fmt.get('format_note', '').lower()
        format_id = fmt.get('format_id', '').lower()
        
        skip_keywords = [
            'storyboard', 'thumbnail', 'preview', 'dash', 'hls',
            'live', 'premium', 'drm'
        ]
        
        return any(keyword in format_note or keyword in format_id for keyword in skip_keywords)
    
    def _get_resolution_string(self, fmt: Dict) -> str:
        """Get resolution string for format"""
        width = fmt.get('width')
        height = fmt.get('height')
        
        if width and height:
            return f"{width}x{height}"
        elif fmt.get('vcodec') == 'none':
            return 'Audio Only'
        elif height:
            return f"{height}p"
        else:
            return 'Unknown Quality'
    
    def _calculate_filesize_string(self, fmt: Dict) -> str:
        """Calculate and format file size string"""
        filesize = fmt.get('filesize') or fmt.get('filesize_approx', 0)
        
        if not filesize:
            # Estimate based on resolution and bitrate
            filesize = self._estimate_filesize(fmt)
        
        if filesize and filesize > 0:
            # Convert bytes to appropriate unit
            if filesize >= 1024 * 1024 * 1024:  # GB
                return f"{filesize / (1024 * 1024 * 1024):.1f} GB"
            elif filesize >= 1024 * 1024:  # MB
                return f"{filesize / (1024 * 1024):.1f} MB"
            elif filesize >= 1024:  # KB
                return f"{filesize / 1024:.1f} KB"
            else:
                return f"{filesize} B"
        
        return "Size Unknown"
    
    def _estimate_filesize(self, fmt: Dict) -> int:
        """Estimate file size based on available metadata"""
        try:
            width = fmt.get('width', 0)
            height = fmt.get('height', 0)
            duration = fmt.get('duration', 0)
            bitrate = fmt.get('tbr', 0)
            
            if bitrate and duration:
                # Estimate from bitrate: (bitrate in kbps * duration in seconds * 1000) / 8
                return int((bitrate * duration * 1000) / 8)
            
            elif width and height:
                # Rough estimation based on resolution
                resolution_area = width * height
                estimated_size = resolution_area * settings.FILESIZE_ESTIMATION_FACTOR
                return int(estimated_size)
            
            return 0
            
        except Exception:
            return 0
    
    def _get_best_thumbnail(self, thumbnails: List[Dict]) -> str:
        """Get the best quality thumbnail URL"""
        if not thumbnails:
            return ""
        
        # Sort by preference: maxresdefault > hqdefault > others
        def thumbnail_priority(thumb):
            url = thumb.get('url', '')
            if 'maxresdefault' in url:
                return 3
            elif 'hqdefault' in url:
                return 2
            elif 'default' in url:
                return 1
            return 0
        
        best_thumbnail = max(thumbnails, key=thumbnail_priority)
        return best_thumbnail.get('url', '')
    
    def _get_format_selector(self, format_type: str) -> str:
        """Get appropriate format selector for yt-dlp"""
        if format_type == 'mp3':
            return settings.AUDIO_FORMAT_PREFERENCE
        else:
            return settings.VIDEO_FORMAT_PREFERENCE