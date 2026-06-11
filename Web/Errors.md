# Web App — Known Issues & Backlog

## Resolved

- ~~make ui responsive specially for the mobile view~~ — Done (Session 2: mobile-responsive CSS overhaul)
- ~~remove the button of the loading circle when started downloading~~ — Done (Session 2: loading spinner hides after fetch, progress bars handle download feedback)
- ~~Details fetching takes too long (369s for a playlist) — start showing info once data arrives~~ — Done (Session 1: streaming response shows each video as it loads; Session 2: live elapsed timer with video count)
- ~~when showing the playlist remove left side description and picture boxes and show all the videos in the main parent box~~ — Done (Session 2: `playlist-mode` CSS class hides left card, full-width video list)
- ~~show "All selected videos have been downloaded" at bottom in green color~~ — Done (Session 2: green success toast slides up from bottom)

---

## Open

- **Convert from plain HTML/CSS to Next.js + FastAPI** — Planned. Would enable proper component architecture, server-side rendering, TypeScript, and better state management. Currently blocked on migration effort.
- **Run on any browser using cookies from that browser** — Partially addressed (cookie paste UI added). True browser-integrated cookie extraction would require a browser extension.
- **Find a way to reduce playlist fetch time** — Root cause: yt-dlp fetches each video's full metadata sequentially/in batches. Options: cache video metadata, reduce fields requested, or accept current streaming approach that shows videos as they load.
