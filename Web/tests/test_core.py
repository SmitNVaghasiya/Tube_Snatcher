import time

import pytest
from fastapi.testclient import TestClient
from yt_dlp.utils import DownloadCancelled

from app import downloads
from app.formats import list_formats, video_summary
from app.main import app, manager
from app.video_downloader import format_selector


def test_format_selector():
    assert format_selector("mp3", "137", None) == "bestaudio/best"
    assert format_selector("mp4", "137", None) == "137[acodec=none]+bestaudio/137"  # video-only gets audio
    assert format_selector("mp4", None, "720") == "bestvideo[height<=720]+bestaudio/best[height<=720]"
    assert format_selector("mp4", None, "best") == "bestvideo+bestaudio/best"


def test_list_formats_dedupes_skips_junk_and_estimates_size():
    info = {"duration": 100, "formats": [
        {"format_id": "sb0", "ext": "mhtml", "format_note": None, "vcodec": "none", "acodec": "none"},
        {"format_id": "a", "width": 1920, "height": 1080, "vcodec": "avc1", "acodec": "none", "tbr": 8000, "format_note": None},
        {"format_id": "b", "width": 1920, "height": 1080, "vcodec": "vp9", "acodec": "none", "filesize": 5_000_000, "format_note": "1080p"},
        {"format_id": "c", "vcodec": "none", "acodec": "opus", "filesize_approx": 1_048_576},
    ]}
    out = {f["resolution"]: f for f in list_formats(info)}
    assert set(out) == {"1920x1080", "Audio Only"}
    assert out["1920x1080"]["format_id"] == "a"  # 8000kbps*100s = 100MB beats 5MB
    assert out["Audio Only"]["filesize"] == "1.00 MB"
    row = video_summary({"id": "abc", "title": "T", "url": "https://y/watch?v=abc", "duration": 5})
    assert row["thumbnail"].endswith("/abc/mqdefault.jpg") and row["url"].endswith("abc")


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:  # runs lifespan: starts the worker pool
        yield c


def wait_for(client, task_id, *states, timeout=5):
    end = time.time() + timeout
    while time.time() < end:
        t = client.get(f"/task/{task_id}").json()
        if t["status"] in states:
            return t
        time.sleep(0.05)
    raise AssertionError(f"{task_id} never reached {states}: {t}")


def test_input_validation(client):
    assert client.post("/download", data={"url": "file:///etc/passwd"}).status_code == 422
    assert client.post("/download", data={"url": "https://youtu.be/x", "format": "avi"}).status_code == 422
    assert client.post("/download", data={"url": "https://youtu.be/x", "format_id": "a;b"}).status_code == 422
    assert client.post("/fetch_details", data={"url": "not a url"}).status_code == 422


def test_download_lifecycle_and_cookie_wipe(client, monkeypatch):
    def fake(url, selector, directory, fmt, on_progress, cancel, cookies):
        on_progress(50)
        return "x.mp4", "Title", 720

    monkeypatch.setattr(downloads, "download_video", fake)
    r = client.post("/download", data={"url": "https://youtu.be/x", "cookies": "secret", "desired_height": "1080"}).json()
    assert r["message"] == "Download started"
    task = wait_for(client, r["task_id"], "completed")
    assert task["video_title"] == "Title" and task["progress"] == 100
    assert (task["height"], task["actual_height"]) == ("1080", 720)
    assert manager.tasks[r["task_id"]].cookies is None
    assert client.get("/history").json()["history"][0]["id"] == r["task_id"]


def test_cancel_running_and_queued(client, monkeypatch):
    def slow(url, selector, directory, fmt, on_progress, cancel, cookies):
        if cancel.wait(10):
            raise DownloadCancelled("cancelled")
        return "x.mp4", "Title", None

    monkeypatch.setattr(downloads, "download_video", slow)
    n = manager.workers
    ids = [client.post("/download", data={"url": f"https://youtu.be/{i}"}).json() for i in range(n + 1)]
    assert [i["queue_position"] for i in ids] == [0] * n + [1]  # all workers busy, last one waits
    assert len({i["task_id"] for i in ids}) == n + 1

    client.delete(f"/task/{ids[-1]['task_id']}")  # queued -> cancelled immediately
    assert client.get(f"/task/{ids[-1]['task_id']}").json()["status"] == "cancelled"
    for i in ids[:-1]:  # running -> cancelled via the progress hook
        wait_for(client, i["task_id"], "downloading")
        client.delete(f"/task/{i['task_id']}")
        wait_for(client, i["task_id"], "cancelled")
