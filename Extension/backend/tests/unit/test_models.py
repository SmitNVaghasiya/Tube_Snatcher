import time
from datetime import datetime

import pytest
from pydantic import ValidationError

from core.models import (
    DownloadRequest,
    DownloadTask,
    FormatInfo,
    QueueStatus,
    TaskStatus,
    VideoInfo,
)


# ---------------------------------------------------------------------------
# TaskStatus enum
# ---------------------------------------------------------------------------


def test_task_status_queued_value():
    assert TaskStatus.QUEUED == "queued"


def test_task_status_all_members_present():
    values = {s.value for s in TaskStatus}
    assert values == {"queued", "downloading", "completed", "failed", "cancelled"}


def test_task_status_is_string_enum():
    assert isinstance(TaskStatus.COMPLETED, str)


# ---------------------------------------------------------------------------
# DownloadRequest
# ---------------------------------------------------------------------------


def test_download_request_valid():
    req = DownloadRequest(
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        format_id="137",
        format_type="mp4",
    )
    assert req.url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert req.format_type == "mp4"


def test_download_request_strips_url_whitespace():
    req = DownloadRequest(url="  https://youtube.com/watch?v=abc  ", format_id="137")
    assert req.url == "https://youtube.com/watch?v=abc"


def test_download_request_rejects_whitespace_only_url():
    with pytest.raises(ValidationError):
        DownloadRequest(url="   ", format_id="137")


def test_download_request_rejects_invalid_format_type():
    with pytest.raises(ValidationError):
        DownloadRequest(
            url="https://youtube.com/watch?v=abc",
            format_id="137",
            format_type="avi",
        )


def test_download_request_normalises_format_type_to_lowercase():
    req = DownloadRequest(
        url="https://youtube.com/watch?v=abc", format_id="137", format_type="MP4"
    )
    assert req.format_type == "mp4"


def test_download_request_default_format_type_is_mp4():
    req = DownloadRequest(url="https://youtube.com/watch?v=abc", format_id="137")
    assert req.format_type == "mp4"


def test_download_request_accepts_mp3_format():
    req = DownloadRequest(
        url="https://youtube.com/watch?v=abc", format_id="140", format_type="mp3"
    )
    assert req.format_type == "mp3"


def test_download_request_accepts_webm_format():
    req = DownloadRequest(
        url="https://youtube.com/watch?v=abc", format_id="248", format_type="webm"
    )
    assert req.format_type == "webm"


# ---------------------------------------------------------------------------
# DownloadTask
# ---------------------------------------------------------------------------


def _make_task(url="https://youtube.com/watch?v=abc", format_id="137"):
    req = DownloadRequest(url=url, format_id=format_id)
    return DownloadTask(req)


def test_download_task_initial_status_is_queued():
    task = _make_task()
    assert task.status == TaskStatus.QUEUED


def test_download_task_id_has_task_prefix():
    task = _make_task()
    assert task.id.startswith("task_")


def test_download_task_creates_unique_ids():
    task1 = _make_task()
    time.sleep(0.002)
    task2 = _make_task()
    assert task1.id != task2.id


def test_download_task_initial_progress_is_zero():
    task = _make_task()
    assert task.progress == 0


def test_download_task_stores_url():
    task = _make_task(url="https://youtube.com/watch?v=xyz")
    assert task.url == "https://youtube.com/watch?v=xyz"


def test_download_task_to_dict_contains_required_keys():
    task = _make_task()
    d = task.to_dict()
    for key in ("id", "url", "format_id", "format_type", "status", "progress", "created_at"):
        assert key in d, f"Missing key in to_dict(): {key}"


def test_download_task_to_dict_serialises_created_at_as_iso_string():
    task = _make_task()
    d = task.to_dict()
    parsed = datetime.fromisoformat(d["created_at"])
    assert isinstance(parsed, datetime)


def test_download_task_to_dict_status_is_string_value():
    task = _make_task()
    d = task.to_dict()
    assert d["status"] == "queued"


def test_download_task_to_dict_start_time_is_none_initially():
    task = _make_task()
    assert task.to_dict()["start_time"] is None


# ---------------------------------------------------------------------------
# VideoInfo
# ---------------------------------------------------------------------------


def test_video_info_defaults():
    info = VideoInfo(title="Test Video")
    assert info.type == "video"
    assert info.thumbnail == ""
    assert info.duration == 0
    assert info.formats == []
