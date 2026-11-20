import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from httpx import ASGITransport, AsyncClient

from app import cors_origin_regex

PINNED = "abcdefghijklmnopabcdefghijklmnop"
OTHER = "zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"


async def _allow_origin(ids, origin):
    app = FastAPI()
    app.add_middleware(CORSMiddleware, allow_origin_regex=cors_origin_regex(ids), allow_credentials=True,
                       allow_methods=["*"], allow_headers=["*"])

    @app.get("/")
    async def root():
        return {}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        return (await c.get("/", headers={"Origin": origin})).headers.get("access-control-allow-origin")


async def test_pinned_extension_id_is_allowed():
    assert await _allow_origin([PINNED], f"chrome-extension://{PINNED}") == f"chrome-extension://{PINNED}"


async def test_other_extension_id_is_rejected_when_pinned():
    assert await _allow_origin([PINNED], f"chrome-extension://{OTHER}") is None


async def test_localhost_still_allowed_when_pinned():
    assert await _allow_origin([PINNED], "http://localhost:3000") == "http://localhost:3000"


async def test_any_extension_allowed_when_not_pinned():
    assert await _allow_origin([], f"chrome-extension://{OTHER}") == f"chrome-extension://{OTHER}"
