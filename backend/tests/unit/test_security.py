import pytest
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token


class TestSecurity:
    def test_hash_and_verify_password(self):
        password = "test-password-123"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("correct-password")
        assert not verify_password("wrong-password", hashed)

    def test_create_and_decode_token(self):
        subject = "user-123"
        token = create_access_token(subject)
        decoded = decode_access_token(token)
        assert decoded == subject

    def test_invalid_token_returns_none(self):
        result = decode_access_token("invalid-token")
        assert result is None

    def test_different_passwords_different_hashes(self):
        hash1 = hash_password("password-1")
        hash2 = hash_password("password-2")
        assert hash1 != hash2
