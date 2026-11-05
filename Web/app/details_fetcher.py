"""Fetch video / playlist details, streaming results as they become available."""
import asyncio
from collections.abc import AsyncIterator

import yt_dlp

from .formats import list_formats, video_summary
from .ytdl import base_opts, cookie_file


def _extract(url: str, cookies: str | None, **extra) -> dict:
    with cookie_file(cookies) as cf, yt_dlp.YoutubeDL(base_opts(cf) | extra) as ydl:
        return ydl.extract_info(url, download=False)


async def stream_details(url: str, cookies: str | None = None) -> AsyncIterator[dict]:
    # extract_flat only affects playlist entries: a single video still comes back fully resolved,
    # a playlist comes back instantly as a flat list. One call either way.
    info = await asyncio.to_thread(
        _extract, url, cookies, extract_flat="in_playlist", ignore_no_formats_error=True
    )

    if "entries" not in info:
        yield {
            "type": "video",
            "title": info.get("title") or "No title available",
            "thumbnail": info.get("thumbnail") or "",
            "formats": list_formats(info),
        }
        return

    # The flat listing already has title/duration/thumbnail for every entry, so a 300-video
    # playlist streams out instantly. Formats are resolved at download time, not here.
    entries = [e for e in info["entries"] if e and (e.get("url") or e.get("webpage_url"))]
    yield {
        "type": "playlist",
        "title": info.get("title") or "Playlist",
        "thumbnail": ((info.get("thumbnails") or [{}])[-1]).get("url", ""),
        "video_count": len(entries),
    }
    for entry in entries:
        yield {"type": "video_update", "video": video_summary(entry)}
