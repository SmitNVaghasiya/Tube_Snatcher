import os
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from cryptography.fernet import Fernet
import pytest
from httpx import AsyncClient, ASGITransport

# Must be set before any app imports — utils.py reads COOKIE_ENCRYPTION_KEY at import
# time to construct the module-level Fernet cipher.
_TEST_FERNET_KEY = Fernet.generate_key().decode()
os.environ.setdefault("COOKIE_ENCRYPTION_KEY", _TEST_FERNET_KEY)
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-chars!!")
os.environ.setdefault("DOWNLOAD_DIR", "/tmp/ts_test_downloads")

from app import app  # noqa: E402

# Never connect to a real MongoDB in tests (httpx's ASGITransport skips lifespan anyway; this is a guard).
@asynccontextmanager
async def _no_lifespan(_app):
    yield


app.router.lifespan_context = _no_lifespan


@pytest.fixture(scope="session")
def fernet_key() -> str:
    return _TEST_FERNET_KEY


@pytest.fixture
def mock_db_manager():
    db = MagicMock()
    db.log_download = AsyncMock()
    db.get_recent_downloads = AsyncMock(return_value=[])
    return db


@pytest.fixture
async def async_client(mock_db_manager):
    with patch("api.routes.db_manager", mock_db_manager):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


@pytest.fixture
def valid_auth_token() -> str:
    from core.auth import create_access_token
    from datetime import timedelta

    return create_access_token({"sub": "127.0.0.1"}, timedelta(hours=1))


@pytest.fixture
def expired_auth_token() -> str:
    from core.auth import create_access_token
    from datetime import timedelta

    return create_access_token({"sub": "127.0.0.1"}, timedelta(seconds=-1))


@pytest.fixture
def sample_ydl_info() -> dict:
    return {
        "title": "Test Video",
        "thumbnail": "https://i.ytimg.com/vi/testid/maxresdefault.jpg",
        "duration": 300,
        "uploader": "Test Channel",
        "upload_date": "20240101",
        "view_count": 100000,
        "formats": [
            {
                "format_id": "137",
                "ext": "mp4",
                "width": 1920,
                "height": 1080,
                "filesize": 52428800,
                "vcodec": "avc1",
                "acodec": "none",
                "format_note": "1080p",
                "tbr": 4000,
                "fps": 30,
            },
            {
                "format_id": "248",
                "ext": "webm",
                "width": 1280,
                "height": 720,
                "filesize": 30000000,
                "vcodec": "vp9",
                "acodec": "none",
                "format_note": "720p",
                "tbr": 2500,
                "fps": 30,
            },
            {
                "format_id": "140",
                "ext": "m4a",
                "width": None,
                "height": None,
                "filesize": 4194304,
                "vcodec": "none",
                "acodec": "mp4a",
                "format_note": "audio only",
                "tbr": 128,
                "fps": None,
            },
            {
                "format_id": "sb0",
                "ext": "mhtml",
                "width": 48,
                "height": 27,
                "filesize": None,
                "vcodec": "none",
                "acodec": "none",
                "format_note": "storyboard",
                "tbr": None,
                "fps": None,
            },
        ],
        "thumbnails": [
            {"url": "https://i.ytimg.com/vi/testid/default.jpg"},
            {"url": "https://i.ytimg.com/vi/testid/hqdefault.jpg"},
            {"url": "https://i.ytimg.com/vi/testid/maxresdefault.jpg"},
        ],
    }
