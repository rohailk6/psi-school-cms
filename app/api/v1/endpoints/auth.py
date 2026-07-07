from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest, LogoutRequest, TokenData, UserBrief
from app.services import auth_service

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Authenticate with email + password.
    Returns access token (15 min) and refresh token (7 days).
    The access token contains roles + permissions embedded inside it.
    """
    return await auth_service.login(db, payload)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: LogoutRequest,
    db: AsyncSession = Depends(get_db),
    _: TokenData = Depends(get_current_user),
):
    """
    Revokes the refresh token server-side.
    The access token stays valid until it expires (max 15 min) — that's
    the accepted tradeoff for stateless JWTs.
    """
    await auth_service.logout(db, payload.refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Exchange a valid refresh token for a new access + refresh token pair.
    Old refresh token is revoked (token rotation — one-time use).
    """
    return await auth_service.refresh_tokens(db, payload.refresh_token)


@router.get("/me", response_model=UserBrief)
async def me(current_user: TokenData = Depends(get_current_user)):
    """
    Returns the currently authenticated user's profile from the JWT.
    No database query — everything comes from the token itself.
    """
    return UserBrief(
        id=current_user.sub,
        email=current_user.email,
        first_name="",
        last_name="",
        roles=current_user.roles,
        permissions=current_user.permissions,
    )
