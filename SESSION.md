# Session Log

This file tracks significant development sessions and what was changed in each.

---

## Session 2 — 2026-06-11 (Features + Polish)

**Branch:** `claude/ui-backend-improvements-62tnzr`  
**PRs merged in:** #2 (test suite), #3 (UI/backend improvements)

### What was implemented

#### Web App — New Features
- **Real-time download progress**: Each queued download shows a live progress bar that polls `/task/{id}` every second. Progress is driven by real yt-dlp `progress_hooks` (not simulated).
- **Task cancel button**: Each progress card has a ✕ button that calls `DELETE /task/{id}` to cancel queued tasks.
- **Download history**: `/history` endpoint returns the last 100 completed/failed/cancelled tasks. A history section renders below the results panel and updates after each task finishes.
- **Cookie authentication (web app)**: A collapsible "⚙ Cookie Auth" panel lets users paste YouTube cookies for age-restricted or member-only videos. Cookies are stored in `sessionStorage` and passed with every download request. The backend writes them to a temp file for yt-dlp and deletes immediately after.
- **Playlist full-width layout**: When a playlist is detected, the left-side thumbnail/description card is hidden and the video list takes full width (`playlist-mode` CSS class).
- **Success toast**: A green sliding toast appears at the bottom of the screen when a download completes or a playlist batch is fully queued.

#### Web App — Fixes
- Replaced fake simulated progress (`task.progress += 5`) with real yt-dlp `progress_hook` callbacks.
- Replaced `os._exit(0)` with `os.kill(os.getpid(), signal.SIGTERM)` for graceful shutdown.
- Moved `fetch_video_info` and `download_video` calls into `asyncio.get_running_loop().run_in_executor()` so they no longer block the FastAPI event loop.
- Used `asyncio.get_running_loop()` instead of deprecated `asyncio.get_event_loop()`.
- Estimated wait time in `/download` response is now dynamic based on queue depth.
- Added `all_tasks` dict for O(1) task lookup by ID.
- Removed Cloudflare challenge iframe that was left over from a previous deployment.
- Removed jQuery dependency — all DOM manipulation and HTTP calls now use vanilla JS and `fetch()`.

#### Extension Backend
- **Removed auto-shutdown**: Deleted `_start_shutdown_timer()` and `_shutdown_after_delay()` from `DownloadManager`. The server is now expected to run persistently as a service (not auto-terminate).
- Fixed `cookie_file_path` `NameError` in `finally` block of `video_downloader.py`.
- Removed deprecated `prefer_ffmpeg` yt-dlp option.
- Used `asyncio.get_running_loop()` instead of `asyncio.get_event_loop()`.
- Cleaned up `requirements.txt`: removed unused `passlib[bcrypt]`, `pymongo` (sync driver, motor is used), `asyncio` (stdlib).

#### Dependencies
- Updated yt-dlp to `2026.06.09` in both Web and Extension (from `2025.3.26`). Key changes in new version: improved YouTube player fallbacks, CVE fixes for cookie handling (CVE-2026-50019), aria2c HLS/DASH removed (not used here).

#### Documentation
- `README.md`: Complete rewrite — corrected framework (Flask → FastAPI), port (8000 → 2004), added project structure, API table, feature list, cookie instructions.
- `SESSION.md`: Created (this file).
- `DECISION.md`: Created — documents key architectural decisions and their rationale.
- `Web/Errors.md`: Updated — marked resolved issues.

---

## Session 1 — 2025-04-27 (Initial Release)

Initial project setup with:
- Web app using FastAPI + yt-dlp for video/playlist downloading
- Chrome/Firefox extension with popup UI and injected download button
- MongoDB integration for download analytics (extension backend)
- JWT authentication for extension API
- Basic dark-theme UI with playlist support
