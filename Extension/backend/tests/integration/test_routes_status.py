import pytest


async def test_health_endpoint_returns_200(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200


async def test_health_endpoint_status_is_healthy(async_client):
    response = await async_client.get("/health")
    assert response.json()["status"] == "healthy"


async def test_root_endpoint_returns_200(async_client):
    response = await async_client.get("/")
    assert response.status_code == 200


async def test_root_endpoint_has_service_and_version(async_client):
    response = await async_client.get("/")
    data = response.json()
    assert "service" in data
    assert "version" in data


async def test_status_endpoint_returns_200(async_client):
    response = await async_client.get("/api/v1/status")
    assert response.status_code == 200


async def test_status_endpoint_has_expected_fields(async_client):
    response = await async_client.get("/api/v1/status")
    data = response.json()
    assert "status" in data
    assert "queue_size" in data
    assert "active_downloads" in data


async def test_status_endpoint_status_value_is_running(async_client):
    response = await async_client.get("/api/v1/status")
    assert response.json()["status"] == "running"


async def test_queue_endpoint_returns_200(async_client):
    response = await async_client.get("/api/v1/queue")
    assert response.status_code == 200


async def test_queue_endpoint_has_expected_fields(async_client):
    response = await async_client.get("/api/v1/queue")
    data = response.json()
    assert "total_queue_size" in data
    assert "active_downloads" in data
    assert "queued_downloads" in data
    assert "active_tasks" in data
