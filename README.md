# Tube Snatcher

Download YouTube videos and audio — free, fast, and at HD quality.

![Tube Snatcher Screenshot](https://github.com/user-attachments/assets/4183db2c-c86a-4408-8863-7edcf6468b30)

---

## What It Does

Tube Snatcher lets you paste any YouTube URL and download it as MP4 (video) or MP3 (audio) at the best available quality. It supports:

- Single videos with full format/resolution selection
- Playlists with per-video download controls and batch selection
- Age-restricted and member-only content via cookie authentication
- Real-time download progress tracking per task
- Download history for the current session

---

## Project Structure

```
Tube_Snatcher/
├── Web/                        # Standalone web application
│   ├── main.py                 # FastAPI entry point
│   ├── app/
│   │   ├── main.py             # Routes, queue management, task tracking
│   │   ├── video_downloader.py # yt-dlp download wrapper (progress + cookies)
│   │   └── details_fetcher.py  # Video/playlist info extraction
│   ├── templates/
│   │   └── index.html          # Single-page UI
│   ├── static/
│   │   ├── script.js           # Vanilla JS — streaming, polling, history, cookies
│   │   └── styles.css          # Dark theme, mobile-responsive
│   └── requirements.txt
│
├── Extension/                  # Chrome/Firefox browser extension
│   ├── frontend/               # Extension popup and content scripts
│   │   ├── manifest.json       # Extension config (Manifest v3)
│   │   ├── popup.html/js       # Download UI shown on click
│   │   ├── content.js          # Injects Download button on YouTube
│   │   └── background.js       # Service worker
│   └── backend/                # FastAPI server for extension
│       ├── app.py              # FastAPI app + CORS setup
│       ├── api/routes.py       # All API endpoints (/api/v1/...)
│       ├── core/
│       │   ├── models.py       # Pydantic schemas
│       │   ├── config.py       # Environment-based settings
│       │   ├── download_manager.py  # Async download queue
│       │   ├── video_downloader.py  # yt-dlp wrapper with progress hooks
│       │   ├── video_fetcher.py     # Info + format extraction
│       │   ├── database.py          # MongoDB analytics/history
│       │   ├── auth.py              # JWT token management
│       │   └── utils.py             # URL validation, cookie sanitization
│       ├── tests/              # 179 tests (unit + integration)
│       └── requirements.txt
```

---

## Web App — Quick Start

### Requirements

- Python 3.10+
- [ffmpeg](https://ffmpeg.org/download.html) in your PATH

### Install & Run

```bash
cd Web
pip install -r requirements.txt
python main.py
```

Open `http://127.0.0.1:2004` in your browser.

### How It Works

1. Paste a YouTube URL — video info loads automatically as you type
2. Choose MP4 or MP3
3. For videos: pick a resolution and click Download
4. For playlists: browse videos, select by checkbox or range (`1,4,7-10`), then download
5. Watch live progress bars per download task
6. View recent download history below

### Cookie Authentication (for restricted videos)

Click **⚙ Cookie Auth** below the URL bar, paste your YouTube cookies in Netscape format. Cookies are stored only in your browser session — never sent anywhere except your local server.

---

## Extension — Quick Start

1. Start the backend server: `cd Extension/backend && uvicorn app:app --port 2004`
2. In Chrome: `chrome://extensions/` → Enable Developer Mode → Load Unpacked → select `Extension/frontend`
3. Visit any YouTube video page and click the **Download** button

See [`Extension/SETUP.md`](Extension/SETUP.md) for full setup instructions.

---

## Key Technologies

| Layer | Technology |
|---|---|
| Backend | FastAPI (async) |
| Downloading | yt-dlp 2026.06.09 |
| Database (extension) | MongoDB + Motor (async) |
| Auth (extension) | JWT (python-jose) |
| Frontend | Vanilla JS + Fetch API |
| Styling | Custom CSS (dark, mobile-responsive) |
| Tests | pytest (179 tests) |

---

## API Endpoints (Web App)

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Web UI |
| `POST` | `/fetch_details` | Streaming video/playlist info |
| `POST` | `/download` | Queue a download |
| `GET` | `/task/{id}` | Poll task status + progress |
| `DELETE` | `/task/{id}` | Cancel a queued task |
| `GET` | `/history` | Session download history |
| `GET` | `/queue` | Current queue + active downloads |
| `GET` | `/status` | Server health |

---

## Deployment Notes

- YouTube's anti-bot measures may require cookies for server-side requests
- Use cookies extracted in **incognito mode** for longer validity
- For production: serve over HTTPS to protect cookie transmission
- yt-dlp needs updating periodically as YouTube changes its internals

---

## Disclaimer

For educational and personal use only. Respect YouTube's Terms of Service and copyright law. Do not download content you do not have rights to.
