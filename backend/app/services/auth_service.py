"""Authentication business logic.

Framework-agnostic: no FastAPI, no HTTP, no cookies here. Takes a DB session, returns
domain objects or raises domain exceptions. This is the layer covered by unit tests.
"""

import jwt
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, db: Session) -> None:
        self.users = UserRepository(db)

    # ── Registration ─────────────────────────────────────────────────────────
    def register(self, *, email: str, password: str, full_name: str | None) -> User:
        normalized = email.strip().lower()
        if self.users.get_by_email(normalized) is not None:
            raise ConflictError("An account with this email already exists")
        return self.users.create(
            email=normalized,
            hashed_password=hash_password(password),
            full_name=full_name,
        )

    # ── Login ────────────────────────────────────────────────────────────────
    def authenticate(self, *, email: str, password: str) -> User:
        user = self.users.get_by_email(email.strip().lower())
        # Same error whether the email is unknown or the password is wrong, so the
        # endpoint can't be used to enumerate registered accounts.
        if user is None or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Incorrect email or password")
        if not user.is_active:
            raise AuthenticationError("This account is disabled")
        return user

    # ── Tokens ───────────────────────────────────────────────────────────────
    def issue_tokens(self, user: User) -> tuple[str, str]:
        """Return (access_token, refresh_token) for a user."""
        return create_access_token(user.id), create_refresh_token(user.id)

    def user_from_refresh_token(self, token: str) -> User:
        """Validate a refresh token and return its user, or raise."""
        try:
            payload = decode_token(token, expected_type="refresh")
        except jwt.InvalidTokenError as exc:
            raise AuthenticationError("Invalid or expired session") from exc

        user = self.users.get(int(payload["sub"]))
        if user is None or not user.is_active:
            raise AuthenticationError("Invalid or expired session")
        return user

    def get_active_user(self, user_id: int) -> User:
        user = self.users.get(user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("User no longer exists")
        return user
