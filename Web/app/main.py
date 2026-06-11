# app/main.py
import os
import signal
import time
import json
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from .details_fetcher import fetch_video_info
from .video_downloader import download_video

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# In-memory state
all_tasks: dict = {}       # task_id -> DownloadTask (for fast lookup)
download_queue: list = []
active_downloads: list = []
download_history: list = []   # last 100 records (newest appended last)
server_start_time = None
shutdown_timer = None


class DownloadTask:
    def __init__(self, url, format_id, desired_height, format_type, cookies=None):
        self.id = f"task_{int(time.time() * 1000)}"
        self.url = url
        self.format_id = format_id
        self.desired_height = desired_height
        self.format_type = format_type
        self.cookies = cookies
        self.status = "queued"
        self.progress = 0
        self.filename = None
        self.video_title = None
        self.error = None
        self.start_time = None
        self.completion_time = None
        self.created_at = datetime.now()

    def to_dict(self):
        return {
            "id": self.id,
            "url": self.url,
            "status": self.status,
            "progress": self.progress,
            "video_title": self.video_title,
            "format_type": self.format_type,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "completion_time": self.completion_time.isoformat() if self.completion_time else None,
        }


# ── Queue management ──────────────────────────────────────────────────────────

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


def add_to_queue(url, format_id, desired_height, format_type, cookies=None):
    task = DownloadTask(url, format_id, desired_height, format_type, cookies)
    all_tasks[task.id] = task
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
            lambda: download_video(
                task.url, format_or_height, "temp",
                task.format_type, on_progress, task.cookies
            ),
        )

        if error:
            task.status = "failed"
            task.error = error
        else:
            task.status = "completed"
            task.filename = filename
            task.video_title = title
            task.progress = 100
            task.completion_time = datetime.now()

    except Exception as e:
        task.status = "failed"
        task.error = str(e)

    finally:
        if task in active_downloads:
            active_downloads.remove(task)

        # Persist to in-memory history (newest last, capped at 100)
        download_history.append(task.to_dict())
        if len(download_history) > 100:
            download_history.pop(0)

        if not download_queue and not active_downloads:
            start_shutdown_timer()


# ── Routes ────────────────────────────────────────────────────────────────────

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
        "queue": [t.to_dict() for t in download_queue],
        "active": [t.to_dict() for t in active_downloads],
    }


@app.get("/task/{task_id}")
async def get_task(task_id: str):
    task = all_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@app.delete("/task/{task_id}")
async def cancel_task(task_id: str):
    task = all_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status == "queued":
        task.status = "cancelled"
        if task in download_queue:
            download_queue.remove(task)
        download_history.append(task.to_dict())
        return {"message": "Task cancelled", "task_id": task_id}
    return {"message": f"Cannot cancel task with status: {task.status}"}


@app.get("/history")
async def get_history():
    return {"history": list(reversed(download_history))}


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
    cookies: str = Form(None),
):
    if not url:
        raise HTTPException(status_code=400, detail="No URL provided")

    task = add_to_queue(url, format_id, desired_height, format, cookies or None)
    queue_pos = len(download_queue)
    wait_secs = queue_pos * 60 + len(active_downloads) * 30
    if wait_secs < 30:
        wait_str = "starting shortly"
    elif wait_secs < 120:
        wait_str = "~1 minute"
    else:
        wait_str = f"~{wait_secs // 60} minutes"

    return {
        "message": "Download started" if not queue_pos else f"Queued (position {queue_pos})",
        "task_id": task.id,
        "queue_position": queue_pos,
        "estimated_wait": wait_str,
    }


@app.on_event("startup")
async def startup_event():
    global server_start_time
    server_start_time = datetime.now()
    print(f"Tube Snatcher started at {server_start_time}")
