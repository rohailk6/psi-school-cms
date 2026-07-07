from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import verify_password, create_access_token, create_refresh_token, hash_token
from app.models.user import User
from app.repositories.user import UserRepository, RefreshTokenRepository
from app.schemas.auth import LoginRequest, TokenResponse, UserBrief


def _collect_roles_and_permissions(user: User) -> tuple[list[str], list[str]]:
    """
    Walks the user's role assignments and collects role names + permission codes.
    Uses a set for permissions to deduplicate (two roles may share a permission).
    Returns sorted permissions so the JWT payload is deterministic.
    """
    roles: list[str] = []
    permissions: set[str] = set()
    for assignment in user.role_assignments:
        roles.append(assignment.role.name)
        for perm in assignment.role.permissions:
            permissions.add(perm.code)
    return roles, sorted(permissions)


async def login(db: AsyncSession, payload: LoginRequest) -> TokenResponse:
    user_repo = UserRepository(db)
    token_repo = RefreshTokenRepository(db)

    # Load user + roles in one query chain (selectinload)
    user = await user_repo.get_by_email_with_roles(payload.email)

    if not user or not user.is_active or user.deleted_at is not None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")

    roles, permissions = _collect_roles_and_permissions(user)

    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "roles": roles,
        "permissions": permissions,
    }
    access_token = create_access_token(token_data)
    refresh_token_str = create_refresh_token(token_data)

    from app.models.user import RefreshToken
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    await token_repo.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token_str),
        expires_at=expires_at,
    ))

    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_str,
        user=UserBrief(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            roles=roles,
            permissions=permissions,
        ),
    )


async def refresh_tokens(db: AsyncSession, refresh_token_str: str) -> TokenResponse:
    """
    Exchange a valid refresh token for a new access + refresh token pair.

    Why load the user from DB here (instead of just re-using the JWT payload)?
    A user's roles may have changed during the 7-day refresh window.
    Loading fresh roles ensures the new access token reflects current permissions.

    Token rotation: the old refresh token is revoked and a new one is issued.
    If an attacker steals a refresh token and uses it after the legitimate
    user has already rotated it, the lookup will find revoked_at is set and reject it.
    """
    from app.models.user import RefreshToken
    user_repo = UserRepository(db)
    token_repo = RefreshTokenRepository(db)

    token_hash = hash_token(refresh_token_str)
    db_token = await token_repo.get_by_hash(token_hash)

    if not db_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")

    now = datetime.now(timezone.utc)
    if db_token.expires_at.replace(tzinfo=timezone.utc) < now:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Refresh token has expired")

    # Revoke old token before issuing new one
    token_repo.revoke(db_token)

    # Load current user with up-to-date roles
    user = await user_repo.get_with_roles(db_token.user_id)
    if not user or not user.is_active or user.deleted_at is not None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User account is inactive")

    roles, permissions = _collect_roles_and_permissions(user)
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "roles": roles,
        "permissions": permissions,
    }

    access_token = create_access_token(token_data)
    new_refresh_str = create_refresh_token(token_data)

    expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    await token_repo.add(RefreshToken(
        user_id=user.id,
        token_hash=hash_token(new_refresh_str),
        expires_at=expires_at,
    ))
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_str,
        user=UserBrief(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            roles=roles,
            permissions=permissions,
        ),
    )


async def logout(db: AsyncSession, refresh_token_str: str) -> None:
    token_repo = RefreshTokenRepository(db)
    token = await token_repo.get_by_hash(hash_token(refresh_token_str))
    if token:
        token_repo.revoke(token)
        await db.commit()
    # Silently succeed if token not found — already revoked or never existed
