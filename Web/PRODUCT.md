# Product

## Register

product

## Users

Primarily the owner, running the app locally on a desktop; also friends/family who paste a link and expect it to just work, and portfolio visitors (recruiters, GitHub readers) who judge the craft from screenshots or a demo. Context: they have a YouTube URL in the clipboard and want the file on disk with as few decisions as possible. Playlists of 100-300 videos are a normal case, not an edge case.

## Product Purpose

Local YouTube video/audio downloader (FastAPI + yt-dlp). Paste a URL, choose MP4 or MP3, optionally pick a resolution or a subset of a playlist, watch honest progress, and find the file in the downloads folder. Success: a first-time user completes a download without reading anything, and a playlist of 300 videos is still easy to scan and select from.

## Brand Personality

Polished, premium, calm, minimal. Quiet confidence: one obvious action per state, generous space, refined type, subtle depth. It should feel like a paid native utility, not a hobby script.

## Anti-references

- Sketchy downloader sites: neon green buttons, ads, "FREE HD!!" tagline energy.
- Generic dark SaaS: near-black plus purple/blue gradient, identical rounded card grids.
- A YouTube clone: red/white imitation of YouTube's own look.
- Cluttered power-tool UIs: many panels and options visible at once.

## Design Principles

1. **One obvious next step.** At any moment the primary action is unmistakable; advanced controls (cookies, per-format choice) stay folded away until needed.
2. **Show real state, never fake it.** Progress, queue position, and the actual resolution downloaded come from the server; when something falls back or fails, say what happened and what to do.
3. **Built for 300 items.** Playlists are scanned, filtered, and bulk-selected, not scrolled card by card.
4. **Quiet until it matters.** Restraint in color and motion; the accent is reserved for the primary action and live progress.
5. **Looks as good in a screenshot as it works in use.** Portfolio-grade craft is part of the brief, not decoration on top.

## Accessibility & Inclusion

Target WCAG 2.2 AA: 4.5:1 body contrast, visible keyboard focus on every control, full keyboard operation (paste, select, download, cancel), labels on all inputs, status changes announced via live regions, `prefers-reduced-motion` respected, no information conveyed by color alone (status always has an icon or word). (Defaults assumed; not yet confirmed by the owner.)
