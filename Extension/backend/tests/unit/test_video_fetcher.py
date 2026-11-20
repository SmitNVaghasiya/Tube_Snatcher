import pytest

from core.config import settings
from core.video_fetcher import VideoFetcher


@pytest.fixture
def fetcher():
    return VideoFetcher()


# ---------------------------------------------------------------------------
# _get_format_selector
# ---------------------------------------------------------------------------


def test_get_format_selector_mp3_returns_audio_preference(fetcher):
    assert fetcher._get_format_selector("mp3") == settings.AUDIO_FORMAT_PREFERENCE


def test_get_format_selector_mp4_returns_video_preference(fetcher):
    assert fetcher._get_format_selector("mp4") == settings.VIDEO_FORMAT_PREFERENCE


def test_get_format_selector_webm_returns_video_preference(fetcher):
    assert fetcher._get_format_selector("webm") == settings.VIDEO_FORMAT_PREFERENCE
