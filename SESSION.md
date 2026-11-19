# Session Log

This file tracks significant development sessions and what was changed in each.

---

## Session 3 — 2026-11-20 (Over-engineering audit + cleanup)

Ran a ponytail over-engineering audit across the repo, then applied it. Nothing committed.

### Web
- Download results now report the resolution actually delivered: `download_video` returns the real height, `Task` stores `actual_height`, and `to_dict()`/history include `height` + `actual_height`. The progress card and history row show e.g. "Downloaded at 720p (1080p not available)" (task #19). One assert added to `tests/test_core.py`.
- Removed the unused `/queue` route, `Web/Errors.md` (superseded by `task.md`), and the `jinja2` dependency (the index page is served with `FileResponse`).

### Extension backend
- Removed all auto-shutdown leftovers (`SHUTDOWN_DELAY`, banner print, `_start_shutdown_timer` test patch, render.yaml/README/SETUP mentions).
- Removed dead code: `get_current_user` (it was broken and unused), `get_video_id_from_url`, `/analytics` + `/clear-queue` routes, `DownloadManager.clear_queue`, `DatabaseManager.get_analytics`, unused models (`Token`, `TokenType`, `DownloadRecord`, `UniqueVisitor`, `AnalyticsResponse`), and `_validate_download_location`. Their tests were removed too.
- `verify_token` no longer re-checks `exp` by hand (python-jose already enforces it).
- One `cookie_file()` context manager in `core/utils.py` replaces five copy-pasted temp-file blocks and always deletes the file.
- Merged the duplicate fetch/download routes: `VideoFetcher.fetch_details` and `VideoDownloader.download_playlist` now do the yt-dlp work; the routes only call them. Playlist downloads no longer block the event loop. The legacy `/fetch-details` and `/download` routes were deleted (the popup, content and background scripts never call them).
- All `print()` calls became module loggers (no emoji). `main.py` is a plain `uvicorn.run`; `app.py` lost the redundant `@app.options` route and uses `allow_origin_regex` (the old `chrome-extension://*` entries never matched). Dropped lower-case env fallbacks and `pydantic-settings`.
- Tests: 159 pass (was ~179 before removing tests for deleted code; 2 added for `cookie_file`, 2 for `fetch-details-with-cookies`).
- READMEs/SETUP now say the backend is started manually and never auto-shuts down (an MV3 extension cannot launch processes).

### Not done / left
See `TODO.md`.

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
