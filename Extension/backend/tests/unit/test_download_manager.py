import pytest
from unittest.mock import AsyncMock, MagicMock

from core.download_manager import DownloadManager
from core.models import DownloadRequest, DownloadTask, TaskStatus
from core.video_downloader import DownloadResult


def _make_request(
    url="https://youtube.com/watch?v=test123",
    format_id="137",
    format_type="mp4",
):
    return DownloadRequest(url=url, format_id=format_id, format_type=format_type)


@pytest.fixture
def manager(mocker):
    m = DownloadManager()
    # Disable the shutdown timer so tests don't spawn long-lived asyncio tasks.
    mocker.patch.object(m, "_start_shutdown_timer")
    # Stub the downloader to prevent real yt-dlp invocations.
    m.downloader = MagicMock()
    return m


@pytest.fixture
def success_result():
    return DownloadResult(
        success=True,
        filename="/tmp/test_video.mp4",
        video_title="Test Video",
        thumbnail="http://img/thumb.jpg",
        file_size=1024,
        error=None,
    )


@pytest.fixture
def failure_result():
    return DownloadResult(
        success=False,
        filename=None,
        video_title=None,
        thumbnail=None,
        file_size=None,
        error="network error",
    )


# ---------------------------------------------------------------------------
# add_to_queue
# ---------------------------------------------------------------------------


async def test_add_to_queue_returns_task_id_string(manager, mocker):
    mocker.patch("asyncio.create_task")
    task_id = await manager.add_to_queue(_make_request())
    assert isinstance(task_id, str)
    assert task_id.startswith("task_")


async def test_add_to_queue_increments_queue_length(manager, mocker):
    mocker.patch("asyncio.create_task")
    await manager.add_to_queue(_make_request())
    assert len(manager.download_queue) == 1


async def test_add_to_queue_multiple_tasks(manager, mocker):
    mocker.patch("asyncio.create_task")
    await manager.add_to_queue(_make_request())
    await manager.add_to_queue(_make_request(url="https://youtube.com/watch?v=second"))
    assert len(manager.download_queue) == 2


# ---------------------------------------------------------------------------
# get_task_by_id
# ---------------------------------------------------------------------------


async def test_get_task_by_id_found(manager, mocker):
    mocker.patch("asyncio.create_task")
    task_id = await manager.add_to_queue(_make_request())
    task = manager.get_task_by_id(task_id)
    assert task is not None
    assert task.id == task_id


def test_get_task_by_id_returns_none_for_unknown_id(manager):
    assert manager.get_task_by_id("nonexistent_id") is None


def test_get_task_by_id_searches_active_and_completed(manager):
    import time as _time

    queued = DownloadTask(_make_request())
    manager.download_queue.append(queued)
    _time.sleep(0.002)

    active = DownloadTask(_make_request(url="https://youtube.com/watch?v=active"))
    active.status = TaskStatus.DOWNLOADING
    manager.active_downloads.append(active)
    _time.sleep(0.002)

    completed = DownloadTask(_make_request(url="https://youtube.com/watch?v=done"))
    completed.status = TaskStatus.COMPLETED
    manager.completed_tasks.append(completed)

    assert manager.get_task_by_id(queued.id) is queued
    assert manager.get_task_by_id(active.id) is active
    assert manager.get_task_by_id(completed.id) is completed


# ---------------------------------------------------------------------------
# cancel_task
# ---------------------------------------------------------------------------


async def test_cancel_queued_task_returns_true(manager, mocker):
    mocker.patch("asyncio.create_task")
    task_id = await manager.add_to_queue(_make_request())
    result = await manager.cancel_task(task_id)
    assert result is True


async def test_cancel_queued_task_removes_from_queue(manager, mocker):
    mocker.patch("asyncio.create_task")
    task_id = await manager.add_to_queue(_make_request())
    await manager.cancel_task(task_id)
    assert len(manager.download_queue) == 0


async def test_cancel_queued_task_sets_cancelled_status(manager, mocker):
    mocker.patch("asyncio.create_task")
    task_id = await manager.add_to_queue(_make_request())
    await manager.cancel_task(task_id)
    task = manager.get_task_by_id(task_id)
    assert task.status == TaskStatus.CANCELLED


async def test_cancel_task_returns_false_for_unknown_id(manager):
    result = await manager.cancel_task("nonexistent_id")
    assert result is False


async def test_cancel_active_task_marks_cancelled_without_removing(manager):
    req = _make_request()
    task = DownloadTask(req)
    task.status = TaskStatus.DOWNLOADING
    manager.active_downloads.append(task)

    result = await manager.cancel_task(task.id)
    assert result is True
    assert task.status == TaskStatus.CANCELLED
    assert task in manager.active_downloads


# ---------------------------------------------------------------------------
# clear_queue
# ---------------------------------------------------------------------------


async def test_clear_queue_empties_download_queue(manager, mocker):
    mocker.patch("asyncio.create_task")
    await manager.add_to_queue(_make_request())
    await manager.add_to_queue(_make_request(url="https://youtube.com/watch?v=b"))
    await manager.clear_queue()
    assert len(manager.download_queue) == 0


