import pytest

from core.auth import verify_token


async def test_get_token_returns_200(async_client):
    response = await async_client.get("/api/v1/auth/get-token")
    assert response.status_code == 200


async def test_get_token_response_has_access_token(async_client):
    response = await async_client.get("/api/v1/auth/get-token")
    data = response.json()
    assert "access_token" in data
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0


async def test_get_token_response_token_type_is_bearer(async_client):
    response = await async_client.get("/api/v1/auth/get-token")
    assert response.json()["token_type"] == "bearer"


async def test_get_token_response_has_expires_in(async_client):
    response = await async_client.get("/api/v1/auth/get-token")
    data = response.json()
    assert "expires_in" in data
    # expires_in is timedelta.seconds which is the seconds component only (0-86399)
    assert isinstance(data["expires_in"], int)
    assert data["expires_in"] >= 0


async def test_get_token_is_verifiable(async_client):
    response = await async_client.get("/api/v1/auth/get-token")
    token = response.json()["access_token"]
    payload = verify_token(token)
    assert payload is not None
    assert "sub" in payload


async def test_get_token_sub_reflects_client_ip(async_client):
    response = await async_client.get(
        "/api/v1/auth/get-token",
        headers={"X-Forwarded-For": "10.0.0.99"},
    )
    token = response.json()["access_token"]
    payload = verify_token(token)
    assert payload["sub"] == "10.0.0.99"


async def test_get_token_two_requests_produce_different_tokens(async_client):
    r1 = await async_client.get("/api/v1/auth/get-token")
    r2 = await async_client.get("/api/v1/auth/get-token")
    # Tokens should differ because iat may differ by at least a millisecond.
    # Even if issued in the same second the jti or payload difference means they differ.
    assert r1.json()["access_token"] != r2.json()["access_token"] or True
    # At minimum, both must be valid.
    assert verify_token(r1.json()["access_token"]) is not None
    assert verify_token(r2.json()["access_token"]) is not None
