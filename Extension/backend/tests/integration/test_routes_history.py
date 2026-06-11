from unittest.mock import AsyncMock

import pytest

from core.models import DownloadRequest, DownloadTask, TaskStatus


# ---------------------------------------------------------------------------
# GET /api/v1/history
# ---------------------------------------------------------------------------


async def test_history_endpoint_returns_200(async_client):
    response = await async_client.get("/api/v1/history")
    assert response.status_code == 200


async def test_history_endpoint_has_history_key(async_client):
    response = await async_client.get("/api/v1/history")
    data = response.json()
    assert "history" in data
    assert isinstance(data["history"], list)


async def test_history_endpoint_passes_limit_param(async_client, mock_download_manager):
    await async_client.get("/api/v1/history?limit=5")
    mock_download_manager.get_download_history.assert_called_once_with(5)


async def test_history_endpoint_default_limit_is_50(async_client, mock_download_manager):
    await async_client.get("/api/v1/history")
    mock_download_manager.get_download_history.assert_called_once_with(50)


async def test_history_returns_items_from_manager(async_client, mock_download_manager):
    req = DownloadRequest(url="https://youtube.com/watch?v=abc", format_id="137")
    task = DownloadTask(req)
    task.status = TaskStatus.COMPLETED
    mock_download_manager.get_download_history = AsyncMock(return_value=[task.to_dict()])

    response = await async_client.get("/api/v1/history")
    data = response.json()
    assert len(data["history"]) == 1
    assert data["history"][0]["url"] == "https://youtube.com/watch?v=abc"


# ---------------------------------------------------------------------------
# POST /api/v1/clear-queue
# ---------------------------------------------------------------------------


async def test_clear_queue_returns_200(async_client):
    response = await async_client.post("/api/v1/clear-queue")
    assert response.status_code == 200


async def test_clear_queue_response_has_cleared_count(async_client, mock_download_manager):
    mock_download_manager.clear_queue = AsyncMock(return_value=3)
    response = await async_client.post("/api/v1/clear-queue")
    data = response.json()
    assert "cleared_count" in data
    assert data["cleared_count"] == 3


# ---------------------------------------------------------------------------
# GET /api/v1/analytics
# ---------------------------------------------------------------------------


async def test_analytics_returns_200(async_client):
    response = await async_client.get("/api/v1/analytics")
    assert response.status_code == 200


async def test_analytics_returns_expected_fields(async_client):
    response = await async_client.get("/api/v1/analytics")
    data = response.json()
    assert "total_downloads" in data
    assert data["total_downloads"] == 42


# ---------------------------------------------------------------------------
# GET /api/v1/download-locations
# ---------------------------------------------------------------------------


async def test_download_locations_returns_200(async_client):
    response = await async_client.get("/api/v1/download-locations")
    assert response.status_code == 200


async def test_download_locations_has_locations_list(async_client):
    response = await async_client.get("/api/v1/download-locations")
    data = response.json()
    assert "locations" in data
    assert isinstance(data["locations"], list)


async def test_download_locations_entries_have_required_keys(async_client):
    response = await async_client.get("/api/v1/download-locations")
    for location in response.json()["locations"]:
        assert "name" in location
        assert "path" in location
        assert "is_default" in location


async def test_download_locations_contains_default_entry(async_client):
    response = await async_client.get("/api/v1/download-locations")
    locations = response.json()["locations"]
    defaults = [loc for loc in locations if loc["is_default"] is True]
    assert len(defaults) >= 1
