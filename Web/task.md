# Web App — Task List

Review of `Web/` (FastAPI + yt-dlp + vanilla JS). Tracks every issue found plus the modernization pass.
`[x]` = done, `[ ]` = open. Run: `uv sync && uv run main.py` → http://127.0.0.1:2004

## Bugs & weak spots (from review)

- [x] **1. Fake playlist streaming.** `/fetch_details` awaited the *whole* playlist before first `yield`.
  Fix: flat-extract playlist only (298 videos stream in ~1s); no per-video lookups at all, formats resolve at download time.
- [x] **2. Playlist fetch blocks on slowest of each batch of 5, default-size thread pool.**
  Fix: removed entirely (see 1). Downloads: 3 workers (`TS_WORKERS`) + 4 parallel fragments.
- [x] **3. Task ID collision** (`task_<ms>`): two adds in the same ms overwrite each other. Fix: `uuid4` ids.
- [x] **4. Unbounded memory / cookies kept forever.** `all_tasks` never pruned; `task.cookies` retained.
  Fix: cap finished tasks, wipe cookies as soon as the download ends.
- [x] **5. Queue busy-loop** (`sleep(1)` spin + racy "start loop if idle" check).
  Fix: `asyncio.Queue` + fixed worker pool (3 by default, `TS_WORKERS`).
- [x] **6. Shutdown timer race / never fires.** Timer only armed after a download; `os.kill(SIGTERM)` is a hard kill on Windows; `reload=True` fights it.
  Fix: idle watcher (no requests + no downloads for N s), graceful `server.should_exit`, page heartbeat, no reloader.
- [x] **7. No cancel for running downloads; `temp/` never cleaned / misleading name.**
  Fix: cancel via `DownloadCancelled` in progress hook; output dir is `downloads/` (env `TS_DOWNLOAD_DIR`), cancelled/failed partials removed.
- [x] **8. Redundant `FFmpegVideoConvertor`** (re-encodes after merge!) on top of `merge_output_format`.
  Fix: lossless `FFmpegVideoRemuxer`; take final path from `requested_downloads` instead of guessing extension.
- [x] **9. `details_fetcher.py` duplication / dead code / crash.** Format-building copy-pasted twice, unused vars, debug print, `format_note=None` → `.lower()` crash, bogus yt-dlp options (`get_filesize`, `dump_single_json`).
  Fix: one `describe_format()` helper, tbr-based size estimate, null-safe.
- [x] **10. `requirements.txt` broken on clean install.** No `uvicorn`, no `python-multipart` (needed by `Form`), useless `gunicorn`/`requests`/`pycryptodome`, unpinned fastapi.
  Fix: `pyproject.toml` + `uv.lock`, `yt-dlp[default]`, drop dead deps.
- [x] **11. Deprecated APIs.** `@app.on_event("startup")`, old `TemplateResponse(name, {"request": …})`, `Form(...)` defaults, cwd-relative static/template paths.
  Fix: lifespan, new `TemplateResponse(request, name)`, `Annotated` params, paths relative to the package.
- [x] **12. Frontend XSS surface.** Only `<`/`>` escaped; `v.url`, thumbnails, `format_note`, progress title injected raw into attributes/HTML (and persisted + re-injected from `localStorage`).
  Fix: one `esc()` helper used on every interpolation.
- [x] **13. Made-up ETA** (`queue_pos*60`). Fix: removed; return real `queue_position` only.

## Extra problems found while fixing

- [x] **14. Video-only format downloaded with no audio.** Quick-download and per-format buttons send a `format_id`
  that is usually video-only. Fix: `id[acodec=none]+bestaudio/id`.
- [x] **15. No input validation at the trust boundary.** Fix: http(s) URL only, `format` ∈ {mp4,mp3}, `format_id`/`desired_height` pattern-checked.
- [x] **16. YouTube needs a JS runtime now** (yt-dlp EJS challenge solver). Fix: enable `node` (installed via nvm) + `yt-dlp[default]` ships `yt-dlp-ejs`.
- [x] **17. Playlist order** must stay stable on the client (rows indexed by arrival). Fix: server emits in order.
- [x] **18. ffmpeg missing → opaque error.** Fix: startup warning if not on PATH.

## Housekeeping

- [x] `pyproject.toml` + `.python-version` + `uv.lock` (replaces `requirements.txt`).
- [x] `Web/.gitignore` (`.venv/`, `downloads/`).
- [x] Small pytest suite (`uv run pytest`).
- [x] Next.js migration (from `Errors.md`) — **deliberately dropped**: no build step needed, nvm/Node not required by this project.

## Open (follow-ups)

- [x] **19. Resolution fallback is silent.** Playlist dropdown offers a fixed list (2160p…144p) because per-video
  format lookups were too slow. If a video has no stream at the chosen height, yt-dlp quietly downloads the best one
  below it. Show that: after download, report the actual height on the task (`requested_downloads[0]["height"]`)
  and render e.g. "Downloaded at 720p (1080p not available)" in the progress card / history row.
- [ ] **20. UI redesign.** Audit + 3 design options in `design/ui-options.html`; pick one, then port to `templates/` + `static/`.
