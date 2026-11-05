"""Download queue: fixed worker pool over an asyncio.Queue, with in-memory history."""
import asyncio
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from yt_dlp.utils import DownloadCancelled

from .video_downloader import download_video, format_selector

FINISHED = {"completed", "failed", "cancelled"}


def _iso(t: datetime | None) -> str | None:
    return t.isoformat() if t else None


@dataclass(eq=False)
class Task:
    url: str
    format_type: str
    format_id: str | None = None
    height: str | None = None
    cookies: str | None = field(default=None, repr=False)
    id: str = field(default_factory=lambda: uuid4().hex[:12])
    status: str = "queued"
    progress: int = 0
    filename: str | None = None
    video_title: str | None = None
    error: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    start_time: datetime | None = None
    completion_time: datetime | None = None
    cancel: threading.Event = field(default_factory=threading.Event, repr=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id, "url": self.url, "status": self.status, "progress": self.progress,
            "video_title": self.video_title, "format_type": self.format_type, "error": self.error,
            "created_at": _iso(self.created_at), "start_time": _iso(self.start_time),
            "completion_time": _iso(self.completion_time),
        }


class DownloadManager:
    MAX_TASKS = 200  # finished tasks beyond this are forgotten (history keeps summaries)

    def __init__(self, directory: Path, workers: int = 2, history_size: int = 100):
        self.directory = directory
        self.workers = workers
        self.tasks: dict[str, Task] = {}
        self.history: deque[dict] = deque(maxlen=history_size)
        self._queue: asyncio.Queue[Task] = asyncio.Queue()
        self._pool: list[asyncio.Task] = []

    # ── lifecycle ──
    def start(self) -> None:
        self._pool = [asyncio.create_task(self._work()) for _ in range(self.workers)]

    async def stop(self) -> None:
        for t in self.tasks.values():
            t.cancel.set()  # running threads bail out at their next progress tick
        for w in self._pool:
            w.cancel()
        await asyncio.gather(*self._pool, return_exceptions=True)

    # ── queries ──
    def _by_status(self, status: str) -> list[Task]:
        return [t for t in self.tasks.values() if t.status == status]

    @property
    def queued(self) -> list[Task]:
        return self._by_status("queued")

    @property
    def active(self) -> list[Task]:
        return self._by_status("downloading")

    @property
    def busy(self) -> bool:
        return any(t.status not in FINISHED for t in self.tasks.values())

    # ── commands ──
    def submit(self, url, format_type, format_id=None, height=None, cookies=None) -> tuple[Task, int]:
        """Returns (task, number of tasks that must start before it can)."""
        task = Task(url, format_type, format_id, height, cookies)
        self.tasks[task.id] = task
        self._queue.put_nowait(task)
        free = max(0, self.workers - len(self.active))
        return task, max(0, len(self.queued) - free)

    def cancel(self, task: Task) -> bool:
        if task.status == "queued":  # the worker skips it when it reaches it
            self._finish(task, "cancelled")
        elif task.status == "downloading":
            task.cancel.set()
        else:
            return False
        return True

    # ── internals ──
    async def _work(self) -> None:
        while True:
            task = await self._queue.get()
            if task.status == "queued":
                await self._run(task)

    async def _run(self, task: Task) -> None:
        task.status, task.start_time = "downloading", datetime.now()
        selector = format_selector(task.format_type, task.format_id, task.height)

        def on_progress(pct: float) -> None:  # called from the download thread
            task.progress = max(task.progress, min(int(pct), 99))  # monotonic across video+audio streams

        try:
            task.filename, task.video_title = await asyncio.to_thread(
                download_video, task.url, selector, self.directory, task.format_type,
                on_progress, task.cancel, task.cookies,
            )
            task.progress = 100
            self._finish(task, "completed")
        except DownloadCancelled:
            self._finish(task, "cancelled")
        except Exception as e:
            if task.cancel.is_set():
                self._finish(task, "cancelled")
            else:
                self._finish(task, "failed", str(e))

    def _finish(self, task: Task, status: str, error: str | None = None) -> None:
        task.status, task.error = status, error
        task.completion_time = datetime.now()
        task.cookies = None  # never keep credentials longer than the download
        self.history.append(task.to_dict())
        for tid, t in list(self.tasks.items()):  # oldest first
            if len(self.tasks) <= self.MAX_TASKS:
                break
            if t.status in FINISHED:
                del self.tasks[tid]
