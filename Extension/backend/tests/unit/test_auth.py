from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt

from core.auth import create_access_token, get_current_user, verify_token
from core.config import settings


# ---------------------------------------------------------------------------
# create_access_token
# ---------------------------------------------------------------------------


def test_create_access_token_returns_string():
    token = create_access_token({"sub": "test_user"})
    assert isinstance(token, str)
    assert len(token) > 0


def test_create_access_token_contains_expected_claims():
    token = create_access_token({"sub": "test_user"})
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["sub"] == "test_user"
    assert "exp" in payload
    assert "iat" in payload


def test_create_access_token_with_explicit_delta():
    delta = timedelta(minutes=5)
    token = create_access_token({"sub": "test"}, expires_delta=delta)
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    duration = payload["exp"] - payload["iat"]
    assert abs(duration - 300) <= 2


def test_create_access_token_default_expiry_uses_settings():
    token = create_access_token({"sub": "test"})
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    expected_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    actual_seconds = payload["exp"] - payload["iat"]
    assert abs(actual_seconds - expected_seconds) <= 2


def test_create_access_token_preserves_extra_claims():
    token = create_access_token({"sub": "user", "user_agent": "TestBrowser/1.0"})
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    assert payload["user_agent"] == "TestBrowser/1.0"


# ---------------------------------------------------------------------------
# verify_token
# ---------------------------------------------------------------------------


def test_verify_token_valid_returns_payload():
    token = create_access_token({"sub": "user1"})
    result = verify_token(token)
    assert result is not None
    assert result["sub"] == "user1"


def test_verify_token_returns_none_for_garbage():
    assert verify_token("not.a.valid.token") is None


def test_verify_token_returns_none_for_wrong_secret():
    wrong_token = jwt.encode(
        {"sub": "user", "exp": datetime.utcnow() + timedelta(hours=1)},
        "wrong-secret-that-is-definitely-not-the-real-one",
        algorithm=settings.ALGORITHM,
    )
    assert verify_token(wrong_token) is None


def test_verify_token_returns_none_for_expired_token():
    expired_token = create_access_token({"sub": "user"}, expires_delta=timedelta(seconds=-10))
    assert verify_token(expired_token) is None


def test_verify_token_returns_none_for_empty_string():
    assert verify_token("") is None


# ---------------------------------------------------------------------------
# get_current_user
# ---------------------------------------------------------------------------


def test_get_current_user_raises_401_for_invalid_token():
    credentials = MagicMock(spec=HTTPAuthorizationCredentials)
    credentials.credentials = "not_a_real_token"
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials)
    assert exc_info.value.status_code == 401


def test_get_current_user_returns_payload_for_valid_token():
    token = create_access_token({"sub": "127.0.0.1"})
    credentials = MagicMock(spec=HTTPAuthorizationCredentials)
    credentials.credentials = token
    result = get_current_user(credentials)
    assert result is not None
    assert result["sub"] == "127.0.0.1"


def test_get_current_user_raises_401_for_expired_token():
    expired_token = create_access_token({"sub": "user"}, expires_delta=timedelta(seconds=-10))
    credentials = MagicMock(spec=HTTPAuthorizationCredentials)
    credentials.credentials = expired_token
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials)
    assert exc_info.value.status_code == 401
