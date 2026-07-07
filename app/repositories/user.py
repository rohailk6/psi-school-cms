from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User, RefreshToken, UserRoleAssignment
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_with_roles(self, user_id: UUID) -> Optional[User]:
        """
        Loads the user with role_assignments → role → permissions
        in 2 extra SELECTs (selectinload chain), not N+1.
        Used at login to build the JWT payload.
        """
        result = await self.db.execute(
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.role_assignments).selectinload(UserRoleAssignment.role)
            )
        )
        return result.scalar_one_or_none()

    async def get_by_email_with_roles(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User)
            .where(User.email == email)
            .options(
                selectinload(User.role_assignments).selectinload(UserRoleAssignment.role)
            )
        )
        return result.scalar_one_or_none()


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    model = RefreshToken

    async def get_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def revoke(self, token: RefreshToken) -> None:
        token.revoked_at = datetime.utcnow()
