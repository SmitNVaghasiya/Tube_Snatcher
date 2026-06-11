from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.models import DownloadTask, DownloadRequest, TaskStatus, VideoInfo, FormatInfo
from core.video_downloader import DownloadResult


# ---------------------------------------------------------------------------
# POST /api/v1/download
# ---------------------------------------------------------------------------


async def test_queue_download_returns_200(async_client):
    response = await async_client.post(
        "/api/v1/download",
        data={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "format_id": "137"},
    )
    assert response.status_code == 200


async def test_queue_download_response_has_task_id(async_client):
    response = await async_client.post(
        "/api/v1/download",
        data={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "format_id": "137"},
    )
    data = response.json()
    assert "task_id" in data
    assert data["task_id"] == "task_12345"


async def test_queue_download_response_success_is_true(async_client):
    response = await async_client.post(
        "/api/v1/download",
        data={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "format_id": "137"},
    )
    assert response.json()["success"] is True


async def test_queue_download_rejects_empty_url(async_client):
    # Empty form fields may be rejected by FastAPI (422) or the route handler (400)
    response = await async_client.post(
        "/api/v1/download",
        data={"url": "   ", "format_id": "137"},
    )
    assert response.status_code in (400, 422)


async def test_queue_download_rejects_missing_format_id(async_client):
    response = await async_client.post(
        "/api/v1/download",
        data={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "format_id": "   "},
    )
    assert response.status_code in (400, 422)


# ---------------------------------------------------------------------------
# GET /api/v1/task/{task_id}
# ---------------------------------------------------------------------------


async def test_get_task_status_returns_404_for_unknown_id(async_client):
    response = await async_client.get("/api/v1/task/nonexistent_task_id")
    assert response.status_code == 404


async def test_get_task_status_returns_200_for_known_task(async_client, mock_download_manager):
    req = DownloadRequest(
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ", format_id="137"
    )
    task = DownloadTask(req)
    mock_download_manager.get_task_by_id = MagicMock(return_value=task)

    response = await async_client.get(f"/api/v1/task/{task.id}")
    assert response.status_code == 200


async def test_get_task_status_response_has_expected_fields(async_client, mock_download_manager):
    req = DownloadRequest(
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ", format_id="137"
    )
    task = DownloadTask(req)
    mock_download_manager.get_task_by_id = MagicMock(return_value=task)

    response = await async_client.get(f"/api/v1/task/{task.id}")
    data = response.json()
    for key in ("task_id", "status", "progress"):
        assert key in data, f"Missing key: {key}"


# ---------------------------------------------------------------------------
# DELETE /api/v1/task/{task_id}
# ---------------------------------------------------------------------------


async def test_cancel_task_returns_200_on_success(async_client, mock_download_manager):
    mock_download_manager.cancel_task = AsyncMock(return_value=True)
    response = await async_client.delete("/api/v1/task/task_12345")
    assert response.status_code == 200


async def test_cancel_task_returns_404_when_not_found(async_client, mock_download_manager):
    mock_download_manager.cancel_task = AsyncMock(return_value=False)
    response = await async_client.delete("/api/v1/task/task_missing")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/v1/fetch-details
# ---------------------------------------------------------------------------


async def test_fetch_details_returns_200_with_valid_url(async_client):
    mock_video_info = VideoInfo(
        title="Test Video",
        thumbnail="http://img",
        duration=300,
        formats=[],
    )
    with patch("api.routes.VideoFetcher") as MockFetcher:
        MockFetcher.return_value.fetch_video_info = AsyncMock(return_value=mock_video_info)
        response = await async_client.post(
            "/api/v1/fetch-details",
            data={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        )
    assert response.status_code == 200


async def test_fetch_details_response_contains_title(async_client):
    mock_video_info = VideoInfo(title="My Test Video", thumbnail="", duration=120, formats=[])
    with patch("api.routes.VideoFetcher") as MockFetcher:
        MockFetcher.return_value.fetch_video_info = AsyncMock(return_value=mock_video_info)
        response = await async_client.post(
            "/api/v1/fetch-details",
            data={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        )
    assert response.json()["title"] == "My Test Video"


async def test_fetch_details_returns_404_when_fetcher_returns_none(async_client):
    with patch("api.routes.VideoFetcher") as MockFetcher:
        MockFetcher.return_value.fetch_video_info = AsyncMock(return_value=None)
        response = await async_client.post(
            "/api/v1/fetch-details",
            data={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        )
    assert response.status_code == 404


async def test_fetch_details_returns_400_for_empty_url(async_client):
    # Whitespace-only URL triggers the route's manual check (400)
    response = await async_client.post("/api/v1/fetch-details", data={"url": "   "})
    assert response.status_code in (400, 422)


# ---------------------------------------------------------------------------
# POST /api/v1/download-with-cookies
# ---------------------------------------------------------------------------


async def test_download_with_cookies_rejects_non_youtube_url(async_client):
    response = await async_client.post(
        "/api/v1/download-with-cookies",
        json={
            "url": "https://vimeo.com/123456",
            "cookies": "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tFALSE\t0\tSID\tv",
            "format_id": "137",
            "format_type": "mp4",
        },
    )
    assert response.status_code == 400
    assert "Invalid YouTube URL" in response.json()["detail"]


async def test_download_with_cookies_rejects_empty_cookies(async_client):
    response = await async_client.post(
        "/api/v1/download-with-cookies",
        json={
            "url": "https://www.youtube.com/watch?v=abc",
            "cookies": "   ",
            "format_id": "137",
            "format_type": "mp4",
        },
    )
    assert response.status_code in (400, 422)


async def test_download_with_cookies_success_path_calls_db_log(async_client, mock_db_manager):
    success_result = DownloadResult(
        success=True,
        filename="/tmp/video.mp4",
        video_title="Test",
        thumbnail="",
        file_size=1024,
        error=None,
    )
    with patch("api.routes.VideoDownloader") as MockDownloader:
        MockDownloader.return_value.download_video = AsyncMock(return_value=success_result)
        response = await async_client.post(
            "/api/v1/download-with-cookies",
            json={
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "cookies": ".youtube.com\tTRUE\t/\tFALSE\t0\tSID\tvalue",
                "format_id": "137",
                "format_type": "mp4",
            },
        )
    assert response.status_code == 200
    mock_db_manager.log_download.assert_called_once()


async def test_download_with_cookies_failure_path_still_logs_to_db(async_client, mock_db_manager):
    failure_result = DownloadResult(
        success=False,
        filename=None,
        video_title=None,
        thumbnail=None,
        file_size=None,
        error="download failed",
    )
    with patch("api.routes.VideoDownloader") as MockDownloader:
        MockDownloader.return_value.download_video = AsyncMock(return_value=failure_result)
        response = await async_client.post(
            "/api/v1/download-with-cookies",
            json={
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "cookies": ".youtube.com\tTRUE\t/\tFALSE\t0\tSID\tvalue",
                "format_id": "137",
                "format_type": "mp4",
            },
        )
    assert response.status_code == 400
    mock_db_manager.log_download.assert_called_once()
    call_kwargs = mock_db_manager.log_download.call_args[0][0]
    assert call_kwargs["success"] is False
