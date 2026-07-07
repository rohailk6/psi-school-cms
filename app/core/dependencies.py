from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db
from app.schemas.auth import TokenData

# Tells FastAPI where to look for the token in the request.
# It reads the "Authorization: Bearer <token>" header automatically.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> TokenData:
    """
    Decodes the JWT and returns its contents as a TokenData object.

    KEY DESIGN DECISION: This does NOT hit the database.
    All the information we need (user id, roles, permissions) was
    embedded in the token at login time. This keeps every request fast.

    The tradeoff: if an admin revokes a user's role mid-session,
    their access_token remains valid until it expires (15 min max).
    That's an acceptable tradeoff for this MVP — refresh will fail.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    # Verify this is an access token, not a refresh token
    # (both are JWTs, but we stamp them with a "type" field)
    if payload.get("type") != "access":
        raise credentials_exception

    user_id: str | None = payload.get("sub")
    email: str | None = payload.get("email")
    if not user_id or not email:
        raise credentials_exception

    return TokenData(
        sub=user_id,
        email=email,
        roles=payload.get("roles", []),
        permissions=payload.get("permissions", []),
    )


def require_permission(permission: str):
    """
    Factory that creates an endpoint dependency checking one permission.

    Usage in an endpoint:
        @router.post("/exams")
        async def create_exam(
            body: ExamCreate,
            current_user: TokenData = Depends(require_permission("exams:write")),
        ):

    How it works:
    1. get_current_user() decodes the JWT → TokenData
    2. We check if the required permission code is in token's permissions list
    3. If yes → return TokenData so the endpoint can use sub/email/roles
    4. If no → raise 403 Forbidden

    The permission string ("exams:write") is checked against the list
    embedded in the token at login — zero DB queries.
    """
    async def checker(
        current_user: TokenData = Depends(get_current_user),
    ) -> TokenData:
        if permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: requires '{permission}'",
            )
        return current_user

    return Depends(checker)


def require_any_role(*role_names: str):
    """
    Shortcut for role-level checks (coarser than permission checks).
    Use require_permission() for most endpoints; this is for cases
    where you need "is this user an admin?" without a specific action.
    """
    async def checker(
        current_user: TokenData = Depends(get_current_user),
    ) -> TokenData:
        if not any(role in current_user.roles for role in role_names):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the required role",
            )
        return current_user

    return Depends(checker)


# ── Convenience shortcuts ─────────────────────────────────────────────────────
# Import these in endpoints instead of writing require_any_role() every time.
# These will be replaced by require_permission() calls as endpoints are updated.

require_admin = require_any_role("admin", "super_admin")
require_teacher = require_any_role("teacher", "admin", "super_admin")
require_student = require_any_role("student")
