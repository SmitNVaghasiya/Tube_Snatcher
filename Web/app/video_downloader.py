"""Blocking yt-dlp download; run it in a thread."""
import tempfile
import threading
from collections.abc import Callable
from pathlib import Path

import yt_dlp
from yt_dlp.utils import DownloadCancelled

from .ytdl import base_opts, cookie_file


def format_selector(format_type: str, format_id: str | None, height: str | None) -> str:
    if format_type == "mp3":
        return "bestaudio/best"
    if format_id:
        # A chosen video-only format has no sound: add the best audio. Formats that already
        # carry audio (or are audio-only) fail the [acodec=none] filter and are used as-is.
        return f"{format_id}[acodec=none]+bestaudio/{format_id}"
    if height and height.isdigit():
        return f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"
    return "bestvideo+bestaudio/best"


def download_video(
    url: str,
    selector: str,
    directory: Path,
    format_type: str,
    on_progress: Callable[[float], None],
    cancel: threading.Event,
    cookies: str | None = None,
) -> tuple[str, str]:
    """Returns (final file path, title). Raises on failure or DownloadCancelled."""

    def hook(d: dict) -> None:
        if cancel.is_set():
            raise DownloadCancelled("cancelled by user")
        if d["status"] == "downloading":
            if total := d.get("total_bytes") or d.get("total_bytes_estimate"):
                on_progress(d.get("downloaded_bytes", 0) / total * 100)

    if format_type == "mp3":
        post = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]
        extra = {}
    else:
        post = [{"key": "FFmpegVideoRemuxer", "preferedformat": "mp4"}]  # lossless container swap
        extra = {"merge_output_format": "mp4"}

    directory.mkdir(parents=True, exist_ok=True)
    scratch = directory / ".tmp"
    scratch.mkdir(exist_ok=True)
    # In-progress files live in a per-download scratch dir that is always removed,
    # so failed/cancelled downloads leave no .part debris next to the finished files.
    with (
        tempfile.TemporaryDirectory(dir=scratch, ignore_cleanup_errors=True) as tmp,
        cookie_file(cookies) as cf,
    ):
        opts = base_opts(cf) | extra | {
            "format": selector,
            "paths": {"home": str(directory), "temp": tmp},
            "outtmpl": "%(title)s.%(ext)s",
            "noplaylist": True,
            "noprogress": True,
            "concurrent_fragment_downloads": 4,
            "windowsfilenames": True,
            "progress_hooks": [hook],
            "postprocessors": post,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            path = (info.get("requested_downloads") or [{}])[0].get("filepath") or ydl.prepare_filename(info)
    return path, info.get("title") or "Untitled"
