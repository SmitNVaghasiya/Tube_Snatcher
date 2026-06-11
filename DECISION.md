# Architecture Decision Log

Documents the key design decisions made in this project and the reasoning behind them.

---

## ADR-001 — FastAPI over Flask

**Decision:** Use FastAPI as the web framework for both the web app and extension backend.

**Rationale:**
- Native `async/await` support allows non-blocking I/O — critical since yt-dlp downloads are slow blocking operations that need to run in thread pools without blocking other requests.
- Built-in Pydantic validation reduces boilerplate for request/response schemas.
- Auto-generated OpenAPI docs aid development.
- `StreamingResponse` handles playlist fetch streaming cleanly.

**Trade-off:** Flask is simpler for beginners and has a wider ecosystem, but its sync model would require threading hacks to stay responsive during downloads.

---

## ADR-002 — In-memory queue over Celery/Redis

**Decision:** Use a simple Python list + `asyncio.create_task()` for the download queue instead of a dedicated task queue (Celery, RQ, etc.).

**Rationale:**
- The web app is designed to run locally or as a single-user server. Celery/Redis adds significant operational complexity (two extra services, config, monitoring).
- Max 2 concurrent downloads is enforced by checking `len(active_downloads) < 2` in the processing loop — sufficient for the use case.
- State lives only in the running process; a restart clears the queue, which is acceptable.

**Trade-off:** State is lost on server restart. Not horizontally scalable. For a multi-user deployment, switch to Celery + Redis. Tracked in future improvements.

---

## ADR-003 — Vanilla JS over jQuery (Web Frontend)

**Decision:** Removed jQuery dependency and rewrote all frontend JS using vanilla DOM APIs and `fetch()`.

**Rationale:**
- jQuery was used only for `$.ajax()` and simple DOM selectors (`$('#el')`). All of these are natively available in modern browsers.
- Removes a 88KB CDN dependency from every page load.
- `fetch()` returns Promises and supports streaming via `response.body.getReader()` — the jQuery ajax API does not support streaming responses.
- Vanilla code is easier to debug in browser DevTools.

**Trade-off:** Slightly more verbose DOM code in a few places, but no meaningful downside.

---

## ADR-004 — Cookies in sessionStorage, not localStorage

**Decision:** YouTube cookies entered by the user are stored in `sessionStorage`, not `localStorage`.

**Rationale:**
- YouTube authentication cookies grant access to the user's account. Persisting them in `localStorage` would keep them indefinitely, surviving browser restarts — a security risk if the user shares a machine.
- `sessionStorage` clears automatically when the browser tab closes, limiting exposure.
- Cookies are never sent to any third party — only to the local FastAPI server over loopback.

**Trade-off:** Users must re-paste cookies after each browser session. Acceptable given the security benefit.

---

## ADR-005 — Real yt-dlp progress hooks over simulated progress

**Decision:** Wire `progress_hooks` from yt-dlp directly into task progress tracking instead of using a background `asyncio.sleep(1)` ticker that incremented progress by 5% per second.

**Rationale:**
- Simulated progress was completely disconnected from actual download speed. A 2-second download and a 10-minute download both looked the same.
- yt-dlp's `progress_hook` provides `downloaded_bytes` and `total_bytes` on every chunk, giving accurate real-time percentages.
- The hook runs in the executor thread and writes to `task.progress` (an int), which is safe under Python's GIL.

**Trade-off:** Progress is 0% until yt-dlp has enough data to estimate total size (typically a second or two into the download). Acceptable.

---

## ADR-006 — SIGTERM over os._exit for graceful shutdown

**Decision:** Replace `os._exit(0)` with `os.kill(os.getpid(), signal.SIGTERM)` in the auto-shutdown timer.

**Rationale:**
- `os._exit(0)` immediately terminates the process at the OS level, bypassing Python's cleanup handlers, atexit functions, and any in-progress I/O flushes. Active downloads would be interrupted mid-file.
- `signal.SIGTERM` triggers uvicorn's graceful shutdown sequence, which waits for in-flight requests to finish before exiting.

**Trade-off:** None. SIGTERM is strictly better here.

---

## ADR-007 — Remove auto-shutdown from Extension backend

**Decision:** Removed the 1-hour inactivity auto-shutdown from `DownloadManager` in the extension backend.

**Rationale:**
- The extension backend is intended to run as a persistent local service, not a temporary process. Auto-shutting down creates a poor UX where users return to YouTube only to find downloads failing silently because the server went away.
- The `pending_work.md` file explicitly flagged this as a bug to fix.
- The web app's auto-shutdown (30-second timer on inactivity) is intentional — it runs as a short-lived process, not a service.

**Trade-off:** Server stays running indefinitely. Users should manage the process lifecycle themselves (system service, startup script, etc.).

---

## ADR-008 — Task ID dict for O(1) lookup

**Decision:** Added `all_tasks: dict[str, DownloadTask]` in the web app to enable fast lookup of any task by ID.

**Rationale:**
- The `/task/{id}` and `DELETE /task/{id}` endpoints are polled by the frontend every second for every active download. Without a dict, each poll would O(n) scan through `download_queue + active_downloads + completed_tasks`.
- A dict keyed on task ID is O(1) and simpler.

**Trade-off:** Tasks accumulate in `all_tasks` for the lifetime of the server. Capped implicitly by `download_history` at 100 entries. For long-running servers, add an LRU eviction policy.

---

## ADR-009 — MongoDB only for Extension, not Web App

**Decision:** The extension backend persists download history to MongoDB. The web app uses in-memory history only.

**Rationale:**
- The web app is a lightweight local tool. Adding a MongoDB dependency for a tool that auto-shuts down adds unnecessary setup friction.
- The extension backend is designed as a production service with analytics needs (unique user counts, download stats, failure rates). MongoDB is justified there.
- Web app history is session-only and disappears on server restart — acceptable for the use case.

**Trade-off:** Web app history is ephemeral. If persistence is needed, the `download_history` list can be swapped for SQLite with minimal code changes.

---

## ADR-010 — Playlist-mode CSS class for layout switching

**Decision:** Toggle a `playlist-mode` class on the results container instead of using separate HTML templates for single video vs. playlist.

**Rationale:**
- A single HTML structure with a CSS class toggle is simpler and avoids duplicating the container markup.
- The class hides the left thumbnail/description card and gives the video list full width — as requested in `Errors.md`.
- JavaScript simply adds/removes the class when the stream indicates a playlist or single video.

**Trade-off:** The left card HTML is always in the DOM (just hidden). Negligible overhead.
