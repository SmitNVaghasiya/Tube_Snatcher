# Remaining

Open items only (S = under an hour, M = a few hours, L = a day or more).

- [ ] UI redesign (Web task #20): owner picks an option in `Web/design/ui-options.html`, then port to `templates/` + `static/`. (L)
- [ ] Extension download-location prompt: choose one-time / always / ask monthly, then wire it into the popup and `download_location`. (M)
- [ ] Migrate Extension `app.py` from `@app.on_event` to a lifespan handler; needs a `tests/conftest.py` update. (S)
- [ ] `SECRET_KEY` default fallback in `Extension/backend/core/config.py` should fail loudly when `DEBUG` is off. (S)
- [ ] CORS allows any browser-extension origin with credentials; pin the real extension ID. (S)
- [ ] `download-with-cookies` / `download-playlist` accept a client-supplied `download_location` with no validation (the old writable-check helper was dead code and was removed). Restrict to known locations. (S)
- [ ] `/api/v1/task/*`, `/queue` and `DownloadManager.add_to_queue` are now unused by the popup (only the dead `Extension/web/` used them); delete them or wire the popup to the queue. (M)
- [ ] Leftover audit items: `Extension/frontend/icon/create_icons.py`, stale `Extension/.qwen/` and `Extension/pending_work.md`. (`temp.py` is kept on purpose as a quick test script.) (S)
- [ ] Replace deprecated `datetime.utcnow()` (auth, routes, models) with timezone-aware `datetime.now(UTC)`. (S)
- [ ] `popup.js` references `/api/v1/auth/verify-token`, which the backend has never had. (S)
