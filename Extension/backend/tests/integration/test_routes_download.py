from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.video_downloader import DownloadResult


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


# ---------------------------------------------------------------------------
# POST /api/v1/fetch-details-with-cookies
# ---------------------------------------------------------------------------

_COOKIES = ".youtube.com	TRUE	/	FALSE	0	NAME	value"


async def test_fetch_details_with_cookies_returns_fetcher_result(async_client):
    payload = {"type": "video", "title": "T", "formats": []}
    with patch("api.routes.VideoFetcher") as MockFetcher:
        MockFetcher.return_value.fetch_details = AsyncMock(return_value=payload)
        response = await async_client.post(
            "/api/v1/fetch-details-with-cookies",
            json={"url": "https://youtube.com/watch?v=abc", "format_id": "best", "cookies": _COOKIES},
        )
    assert response.status_code == 200
    assert response.json() == payload


async def test_fetch_details_with_cookies_returns_500_when_fetcher_raises(async_client):
    with patch("api.routes.VideoFetcher") as MockFetcher:
        MockFetcher.return_value.fetch_details = AsyncMock(side_effect=RuntimeError("boom"))
        response = await async_client.post(
            "/api/v1/fetch-details-with-cookies",
            json={"url": "https://youtube.com/watch?v=abc", "format_id": "best", "cookies": _COOKIES},
        )
    assert response.status_code == 500


# ---------------------------------------------------------------------------
# download_location validation
# ---------------------------------------------------------------------------

_BODY = {
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "cookies": ".youtube.com\tTRUE\t/\tFALSE\t0\tSID\tvalue",
    "format_id": "137",
}


async def test_download_with_cookies_rejects_arbitrary_download_location(async_client, mock_db_manager):
    with patch("api.routes.VideoDownloader") as MockDownloader:
        response = await async_client.post(
            "/api/v1/download-with-cookies", json={**_BODY, "download_location": "C:/Windows/System32"}
        )
    assert response.status_code == 400
    MockDownloader.return_value.download_video.assert_not_called()


async def test_download_playlist_rejects_arbitrary_download_location(async_client):
    response = await async_client.post(
        "/api/v1/download-playlist",
        data={
            "playlist_url": "https://www.youtube.com/playlist?list=PL1",
            "cookies": "x",
            "download_location": "/etc",
        },
    )
    assert response.status_code == 400


async def test_download_with_cookies_resolves_listed_location_server_side(async_client):
    listed = (await async_client.get("/api/v1/download-locations")).json()["locations"][0]
    ok = DownloadResult(success=True, filename="f", video_title="T", thumbnail=None, file_size=None, error=None)
    with patch("api.routes.VideoDownloader") as MockDownloader:
        MockDownloader.return_value.download_video = AsyncMock(return_value=ok)
        response = await async_client.post(
            "/api/v1/download-with-cookies", json={**_BODY, "download_location": listed["name"]}
        )
    assert response.status_code == 200
    assert str(MockDownloader.return_value.download_video.call_args.kwargs["directory"]) == listed["path"]
