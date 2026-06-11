from unittest.mock import MagicMock

import pytest

from core.utils import (
    clean_cookie_string,
    decrypt_cookies,
    encrypt_cookies,
    get_client_ip,
    get_video_id_from_url,
    validate_youtube_url,
)


# ---------------------------------------------------------------------------
# validate_youtube_url
# ---------------------------------------------------------------------------


def test_validate_youtube_url_standard_watch():
    assert validate_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True


def test_validate_youtube_url_short_link():
    assert validate_youtube_url("https://youtu.be/dQw4w9WgXcQ") is True


def test_validate_youtube_url_nocookie_domain():
    assert validate_youtube_url("https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ") is True


def test_validate_youtube_url_rejects_vimeo():
    assert validate_youtube_url("https://vimeo.com/123456") is False


def test_validate_youtube_url_rejects_plain_string():
    assert validate_youtube_url("not a url") is False


def test_validate_youtube_url_rejects_empty_string():
    assert validate_youtube_url("") is False


# ---------------------------------------------------------------------------
# get_video_id_from_url
# ---------------------------------------------------------------------------


def test_get_video_id_standard_watch():
    assert get_video_id_from_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_get_video_id_short_link():
    assert get_video_id_from_url("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"


def test_get_video_id_with_extra_params():
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120&list=PLabcdef"
    assert get_video_id_from_url(url) == "dQw4w9WgXcQ"


def test_get_video_id_returns_none_for_non_youtube():
    assert get_video_id_from_url("https://google.com") is None


# ---------------------------------------------------------------------------
# clean_cookie_string
# ---------------------------------------------------------------------------

_VALID_COOKIE_LINE = ".youtube.com\tTRUE\t/\tFALSE\t0\tCOOKIE_NAME\tcookie_value"


def test_clean_cookie_string_keeps_valid_lines():
    result = clean_cookie_string(f"# comment\n{_VALID_COOKIE_LINE}")
    assert _VALID_COOKIE_LINE in result


def test_clean_cookie_string_strips_comment_lines():
    result = clean_cookie_string("# this is a comment\n# another comment")
    assert result == ""


def test_clean_cookie_string_requires_seven_columns():
    short_line = "col1\tcol2\tcol3\tcol4\tcol5"
    assert clean_cookie_string(short_line) == ""


def test_clean_cookie_string_empty_input():
    assert clean_cookie_string("") == ""


def test_clean_cookie_string_multiple_valid_lines():
    second_line = ".google.com\tTRUE\t/\tFALSE\t0\tOTHER_COOKIE\tother_value"
    result = clean_cookie_string(f"{_VALID_COOKIE_LINE}\n{second_line}")
    assert _VALID_COOKIE_LINE in result
    assert second_line in result


# ---------------------------------------------------------------------------
# get_client_ip
# ---------------------------------------------------------------------------


def _make_request(x_forwarded_for=None, x_real_ip=None, client_host=None):
    request = MagicMock()
    headers = {
        "X-Forwarded-For": x_forwarded_for,
        "X-Real-IP": x_real_ip,
    }
    request.headers.get = lambda key, default=None: headers.get(key, default)
    if client_host:
        request.client = MagicMock()
        request.client.host = client_host
    else:
        request.client = None
    return request


def test_get_client_ip_from_x_forwarded_for():
    request = _make_request(x_forwarded_for="192.168.1.1, 10.0.0.1")
    assert get_client_ip(request) == "192.168.1.1"


def test_get_client_ip_x_forwarded_for_takes_priority_over_x_real_ip():
    request = _make_request(x_forwarded_for="1.2.3.4", x_real_ip="9.9.9.9")
    assert get_client_ip(request) == "1.2.3.4"


def test_get_client_ip_from_x_real_ip():
    request = _make_request(x_real_ip="203.0.113.5", client_host="127.0.0.1")
    assert get_client_ip(request) == "203.0.113.5"


def test_get_client_ip_fallback_to_client_host():
    request = _make_request(client_host="1.2.3.4")
    assert get_client_ip(request) == "1.2.3.4"


def test_get_client_ip_returns_unknown_when_no_client():
    request = _make_request()
    assert get_client_ip(request) == "unknown"


# ---------------------------------------------------------------------------
# encrypt_cookies / decrypt_cookies
# ---------------------------------------------------------------------------


def test_encrypt_decrypt_roundtrip():
    original = "# Netscape HTTP Cookie File\n.youtube.com\tTRUE\t/\tFALSE\t0\tSID\tvalue"
    encrypted = encrypt_cookies(original)
    assert decrypt_cookies(encrypted) == original


def test_encrypt_produces_bytes():
    result = encrypt_cookies("test_cookie_data")
    assert isinstance(result, bytes)


def test_encrypt_different_calls_produce_different_ciphertext():
    data = "same data"
    assert encrypt_cookies(data) != encrypt_cookies(data)


def test_decrypt_raises_on_tampered_data():
    encrypted = encrypt_cookies("some data")
    tampered = encrypted[:-4] + b"XXXX"
    with pytest.raises(Exception):
        decrypt_cookies(tampered)
