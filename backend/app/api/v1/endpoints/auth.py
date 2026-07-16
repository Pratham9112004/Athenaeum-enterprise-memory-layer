"""Authentication endpoints.

Token strategy:
  * access token  -> returned in the response body; the SPA holds it in memory only.
  * refresh token -> set as an httpOnly, SameSite=Lax cookie the JS can never read,
                     so an XSS payload cannot exfiltrate a long-lived credential.
"""

from fastapi import APIRouter, Request, Response, status

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.core.exceptions import AuthenticationError
from app.schemas.auth import AuthResponse, LoginRequest
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

_COOKIE_PATH = settings.api_v1_prefix + "/auth"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path=_COOKIE_PATH,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=settings.refresh_cookie_name, path=_COOKIE_PATH)


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, response: Response, db: DbSession) -> AuthResponse:
    service = AuthService(db)
    user = service.register(
        email=payload.email, password=payload.password, full_name=payload.full_name
    )
    access, refresh = service.issue_tokens(user)
    _set_refresh_cookie(response, refresh)
    return AuthResponse(access_token=access, user=UserRead.model_validate(user))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response, db: DbSession) -> AuthResponse:
    service = AuthService(db)
    user = service.authenticate(email=payload.email, password=payload.password)
    access, refresh = service.issue_tokens(user)
    _set_refresh_cookie(response, refresh)
    return AuthResponse(access_token=access, user=UserRead.model_validate(user))


@router.post("/refresh", response_model=AuthResponse)
def refresh(request: Request, response: Response, db: DbSession) -> AuthResponse:
    """Mint a fresh access token from the httpOnly refresh cookie, rotating it."""
    token = request.cookies.get(settings.refresh_cookie_name)
    if not token:
        raise AuthenticationError("No active session")

    service = AuthService(db)
    user = service.user_from_refresh_token(token)
    access, new_refresh = service.issue_tokens(user)
    _set_refresh_cookie(response, new_refresh)
    return AuthResponse(access_token=access, user=UserRead.model_validate(user))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> Response:
    _clear_refresh_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserRead)
def me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)
