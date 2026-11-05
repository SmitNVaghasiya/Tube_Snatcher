# Project Summary

## Overall Goal
Create a YouTube video/audio downloader browser extension with a Python FastAPI backend that can download videos from YouTube with authentication, cookie support, and queue management.

## Key Knowledge

### Technology Stack
- **Backend**: Python FastAPI application running on port 2004
- **Frontend**: Chrome extension with manifest v3
- **Database**: MongoDB Atlas integration (Motor async client)
- **Video Processing**: yt-dlp library (v2026.06.09)

### Architecture
- **Backend Structure**: 
  - [app.py](file:///c:/Users/smitv/OneDrive/Desktop/Projects/Tube%20Snatcher/Extension/backend/app.py) - FastAPI application configuration and CORS middleware.
  - [main.py](file:///c:/Users/smitv/OneDrive/Desktop/Projects/Tube%20Snatcher/Extension/backend/main.py) - Server entry point starting uvicorn on port 2004.
  - [routes.py](file:///c:/Users/smitv/OneDrive/Desktop/Projects/Tube%20Snatcher/Extension/backend/api/routes.py) - All backend routes for download execution, auth tokens, history, analytics, and status.
  - [config.py](file:///c:/Users/smitv/OneDrive/Desktop/Projects/Tube%20Snatcher/Extension/backend/core/config.py) - Settings and environment variables loading via python-dotenv.
  - [download_manager.py](file:///c:/Users/smitv/OneDrive/Desktop/Projects/Tube%20Snatcher/Extension/backend/core/download_manager.py) - Concurrency-limited async download task queue (max 2 parallel downloads).
  - [video_downloader.py](file:///c:/Users/smitv/OneDrive/Desktop/Projects/Tube%20Snatcher/Extension/backend/core/video_downloader.py) - yt-dlp wrapper with progress hooks.
  - [video_fetcher.py](file:///c:/Users/smitv/OneDrive/Desktop/Projects/Tube%20Snatcher/Extension/backend/core/video_fetcher.py) - Video and playlist metadata extraction.
  - [database.py](file:///c:/Users/smitv/OneDrive/Desktop/Projects/Tube%20Snatcher/Extension/backend/core/database.py) - MongoDB database logger and analytics manager.
  - [auth.py](file:///c:/Users/smitv/OneDrive/Desktop/Projects/Tube%20Snatcher/Extension/backend/core/auth.py) - JWT token generator and validator.
  - [utils.py](file:///c:/Users/smitv/OneDrive/Desktop/Projects/Tube%20Snatcher/Extension/backend/core/utils.py) - URL validation, Netscape cookie sanitization.
- **Frontend Structure**:
  - [manifest.json](file:///c:/Users/smitv/OneDrive/Desktop/Projects/Tube%20Snatcher/Extension/frontend/manifest.json) - Manifest V3 configuration with cookies, activeTab, and storage permissions.
  - [popup.html](file:///c:/Users/smitv/OneDrive/Desktop/Projects/Tube%20Snatcher/Extension/frontend/popup.html) / [popup.css](file:///c:/Users/smitv/OneDrive/Desktop/Projects/Tube%20Snatcher/Extension/frontend/popup.css) / [popup.js](file:///c:/Users/smitv/OneDrive/Desktop/Projects/Tube%20Snatcher/Extension/frontend/popup.js) - Chrome extension popup UI supporting quick download buttons, URL downloading, layout selection, history viewing, and settings.
  - [content.js](file:///c:/Users/smitv/OneDrive/Desktop/Projects/Tube%20Snatcher/Extension/frontend/content.js) - Content script that runs on YouTube pages to extract page info and store video details.
  - [background.js](file:///c:/Users/smitv/OneDrive/Desktop/Projects/Tube%20Snatcher/Extension/frontend/background.js) - Service worker that handles server status checks, messaging, and download queue updates.
  - [config.js](file:///c:/Users/smitv/OneDrive/Desktop/Projects/Tube%20Snatcher/Extension/frontend/config.js) - Centralized backend configuration.

### Environment Configuration
- **Required Variables**: `MONGODB_URI`, `DATABASE_NAME`, `SECRET_KEY`, `COOKIE_ENCRYPTION_KEY`, `PORT`, `HOST`
- **Port**: 2004 (set in both frontend and backend)
- **API Endpoints**: `/api/v1/` prefix for all backend endpoints

### Security & Authentication
- JWT-based authentication system for backend-extension requests.
- YouTube cookie extraction via Chrome Extension APIs (`chrome.cookies`) for access to restricted/premium videos.
- Cookie encryption using Fernet symmetric keys (`cryptography` library) before sending to the backend.

### API Endpoints Available
- `GET /api/v1/auth/get-token` - Authenticated access token generation
- `GET /api/v1/auth/verify-token` - Token validation check
- `GET /api/v1/status` - Basic server queue status and uptime
- `GET /api/v1/queue` - Detailed list of active and queued tasks
- `GET /api/v1/task/{task_id}` - Poll status of a specific task
- `DELETE /api/v1/task/{task_id}` - Cancel a queued/active download task
- `POST /api/v1/clear-queue` - Clear all pending queued downloads
- `GET /api/v1/history` - Get session download history
- `GET /api/v1/analytics` - Get database-backed download usage statistics
- `GET /api/v1/download-locations` - Retrieve common writable local download directories
- `POST /api/v1/fetch-details-with-cookies` - Fetch metadata and formats (supports single video/playlists)
- `POST /api/v1/download-with-cookies` - Queue download using cookies (JSON-based)
- `POST /api/v1/download-playlist` - Download full playlist using cookies
- `POST /api/v1/fetch-details` - Fetch metadata (legacy, form-based)
- `POST /api/v1/download` - Queue download (legacy, form-based)

### Standalone Web Application (Root /Web)
- Contains a standalone FastAPI single-page web app.
- Served on port 8000 (standard local port) with a dark theme custom CSS and vanilla streaming JS.
- Utilizes the same core download utilities and supports streaming playlist extraction, sessionStorage cookies, and O(1) in-memory task lookup dictionary (`all_tasks`).

## Recent Actions

### Git Synchronization & Cleanup
- Synchronized local repository with remote `origin/main`, fast-forwarding 7 remote commits.
- Removed all binary `__pycache__` folders from Git tracking and updated `.gitignore` rules to keep the index clean.
- Resolved conflict in `Extension/backend/requirements.txt` to keep both remote yt-dlp updates and local `python-dotenv` support.

### Backend Improvements
- **Graceful Shutdown**: Replaced `os._exit(0)` with `signal.SIGTERM` triggers to ensure uvicorn finishes active downloads before shutting down.
- **Removed Extension Auto-Shutdown**: Removed uvicorn auto-shutdown functionality from the extension backend to ensure it runs as a persistent service (unlike the Web app's 30s inactivity shutdown).
- **Test Coverage**: Added a comprehensive test suite of 179 unit and integration tests (under `Extension/backend/tests`) using pytest.

### Frontend Enhancements
- Added quick download buttons for MP4 and MP3 best quality.
- Added URL input downloader section for downloading YouTube links directly without visiting them.
- Implemented real-time progress bars, download history lists, and custom location directory paths.
- Added layout toggling for single-video vs. playlist-mode views.

## Current Plan & Next Steps

### Current Plan
- [DONE] MongoDB Atlas database integration.
- [DONE] JWT authentication and automatic cookie extraction/encryption.
- [DONE] Multi-format single video and full playlist downloading.
- [DONE] Comprehensive pytest test suite coverage.
- [IN PROGRESS] Implementing download location user prompt flow in popup interface.
- [IN PROGRESS] Cleaning up leftover auto-shutdown messages and configuration from the backend codebase.

### Next Steps
1. **Interactive Location Prompt**: Implement a centered modal popup in the extension frontend that asks the user if they want to remember a selected custom download directory (with options for one-time use, permanent default, or monthly reminder).
2. **Auto-Shutdown Scrub**: Clean up all remaining references to uvicorn/backend auto-shutdown feature (e.g., config environment variables, print statements on startup, configuration keys in `render.yaml`, and obsolete mock patches in tests).
3. **Verify Local Environment & Tests**: Configure the virtual environment with pytest and ensure all 179 tests pass locally.

---

## Summary Metadata
**Update time**: 2026-06-15T00:15:00.000Z
