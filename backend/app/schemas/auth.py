"""Authentication request/response schemas."""

from pydantic import BaseModel, EmailStr

from app.schemas.user import UserRead


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AccessToken(BaseModel):
    """Returned to the client. The refresh token is delivered as an httpOnly cookie
    and never appears in a response body."""

    access_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    """Login/register payload: the access token plus the authenticated user."""

    access_token: str
    token_type: str = "bearer"
    user: UserRead