async def test_clear_queue_returns_count_of_cleared_tasks(manager, mocker):
    mocker.patch("asyncio.create_task")
    await manager.add_to_queue(_make_request())
    await manager.add_to_queue(_make_request(url="https://youtube.com/watch?v=b"))
    count = await manager.clear_queue()
    assert count == 2


async def test_clear_queue_moves_tasks_to_completed_as_cancelled(manager, mocker):
    mocker.patch("asyncio.create_task")
    await manager.add_to_queue(_make_request())
    await manager.clear_queue()
    assert all(t.status == TaskStatus.CANCELLED for t in manager.completed_tasks)


async def test_clear_empty_queue_returns_zero(manager):
    count = await manager.clear_queue()
    assert count == 0


# ---------------------------------------------------------------------------
# get_queue_status
# ---------------------------------------------------------------------------


async def test_get_queue_status_reflects_queued_and_active_counts(manager, mocker):
    mocker.patch("asyncio.create_task")
    await manager.add_to_queue(_make_request())

    active = DownloadTask(_make_request(url="https://youtube.com/watch?v=active"))
    active.status = TaskStatus.DOWNLOADING
    manager.active_downloads.append(active)

    status = await manager.get_queue_status()
    assert status.total_queue_size == 2
    assert status.active_downloads == 1


async def test_get_queue_status_empty_manager(manager):
    status = await manager.get_queue_status()
    assert status.total_queue_size == 0
    assert status.active_downloads == 0


# ---------------------------------------------------------------------------
# get_download_history
# ---------------------------------------------------------------------------


async def test_get_download_history_respects_limit(manager):
    for _ in range(60):
        task = DownloadTask(_make_request())
        task.status = TaskStatus.COMPLETED
        manager.completed_tasks.append(task)

    history = await manager.get_download_history(limit=10)
    assert len(history) <= 10


async def test_get_download_history_returns_dicts(manager):
    task = DownloadTask(_make_request())
    task.status = TaskStatus.COMPLETED
    manager.completed_tasks.append(task)

    history = await manager.get_download_history()
    assert isinstance(history[0], dict)


# ---------------------------------------------------------------------------
# _update_task_progress
# ---------------------------------------------------------------------------


def test_update_task_progress_normal_value(manager):
    task = DownloadTask(_make_request())
    manager._update_task_progress(task, 55.5)
    assert task.progress == 55.5


def test_update_task_progress_clamps_to_100(manager):
    task = DownloadTask(_make_request())
    manager._update_task_progress(task, 150.0)
    assert task.progress == 100


def test_update_task_progress_clamps_to_zero(manager):
    task = DownloadTask(_make_request())
    manager._update_task_progress(task, -10.0)
    assert task.progress == 0


# ---------------------------------------------------------------------------
# _download_task (success / failure / exception paths)
# ---------------------------------------------------------------------------


async def test_download_task_success_sets_completed_status(
    manager, mocker, success_result
):
    manager.downloader.download_video = AsyncMock(return_value=success_result)
    mocker.patch("core.config.settings.validate_download_directory", return_value=True)

    req = _make_request()
    task = DownloadTask(req)
    manager.active_downloads.append(task)

    await manager._download_task(task)

    assert task.status == TaskStatus.COMPLETED
    assert task.filename == "/tmp/test_video.mp4"
    assert task.video_title == "Test Video"


async def test_download_task_failure_sets_failed_status(
    manager, mocker, failure_result
):
    manager.downloader.download_video = AsyncMock(return_value=failure_result)
    mocker.patch("core.config.settings.validate_download_directory", return_value=True)

    req = _make_request()
    task = DownloadTask(req)
    manager.active_downloads.append(task)

    await manager._download_task(task)

    assert task.status == TaskStatus.FAILED
    assert "network error" in task.error


async def test_download_task_exception_sets_failed_status(manager, mocker):
    manager.downloader.download_video = AsyncMock(side_effect=Exception("ydl crashed"))
    mocker.patch("core.config.settings.validate_download_directory", return_value=True)

    req = _make_request()
    task = DownloadTask(req)
    manager.active_downloads.append(task)

    await manager._download_task(task)

    assert task.status == TaskStatus.FAILED
    assert "ydl crashed" in task.error


async def test_download_task_moves_to_completed_list_on_finish(
    manager, mocker, success_result
):
    manager.downloader.download_video = AsyncMock(return_value=success_result)
    mocker.patch("core.config.settings.validate_download_directory", return_value=True)

    req = _make_request()
    task = DownloadTask(req)
    manager.active_downloads.append(task)

    await manager._download_task(task)

    assert task not in manager.active_downloads
    assert task in manager.completed_tasks


async def test_download_task_invalid_directory_sets_failed(manager, mocker):
    mocker.patch("core.config.settings.validate_download_directory", return_value=False)

    req = _make_request()
    task = DownloadTask(req)
    manager.active_downloads.append(task)

    await manager._download_task(task)

    assert task.status == TaskStatus.FAILED
    assert task.error is not None
