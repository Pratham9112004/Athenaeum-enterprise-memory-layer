"""Unit tests for password hashing and JWT handling."""

import jwt
import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_roundtrip():
    hashed = hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"
    assert verify_password("correct horse battery staple", hashed)


def test_verify_rejects_wrong_password():
    hashed = hash_password("s3cret-password")
    assert not verify_password("not-the-password", hashed)


def test_password_over_72_bytes_does_not_raise():
    # bcrypt's 72-byte limit is handled by explicit truncation, not an exception.
    long_pw = "a" * 200
    hashed = hash_password(long_pw)
    assert verify_password(long_pw, hashed)


def test_verify_handles_malformed_hash_gracefully():
    assert not verify_password("whatever", "not-a-real-bcrypt-hash")


def test_access_token_roundtrip():
    token = create_access_token(42)
    payload = decode_token(token, expected_type="access")
    assert payload["sub"] == "42"
    assert payload["type"] == "access"


def test_refresh_token_roundtrip():
    token = create_refresh_token(7)
    payload = decode_token(token, expected_type="refresh")
    assert payload["sub"] == "7"
    assert payload["type"] == "refresh"


def test_decode_rejects_wrong_token_type():
    access = create_access_token(1)
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(access, expected_type="refresh")


def test_decode_rejects_tampered_token():
    token = create_access_token(1)
    tampered = token[:-2] + ("aa" if not token.endswith("aa") else "bb")
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(tampered, expected_type="access")
