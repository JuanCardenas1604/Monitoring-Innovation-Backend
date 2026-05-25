import time
import uuid
from datetime import timedelta

import pytest
from jose import jwt

from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.core.config import settings


class TestPasswordHashing:
    def test_hash_and_verify(self):
        pw = "TestPass123!"
        h = hash_password(pw)
        assert h != pw
        assert verify_password(pw, h)

    def test_wrong_password_fails(self):
        h = hash_password("correct")
        assert not verify_password("wrong", h)

    def test_empty_password_fails(self):
        h = hash_password("something")
        assert not verify_password("", h)

    def test_different_hashes_for_same_password(self):
        p1 = hash_password("same")
        p2 = hash_password("same")
        assert p1 != p2


class TestJWT:
    def test_create_and_decode(self):
        payload = {"sub": str(uuid.uuid4()), "role": "admin"}
        token = create_access_token(payload)
        decoded = decode_access_token(token)
        assert decoded["sub"] == payload["sub"]
        assert decoded["role"] == payload["role"]

    def test_custom_expiry(self):
        payload = {"sub": "user-1"}
        token = create_access_token(payload, expires_delta=timedelta(hours=1))
        decoded = decode_access_token(token)
        assert decoded["sub"] == "user-1"

    def test_expired_token_returns_none(self):
        payload = {"sub": "user-1"}
        token = create_access_token(payload, expires_delta=timedelta(seconds=-1))
        decoded = decode_access_token(token)
        assert decoded is None

    def test_invalid_signature_returns_none(self):
        bad_token = jwt.encode({"sub": "user-1"}, "wrong-secret", algorithm=settings.ALGORITHM)
        decoded = decode_access_token(bad_token)
        assert decoded is None

    def test_malformed_token_returns_none(self):
        assert decode_access_token("not-a-jwt") is None
        assert decode_access_token("") is None

    def test_token_has_exp_claim(self):
        payload = {"sub": "user-1", "role": "viewer"}
        token = create_access_token(payload)
        decoded = decode_access_token(token)
        assert "exp" in decoded
        assert decoded["exp"] > time.time()
