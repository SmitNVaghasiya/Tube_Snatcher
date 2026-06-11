from unittest.mock import MagicMock

import pytest

from core.config import settings
from core.video_fetcher import VideoFetcher


@pytest.fixture
def fetcher():
    return VideoFetcher()


# ---------------------------------------------------------------------------
# _should_skip_format
# ---------------------------------------------------------------------------


def test_should_skip_format_rejects_storyboard_in_note(fetcher):
    assert fetcher._should_skip_format({"format_note": "storyboard", "format_id": "sb0"}) is True


def test_should_skip_format_rejects_storyboard_in_format_id(fetcher):
    assert fetcher._should_skip_format({"format_note": "", "format_id": "2-storyboard"}) is True


def test_should_skip_format_rejects_drm_in_format_id(fetcher):
    assert fetcher._should_skip_format({"format_note": "", "format_id": "drm-137"}) is True


def test_should_skip_format_rejects_thumbnail_note(fetcher):
    assert fetcher._should_skip_format({"format_note": "thumbnail", "format_id": "th0"}) is True


def test_should_skip_format_accepts_normal_video(fetcher):
    assert fetcher._should_skip_format({"format_note": "1080p", "format_id": "137"}) is False


def test_should_skip_format_accepts_audio_only(fetcher):
    assert fetcher._should_skip_format({"format_note": "audio only", "format_id": "140"}) is False


# ---------------------------------------------------------------------------
# _get_resolution_string
# ---------------------------------------------------------------------------


def test_get_resolution_string_width_and_height(fetcher):
    assert fetcher._get_resolution_string({"width": 1920, "height": 1080}) == "1920x1080"


def test_get_resolution_string_audio_only_when_no_video_codec(fetcher):
    result = fetcher._get_resolution_string({"vcodec": "none", "width": None, "height": None})
    assert result == "Audio Only"


def test_get_resolution_string_height_only_fallback(fetcher):
    assert fetcher._get_resolution_string({"width": None, "height": 720}) == "720p"


def test_get_resolution_string_unknown_when_no_useful_data(fetcher):
    assert fetcher._get_resolution_string({}) == "Unknown Quality"


# ---------------------------------------------------------------------------
# _calculate_filesize_string
# ---------------------------------------------------------------------------


def test_calculate_filesize_string_gb(fetcher):
    result = fetcher._calculate_filesize_string({"filesize": 2 * 1024 ** 3})
    assert "GB" in result


def test_calculate_filesize_string_mb(fetcher):
    result = fetcher._calculate_filesize_string({"filesize": 52_428_800})
    assert "MB" in result


def test_calculate_filesize_string_kb(fetcher):
    result = fetcher._calculate_filesize_string({"filesize": 2048})
    assert "KB" in result


def test_calculate_filesize_string_bytes(fetcher):
    result = fetcher._calculate_filesize_string({"filesize": 500})
    assert "B" in result


def test_calculate_filesize_string_unknown_when_no_data(fetcher):
    assert fetcher._calculate_filesize_string({}) == "Size Unknown"


def test_calculate_filesize_falls_back_to_filesize_approx(fetcher):
    result = fetcher._calculate_filesize_string({"filesize_approx": 10_485_760})
    assert "MB" in result


# ---------------------------------------------------------------------------
# _estimate_filesize
# ---------------------------------------------------------------------------


def test_estimate_filesize_from_bitrate_and_duration(fetcher):
    fmt = {"tbr": 4000, "duration": 60}
    # (4000 kbps * 60 s * 1000) / 8 = 30_000_000 bytes
    result = fetcher._estimate_filesize(fmt)
    assert abs(result - 30_000_000) < 1000


def test_estimate_filesize_from_resolution(fetcher):
    fmt = {"width": 1920, "height": 1080}
    expected = int(1920 * 1080 * settings.FILESIZE_ESTIMATION_FACTOR)
    assert fetcher._estimate_filesize(fmt) == expected


def test_estimate_filesize_returns_zero_on_empty_dict(fetcher):
    assert fetcher._estimate_filesize({}) == 0


# ---------------------------------------------------------------------------
# _get_best_thumbnail
# ---------------------------------------------------------------------------


def test_get_best_thumbnail_prefers_maxresdefault(fetcher):
    thumbnails = [
        {"url": "https://img.youtube.com/vi/abc/default.jpg"},
        {"url": "https://img.youtube.com/vi/abc/hqdefault.jpg"},
        {"url": "https://img.youtube.com/vi/abc/maxresdefault.jpg"},
    ]
    assert "maxresdefault" in fetcher._get_best_thumbnail(thumbnails)


def test_get_best_thumbnail_falls_back_to_hqdefault(fetcher):
    thumbnails = [
        {"url": "https://img.youtube.com/vi/abc/default.jpg"},
        {"url": "https://img.youtube.com/vi/abc/hqdefault.jpg"},
    ]
    assert "hqdefault" in fetcher._get_best_thumbnail(thumbnails)


