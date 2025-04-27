# app/main.py
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
import time
import json
from .details_fetcher import fetch_video_info
from .video_downloader import download_video

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

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

        directory = "temp"
        if not os.path.exists(directory):
            os.makedirs(directory)

        print(f"Download started for {url}")
        if format_id:
            filename, error, title, thumbnail = download_video(url, format_id, directory, format)
        else:
            filename, error, title, thumbnail = download_video(url, desired_height, directory, format)

        if error:
            print(f"Error during download: {error}")
            raise HTTPException(status_code=500, detail=error)

        print(f"Downloaded: {title}")
        return {"message": f"Downloaded: {title}", "filename": filename, "thumbnail": thumbnail}
    except Exception as e:
        print(f"Error during download: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")