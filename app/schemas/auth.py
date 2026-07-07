from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """What the client sends to log in."""
    email: EmailStr
    password: str


class TokenData(BaseModel):
    """
    The decoded contents of a JWT access token.

    This is what get_current_user() returns — it comes from decoding
    the JWT, NOT from a database query. That's the point: every
    request can be authenticated and authorized without a DB hit.

    sub  = "subject" = the user's UUID (standard JWT claim)
    roles       = role names e.g. ["teacher"]
    permissions = permission codes e.g. ["marks:write", "students:read"]
                  these are checked by require_permission() in endpoints
    """
    sub: str          # user UUID as string (standard JWT "subject" field)
    email: str
    roles: List[str]
    permissions: List[str]


class TokenResponse(BaseModel):
    """
    What we send back after a successful login.

    access_token  — short-lived (15 min). Sent with every API request.
    refresh_token — long-lived (7 days). Used only to get a new access token.
    token_type    — always "bearer" per the OAuth2 standard.
    user          — basic user info so the frontend can render the UI
                    without needing a second /me request.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserBrief"


class UserBrief(BaseModel):
    """
    Minimal user info returned at login.
    Enough for the frontend to know who is logged in and what to show.
    """
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    roles: List[str]
    permissions: List[str]

    model_config = {"from_attributes": True}


class RefreshRequest(BaseModel):
    """
    Sent when the access token has expired.
    The frontend exchanges this refresh token for a new access token.
    """
    refresh_token: str


class LogoutRequest(BaseModel):
    """
    The refresh token to revoke on logout.
    We revoke server-side so the token can't be used again even if
    someone copied it from memory/storage.
    """
    refresh_token: str
