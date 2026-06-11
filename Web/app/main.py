# app/main.py
import os
import signal
import time
import json
import asyncio
from datetime import datetime
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from .details_fetcher import fetch_video_info
from .video_downloader import download_video

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

download_queue = []
active_downloads = []
server_start_time = None
shutdown_timer = None


class DownloadTask:
    def __init__(self, url, format_id, desired_height, format_type):
        self.id = f"task_{int(time.time() * 1000)}"
        self.url = url
        self.format_id = format_id
        self.desired_height = desired_height
        self.format_type = format_type
        self.status = "queued"
        self.progress = 0
        self.filename = None
        self.error = None
        self.start_time = None
        self.completion_time = None
        self.created_at = datetime.now()


def start_shutdown_timer():
    global shutdown_timer
    if shutdown_timer:
        shutdown_timer.cancel()
    shutdown_timer = asyncio.create_task(delayed_shutdown())


async def delayed_shutdown():
    await asyncio.sleep(30)
    if not download_queue and not active_downloads:
        print("No activity. Shutting down server…")
        os.kill(os.getpid(), signal.SIGTERM)


def add_to_queue(url, format_id, desired_height, format_type):
    task = DownloadTask(url, format_id, desired_height, format_type)
    download_queue.append(task)
    if not active_downloads:
        asyncio.create_task(process_download_queue())
    return task


async def process_download_queue():
    while download_queue:
        if len(active_downloads) >= 2:
            await asyncio.sleep(1)
            continue
        task = download_queue.pop(0)
        active_downloads.append(task)
        asyncio.create_task(execute_download(task))


async def execute_download(task: DownloadTask):
    try:
        task.status = "downloading"
        task.start_time = datetime.now()
        task.progress = 0

        os.makedirs("temp", exist_ok=True)

        def on_progress(pct: float):
            task.progress = min(int(pct), 99)

        loop = asyncio.get_running_loop()
        format_or_height = task.format_id or task.desired_height
        filename, error, title, _ = await loop.run_in_executor(
            None,
            lambda: download_video(task.url, format_or_height, "temp", task.format_type, on_progress),
        )

        if error:
            task.status = "failed"
            task.error = error
        else:
            task.status = "completed"
            task.filename = filename
            task.progress = 100
            task.completion_time = datetime.now()
            print(f"Download completed: {title}")

    except Exception as e:
        task.status = "failed"
        task.error = str(e)

    finally:
        if task in active_downloads:
            active_downloads.remove(task)
        if not download_queue and not active_downloads:
            start_shutdown_timer()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/status")
async def get_status():
    return {
        "server_running": True,
        "queue_size": len(download_queue),
        "active_downloads": len(active_downloads),
        "server_uptime": str(datetime.now() - server_start_time) if server_start_time else "0:00:00",
    }


@app.get("/queue")
async def get_queue():
    return {
        "queue": [
            {
                "id": t.id, "url": t.url, "status": t.status,
                "progress": t.progress, "created_at": t.created_at.isoformat(),
                "error": t.error,
            }
            for t in download_queue
        ],
        "active": [
            {
                "id": t.id, "url": t.url, "status": t.status,
                "progress": t.progress,
                "start_time": t.start_time.isoformat() if t.start_time else None,
                "filename": t.filename, "error": t.error,
            }
            for t in active_downloads
        ],
    }


@app.post("/fetch_details")
async def fetch_details(url: str = Form(...), format: str = Form(default="mp4")):
    if not url:
        raise HTTPException(status_code=400, detail="No URL provided")

    async def generate():
        loop = asyncio.get_running_loop()
        try:
            result = await loop.run_in_executor(None, lambda: fetch_video_info(url, format))
        except Exception as e:
            yield json.dumps({"error": str(e)}) + "\n"
            return

        if result is None:
            yield json.dumps({"error": "Failed to fetch video details"}) + "\n"
            return

        if result["type"] == "playlist":
            yield json.dumps({
                "type": "playlist",
                "title": result["title"],
                "thumbnail": result["thumbnail"],
                "video_count": len(result["videos"]),
            }) + "\n"
            for video in result["videos"]:
                yield json.dumps({"type": "video_update", "video": video}) + "\n"
        else:
            yield json.dumps(result) + "\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/download")
async def download(
    url: str = Form(...),
    format_id: str = Form(None),
    desired_height: str = Form(None),
    format: str = Form(default="mp4"),
):
    if not url:
        raise HTTPException(status_code=400, detail="No URL provided")

    task = add_to_queue(url, format_id, desired_height, format)
    queue_pos = len(download_queue)
    wait_secs = queue_pos * 60 + len(active_downloads) * 30
    if wait_secs < 30:
        wait_str = "starting shortly"
    elif wait_secs < 120:
        wait_str = "~1 minute"
    else:
        wait_str = f"~{wait_secs // 60} minutes"

    return {
        "message": f"Download queued (position {queue_pos})" if queue_pos else "Download started",
        "task_id": task.id,
        "queue_position": queue_pos,
        "estimated_wait": wait_str,
    }


@app.on_event("startup")
async def startup_event():
    global server_start_time
    server_start_time = datetime.now()
    print(f"Tube Snatcher started at {server_start_time}")
