async def test_status_endpoint_has_expected_fields(async_client):
    response = await async_client.get("/api/v1/status")
    data = response.json()
    assert data["status"] == "running"
    assert "timestamp" in data


async def test_removed_queue_and_task_routes_are_gone(async_client):
    assert (await async_client.get("/api/v1/queue")).status_code == 404
    assert (await async_client.get("/api/v1/task/x")).status_code == 404
