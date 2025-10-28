# app/main.py
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import time
import json
import asyncio
import threading
from datetime import datetime, timedelta
from .details_fetcher import fetch_video_info
from .video_downloader import download_video

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")

# Global variables for download management
download_queue = []
active_downloads = []
download_progress = {}
server_start_time = None
shutdown_timer = None

class DownloadTask:
    def __init__(self, url, format_id, desired_height, format_type, user_id=None):
        self.id = f"task_{int(time.time() * 1000)}"
        self.url = url
        self.format_id = format_id
        self.desired_height = desired_height
        self.format_type = format_type
        self.user_id = user_id
        self.status = "queued"  # queued, downloading, completed, failed
        self.progress = 0
        self.filename = None
        self.error = None
        self.start_time = None
        self.completion_time = None
        self.created_at = datetime.now()

def start_shutdown_timer():
    """Start a timer to shutdown server if no activity"""
    global shutdown_timer
    if shutdown_timer:
        shutdown_timer.cancel()
    
    shutdown_timer = asyncio.create_task(delayed_shutdown())

async def delayed_shutdown():
    """Shutdown server after 30 seconds of inactivity"""
    await asyncio.sleep(30)
    if len(download_queue) == 0 and len(active_downloads) == 0:
        print("No downloads in queue or active. Shutting down server...")
        os._exit(0)

def add_to_queue(url, format_id, desired_height, format_type, user_id=None):
    """Add download task to queue"""
    task = DownloadTask(url, format_id, desired_height, format_type, user_id)
    download_queue.append(task)
    print(f"Added task {task.id} to queue. Queue size: {len(download_queue)}")
    
    # Start processing if no active downloads
    if len(active_downloads) == 0:
        asyncio.create_task(process_download_queue())
    
    return task.id

async def process_download_queue():
    """Process download queue"""
    global active_downloads
    
    while download_queue:
        if len(active_downloads) >= 2:  # Max 2 concurrent downloads
            await asyncio.sleep(1)
            continue
            
        task = download_queue.pop(0)
        active_downloads.append(task)
        
        # Start download in background
        asyncio.create_task(execute_download(task))

async def execute_download(task):
    """Execute a single download task"""
    try:
        task.status = "downloading"
        task.start_time = datetime.now()
        task.progress = 0
        
        print(f"Starting download for task {task.id}: {task.url}")
        
        # Simulate progress updates
        progress_task = asyncio.create_task(update_progress(task))
        
        directory = "temp"
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        # Execute download
        if task.format_id:
            filename, error, title, thumbnail = download_video(task.url, task.format_id, directory, task.format_type)
        else:
            filename, error, title, thumbnail = download_video(task.url, task.desired_height, directory, task.format_type)
        
        # Cancel progress updates
        progress_task.cancel()
        
        if error:
            task.status = "failed"
            task.error = error
            print(f"Download failed for task {task.id}: {error}")
        else:
            task.status = "completed"
            task.filename = filename
            task.progress = 100
            task.completion_time = datetime.now()
            print(f"Download completed for task {task.id}: {title}")
            
    except Exception as e:
        task.status = "failed"
        task.error = str(e)
        print(f"Download error for task {task.id}: {str(e)}")
    
    finally:
        # Remove from active downloads
        if task in active_downloads:
            active_downloads.remove(task)
        
        # Check if we should shutdown
        if len(download_queue) == 0 and len(active_downloads) == 0:
            start_shutdown_timer()

async def update_progress(task):
    """Update download progress"""
    while task.status == "downloading":
        if task.progress < 90:
            task.progress += 5
        await asyncio.sleep(1)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/status")
async def get_status():
    """Get current server status and download information"""
    return {
        "server_running": True,
        "queue_size": len(download_queue),
        "active_downloads": len(active_downloads),
        "total_tasks": len(download_queue) + len(active_downloads),
        "server_uptime": str(datetime.now() - server_start_time) if server_start_time else "0:00:00"
    }

@app.get("/queue")
async def get_queue():
    """Get current download queue and active downloads"""
    return {
        "queue": [
            {
                "id": task.id,
                "url": task.url,
                "status": task.status,
                "progress": task.progress,
                "created_at": task.created_at.isoformat(),
                "filename": task.filename,
                "error": task.error
            }
            for task in download_queue
        ],
        "active": [
            {
                "id": task.id,
                "url": task.url,
                "status": task.status,
                "progress": task.progress,
                "start_time": task.start_time.isoformat() if task.start_time else None,
                "filename": task.filename,
                "error": task.error
            }
            for task in active_downloads
        ]
    }

@app.post("/fetch_details")
async def fetch_details(url: str = Form(...), format: str = Form(default="mp4")):
    if not url:
        raise HTTPException(status_code=400, detail="No URL provided")

    print(f"URL entered: {url}")
    print(f"Fetching started for {url}")
    start_time = time.time()

    result = fetch_video_info(url, format)

    end_time = time.time()
    print(f"Details fetched for {url}. Time taken: {end_time - start_time:.2f} seconds")

    async def generate():
        if result is None:
            yield json.dumps({'error': 'Failed to fetch video details'}) + '\n'
            return

        if result['type'] == 'playlist':
            yield json.dumps({
                'type': 'playlist',
                'title': result['title'],
                'thumbnail': result['thumbnail'],
                'video_count': len(result['videos']),
                'videos': []
            }) + '\n'

            for video in result['videos']:
                yield json.dumps({
                    'type': 'video_update',
                    'video': video
                }) + '\n'
        else:
            yield json.dumps(result) + '\n'

    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/download")
async def download(
    url: str = Form(...),
    format_id: str = Form(None),
    desired_height: str = Form(None),
    format: str = Form(default="mp4")
):
    try:
        if not url:
            raise HTTPException(status_code=400, detail="No URL provided")

        # Add to download queue instead of immediate download
        task_id = add_to_queue(url, format_id, desired_height, format)
        
        return {
            "message": "Download added to queue",
            "task_id": task_id,
            "queue_position": len(download_queue),
            "estimated_wait": "1-2 minutes"
        }
        
    except Exception as e:
        print(f"Error adding to queue: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add to queue: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Initialize server on startup"""
    global server_start_time
    server_start_time = datetime.now()
    print(f"Tube Snatcher Server started at {server_start_time}")
    print("Server will auto-shutdown when all downloads complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=2004, reload=False)