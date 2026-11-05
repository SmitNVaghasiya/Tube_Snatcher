"""Shared yt-dlp setup: base options, ffmpeg lookup, temp cookie file."""
import contextlib
import os
import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path


def _find_ffmpeg() -> str | None:
    if path := shutil.which("ffmpeg"):
        return path
    try:  # bundled binary from the imageio-ffmpeg wheel
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


FFMPEG = _find_ffmpeg()


def base_opts(cookiefile: str | None = None) -> dict:
    opts = {
        "quiet": True,
        "no_warnings": True,
        "color": "no_color",  # keep ANSI codes out of error messages sent to the UI
        # YouTube needs a JS runtime for its challenges; node comes from nvm, deno if present.
        "js_runtimes": {"deno": {}, "node": {}},
    }
    if FFMPEG:
        opts["ffmpeg_location"] = FFMPEG
    if cookiefile:
        opts["cookiefile"] = cookiefile
    return opts


@contextlib.contextmanager
def cookie_file(cookies: str | None) -> Iterator[str | None]:
    """Write pasted Netscape cookies to a temp file; always delete it afterwards."""
    if not (cookies and cookies.strip()):
        yield None
        return
    fd, path = tempfile.mkstemp(suffix=".txt")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("# Netscape HTTP Cookie File\n" + cookies.strip() + "\n")
        yield path
    finally:
        Path(path).unlink(missing_ok=True)
