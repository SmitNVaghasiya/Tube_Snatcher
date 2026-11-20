# core/video_fetcher.py - Video information fetcher
"""
Enhanced video information fetcher with better error handling and format processing
"""

import logging
import yt_dlp
import asyncio
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor

from core.config import settings
from core.utils import cookie_file

logger = logging.getLogger(__name__)

class VideoFetcher:
    """Enhanced video information fetcher"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=3)
    
    def _get_format_selector(self, format_type: str) -> str:
        """Get appropriate format selector for yt-dlp"""
        if format_type == 'mp3':
            return settings.AUDIO_FORMAT_PREFERENCE
        else:
            return settings.VIDEO_FORMAT_PREFERENCE

    async def fetch_details(self, url: str, format_type: str = "mp4", cookies: Optional[str] = None) -> Dict[str, Any]:
        """Details for a single video or a whole playlist, as plain dicts for the popup. Raises on failure."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, self._fetch_details_sync, url, format_type, cookies)

    def _fetch_details_sync(self, url: str, format_type: str, cookies: Optional[str]) -> Dict[str, Any]:
        base = {**settings.YTDL_DEFAULT_OPTS, 'format': self._get_format_selector(format_type)}
        with cookie_file(cookies) as cookie_path:
            if cookie_path:
                base['cookiefile'] = cookie_path
            # extract_flat: playlist entries come back as a cheap flat list
            with yt_dlp.YoutubeDL({**base, 'noplaylist': False, 'extract_flat': True}) as ydl:
                info = ydl.extract_info(url, download=False)

            if 'entries' not in info:
                return {
                    'type': 'video',
                    **self._summary(info),
                    'uploader': info.get('uploader'),
                    'upload_date': info.get('upload_date'),
                    'view_count': info.get('view_count'),
                }

            playlist = {
                'type': 'playlist',
                'title': info.get('title', 'Playlist'),
                'thumbnail': info.get('thumbnails', [{}])[-1].get('url', '') if info.get('thumbnails') else '',
                'video_count': info.get('playlist_count', len(info.get('entries', []))),
                'videos': [],
            }
            for entry in info.get('entries', []):
                try:
                    with yt_dlp.YoutubeDL({**base, 'noplaylist': True}) as ydl:
                        video = ydl.extract_info(entry.get('url', entry.get('webpage_url')), download=False)
                    playlist['videos'].append({**self._summary(video), 'url': video.get('webpage_url', video.get('url'))})
                except Exception as e:
                    logger.warning(f"Skipping playlist entry: {e}")
            return playlist

    @staticmethod
    def _summary(info: Dict) -> Dict[str, Any]:
        """Title/thumbnail/duration plus a simple per-format list (one dict per yt-dlp format)."""
        formats = []
        for fmt in info.get('formats') or []:
            if 'storyboard' in (fmt.get('format_note') or '').lower():
                continue
            width, height = fmt.get('width'), fmt.get('height')
            size = fmt.get('filesize') or fmt.get('filesize_approx', 0)
            formats.append({
                'format_id': fmt.get('format_id'),
                'resolution': f"{width}x{height}" if width and height else 'Audio Only' if fmt.get('vcodec') == 'none' else 'N/A',
                'filesize': f"{round(size / (1024 * 1024), 2)} MB" if size else "Size Unknown",
                'format_note': fmt.get('format_note', 'N/A'),
                'ext': fmt.get('ext', 'N/A'),
            })
        return {
            'title': info.get('title', 'Unknown Title'),
            'thumbnail': info.get('thumbnail', ''),
            'duration': info.get('duration', 0),
            'formats': formats,
        }