def test_get_best_thumbnail_empty_list_returns_empty_string(fetcher):
    assert fetcher._get_best_thumbnail([]) == ""


def test_get_best_thumbnail_single_entry(fetcher):
    thumbnails = [{"url": "https://img.youtube.com/vi/abc/0.jpg"}]
    result = fetcher._get_best_thumbnail(thumbnails)
    assert result == "https://img.youtube.com/vi/abc/0.jpg"


# ---------------------------------------------------------------------------
# _get_format_selector
# ---------------------------------------------------------------------------


def test_get_format_selector_mp3_returns_audio_preference(fetcher):
    assert fetcher._get_format_selector("mp3") == settings.AUDIO_FORMAT_PREFERENCE


def test_get_format_selector_mp4_returns_video_preference(fetcher):
    assert fetcher._get_format_selector("mp4") == settings.VIDEO_FORMAT_PREFERENCE


def test_get_format_selector_webm_returns_video_preference(fetcher):
    assert fetcher._get_format_selector("webm") == settings.VIDEO_FORMAT_PREFERENCE


# ---------------------------------------------------------------------------
# _process_formats
# ---------------------------------------------------------------------------


def test_process_formats_removes_storyboards(fetcher):
    formats = [
        {"format_id": "sb0", "format_note": "storyboard", "ext": "mhtml",
         "width": 48, "height": 27},
        {"format_id": "137", "format_note": "1080p", "ext": "mp4",
         "width": 1920, "height": 1080, "filesize": 10_000_000, "tbr": 4000, "fps": 30},
    ]
    result = fetcher._process_formats(formats)
    assert len(result) == 1
    assert result[0].format_id == "137"


def test_process_formats_deduplicates_same_resolution(fetcher):
    formats = [
        {"format_id": "137", "format_note": "1080p", "ext": "mp4",
         "width": 1920, "height": 1080, "filesize": 50_000_000, "tbr": 4000, "fps": 30},
        {"format_id": "248", "format_note": "1080p", "ext": "webm",
         "width": 1920, "height": 1080, "filesize": 45_000_000, "tbr": 3500, "fps": 30},
    ]
    result = fetcher._process_formats(formats)
    assert len(result) == 1
    assert result[0].resolution == "1920x1080"


def test_process_formats_includes_audio_only_format(fetcher):
    formats = [
        {"format_id": "140", "format_note": "audio only", "ext": "m4a",
         "width": None, "height": None, "filesize": 4_000_000,
         "vcodec": "none", "tbr": 128, "fps": None},
    ]
    result = fetcher._process_formats(formats)
    assert len(result) == 1
    assert result[0].resolution == "Audio Only"


def test_process_formats_sorts_highest_resolution_first(fetcher):
    formats = [
        {"format_id": "136", "format_note": "720p", "ext": "mp4",
         "width": 1280, "height": 720, "filesize": 20_000_000, "tbr": 2500, "fps": 30},
        {"format_id": "137", "format_note": "1080p", "ext": "mp4",
         "width": 1920, "height": 1080, "filesize": 50_000_000, "tbr": 4000, "fps": 30},
    ]
    result = fetcher._process_formats(formats)
    assert result[0].resolution == "1920x1080"


def test_process_formats_returns_format_info_objects(fetcher):
    from core.models import FormatInfo

    formats = [
        {"format_id": "137", "format_note": "1080p", "ext": "mp4",
         "width": 1920, "height": 1080, "filesize": 10_000_000, "tbr": 4000, "fps": 30},
    ]
    result = fetcher._process_formats(formats)
    assert all(isinstance(f, FormatInfo) for f in result)


# ---------------------------------------------------------------------------
# fetch_video_info (async wrapper — mocked sync internals)
# ---------------------------------------------------------------------------


async def test_fetch_video_info_delegates_to_sync(mocker, fetcher):
    mock_sync = mocker.patch.object(fetcher, "_fetch_video_info_sync", return_value=MagicMock())
    await fetcher.fetch_video_info("https://youtube.com/watch?v=abc", "mp4")
    mock_sync.assert_called_once_with("https://youtube.com/watch?v=abc", "mp4", None)


async def test_fetch_video_info_passes_cookies_to_sync(mocker, fetcher):
    mock_sync = mocker.patch.object(fetcher, "_fetch_video_info_sync", return_value=MagicMock())
    await fetcher.fetch_video_info("https://youtube.com/watch?v=abc", "mp4", cookies="cookie_data")
    mock_sync.assert_called_once_with("https://youtube.com/watch?v=abc", "mp4", "cookie_data")


async def test_fetch_video_info_returns_none_on_exception(mocker, fetcher):
    mocker.patch.object(
        fetcher, "_fetch_video_info_sync", side_effect=Exception("ydl error")
    )
    result = await fetcher.fetch_video_info("https://youtube.com/watch?v=abc")
    assert result is None
