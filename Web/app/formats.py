"""Turn raw yt-dlp info dicts into the small dicts the UI renders."""


def _size(fmt: dict, duration: float | None) -> float:
    """Best-known size in bytes; falls back to bitrate * duration."""
    size = fmt.get("filesize") or fmt.get("filesize_approx") or 0
    if not size and fmt.get("tbr") and duration:
        size = fmt["tbr"] * 125 * duration  # tbr is kbit/s -> bytes/s = *1000/8
    return size


def _resolution(fmt: dict) -> str:
    if fmt.get("width") and fmt.get("height"):
        return f"{fmt['width']}x{fmt['height']}"
    return "Audio Only" if fmt.get("vcodec") == "none" else "N/A"


def _is_downloadable(fmt: dict) -> bool:
    if fmt.get("ext") == "mhtml" or "storyboard" in (fmt.get("format_note") or "").lower():
        return False
    return not (fmt.get("vcodec") == "none" and fmt.get("acodec") == "none")


def list_formats(info: dict) -> list[dict]:
    """One entry per resolution (the largest format of each), as shown for a single video."""
    duration = info.get("duration")
    best: dict[str, tuple[float, dict]] = {}
    for fmt in filter(_is_downloadable, info.get("formats") or []):
        res, size = _resolution(fmt), _size(fmt, duration)
        if res not in best or size > best[res][0]:
            best[res] = (size, fmt)
    return [
        {
            "format_id": fmt.get("format_id"),
            "resolution": res,
            "filesize": f"{size / 1048576:.2f} MB" if size else "Size Unknown",
            "format_note": fmt.get("format_note") or "N/A",
            "ext": fmt.get("ext") or "N/A",
        }
        for res, (size, fmt) in best.items()
    ]


def video_summary(entry: dict) -> dict:
    """Playlist row from a flat yt-dlp entry (no format lookup needed)."""
    thumbs = entry.get("thumbnails") or []
    thumb = entry.get("thumbnail") or (thumbs[-1].get("url") if thumbs else "")
    if not thumb and entry.get("id"):
        thumb = f"https://i.ytimg.com/vi/{entry['id']}/mqdefault.jpg"
    return {
        "title": entry.get("title") or "Untitled",
        "url": entry.get("webpage_url") or entry.get("url"),
        "thumbnail": thumb,
        "duration": entry.get("duration") or 0,
    }
