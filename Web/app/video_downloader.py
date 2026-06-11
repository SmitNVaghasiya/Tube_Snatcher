# app/video_downloader.py
import os
import yt_dlp
from typing import Callable, Optional


def download_video(
    url: str,
    format_id_or_height,
    directory: str,
    format_type: str,
    progress_callback: Optional[Callable[[float], None]] = None,
):
    def progress_hook(d):
        if progress_callback and d["status"] == "downloading":
            try:
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                if total:
                    progress_callback((d.get("downloaded_bytes", 0) / total) * 100)
            except Exception:
                pass

    ydl_opts = {
        "outtmpl": os.path.join(directory, "%(title)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "progress_hooks": [progress_hook],
    }

    if format_type == "mp3":
        ydl_opts.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
        })
    else:
        if not format_id_or_height or format_id_or_height == "best":
            ydl_opts["format"] = "bestvideo+bestaudio/best"
        elif str(format_id_or_height).isdigit():
            h = format_id_or_height
            ydl_opts["format"] = f"bestvideo[height<={h}]+bestaudio/best[height<={h}]"
        else:
            ydl_opts["format"] = format_id_or_height
        ydl_opts.update({
            "merge_output_format": "mp4",
            "postprocessors": [{"key": "FFmpegVideoConvertor", "preferedformat": "mp4"}],
            "keepvideo": False,
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if format_type == "mp3":
                filename = os.path.splitext(filename)[0] + ".mp3"
        return filename, None, info.get("title", "Untitled"), info.get("thumbnail", "")
    except Exception as e:
        print(f"Download error: {e}")
        return None, str(e), None, None
