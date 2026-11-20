from unittest.mock import AsyncMock

import pytest


# ---------------------------------------------------------------------------
# GET /api/v1/history
# ---------------------------------------------------------------------------


async def test_history_endpoint_has_history_key(async_client):
    response = await async_client.get("/api/v1/history")
    assert response.status_code == 200
    data = response.json()
    assert data["history"] == []
    assert data["total_count"] == 0


async def test_history_endpoint_passes_limit_param(async_client, mock_db_manager):
    await async_client.get("/api/v1/history?limit=5")
    mock_db_manager.get_recent_downloads.assert_called_once_with(5)


async def test_history_endpoint_default_limit_is_50(async_client, mock_db_manager):
    await async_client.get("/api/v1/history")
    mock_db_manager.get_recent_downloads.assert_called_once_with(50)


async def test_history_returns_items_from_db(async_client, mock_db_manager):
    mock_db_manager.get_recent_downloads = AsyncMock(
        return_value=[{"id": "1", "url": "https://youtube.com/watch?v=abc", "status": "completed"}]
    )
    data = (await async_client.get("/api/v1/history")).json()
    assert len(data["history"]) == 1
    assert data["history"][0]["url"] == "https://youtube.com/watch?v=abc"


# ---------------------------------------------------------------------------
# GET /api/v1/download-locations
# ---------------------------------------------------------------------------


async def test_download_locations_has_default_entry(async_client):
    locations = (await async_client.get("/api/v1/download-locations")).json()["locations"]
    assert all({"name", "path", "is_default"} <= set(loc) for loc in locations)
    assert any(loc["is_default"] for loc in locations)
