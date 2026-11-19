"""Tube Snatcher web app: FastAPI routes, lifespan, idle auto-shutdown."""
import asyncio
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .details_fetcher import stream_details
from .downloads import DownloadManager
from .ytdl import FFMPEG

log = logging.getLogger("uvicorn.error")

ROOT = Path(__file__).resolve().parent.parent
DOWNLOAD_DIR = Path(os.environ.get("TS_DOWNLOAD_DIR", ROOT / "downloads"))
# Seconds with no requests and no work before the server exits (0 = never). The page pings
# /status every 15s while open; browsers throttle hidden tabs to ~1/min, hence the margin.
IDLE_TIMEOUT = int(os.environ.get("TS_IDLE_TIMEOUT", "90"))

manager = DownloadManager(DOWNLOAD_DIR, workers=int(os.environ.get("TS_WORKERS", "3")))

Url = Annotated[str, Form(pattern=r"^https?://\S+$", max_length=2048)]
Cookies = Annotated[str | None, Form(max_length=200_000)]


async def idle_watch(app: FastAPI) -> None:
    while True:
        await asyncio.sleep(5)
        if manager.busy or app.state.streams:
            app.state.last_activity = time.monotonic()
        elif time.monotonic() - app.state.last_activity > IDLE_TIMEOUT:
            log.info("No activity for %ss, shutting down.", IDLE_TIMEOUT)
            if server := getattr(app.state, "server", None):  # set by main.py
                server.should_exit = True  # graceful: runs lifespan shutdown
            return


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.started = datetime.now()
    app.state.last_activity = time.monotonic()
    app.state.streams = 0  # open /fetch_details streams
    if not FFMPEG:
        log.warning("ffmpeg not found: merging and MP3 conversion will fail. Install it or `uv sync`.")
    manager.start()
    watcher = asyncio.create_task(idle_watch(app)) if IDLE_TIMEOUT else None
    yield
    if watcher:
        watcher.cancel()
    await manager.stop()


app = FastAPI(title="Tube Snatcher", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.middleware("http")
async def touch(request: Request, call_next):
    request.app.state.last_activity = time.monotonic()
    return await call_next(request)


def _get_task(task_id: str):
    if not (task := manager.tasks.get(task_id)):
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.get("/")
async def index():
    return FileResponse(ROOT / "templates" / "index.html")


@app.get("/status")
async def status(request: Request):
    return {
        "server_running": True,
        "queue_size": len(manager.queued),
        "active_downloads": len(manager.active),
        "server_uptime": str(datetime.now() - request.app.state.started),
    }


@app.get("/task/{task_id}")
async def get_task(task_id: str):
    return _get_task(task_id).to_dict()


@app.delete("/task/{task_id}")
async def cancel_task(task_id: str):
    task = _get_task(task_id)
    if manager.cancel(task):
        return {"message": "Task cancelled", "task_id": task_id}
    return {"message": f"Cannot cancel task with status: {task.status}"}


@app.get("/history")
async def history():
    return {"history": list(reversed(manager.history))}


@app.post("/fetch_details")
async def fetch_details(request: Request, url: Url, cookies: Cookies = None):
    """NDJSON stream: one JSON object per line (video | playlist + video_update* | error)."""

    async def lines():
        request.app.state.streams += 1
        try:
            async for item in stream_details(url, cookies):
                yield json.dumps(item) + "\n"
        except Exception as e:
            yield json.dumps({"error": str(e)}) + "\n"
        finally:
            request.app.state.streams -= 1

    return StreamingResponse(lines(), media_type="application/x-ndjson")


@app.post("/download")
async def download(
    url: Url,
    format: Annotated[Literal["mp4", "mp3"], Form()] = "mp4",
    format_id: Annotated[str | None, Form(pattern=r"^[\w.\-]+$", max_length=64)] = None,
    desired_height: Annotated[str | None, Form(pattern=r"^(best|\d{3,4})$")] = None,
    cookies: Cookies = None,
):
    task, position = manager.submit(url, format, format_id, desired_height, cookies or None)
    return {
        "message": f"Queued (position {position})" if position else "Download started",
        "task_id": task.id,
        "queue_position": position,
    }
