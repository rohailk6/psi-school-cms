from __future__ import annotations

from typing import Optional, Sequence, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User, Role, UserRoleAssignment
from app.repositories.user import UserRepository
from app.core.security import hash_password


async def _get_role_by_name(db: AsyncSession, role_name: str) -> Role:
    result = await db.execute(select(Role).where(Role.name == role_name))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(400, f"Role '{role_name}' does not exist")
    return role


async def list_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    role: Optional[str] = None,
    search: Optional[str] = None,
) -> Tuple[Sequence[User], int]:
    from sqlalchemy.orm import joinedload

    base = (
        select(User)
        .options(selectinload(User.role_assignments).selectinload(UserRoleAssignment.role))
        .where(User.deleted_at.is_(None))
    )

    if role:
        base = base.join(User.role_assignments).join(UserRoleAssignment.role).where(Role.name == role)
    if search:
        p = f"%{search}%"
        base = base.where(
            User.first_name.ilike(p) | User.last_name.ilike(p) | User.email.ilike(p)
        )

    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar_one()
    users = (
        await db.execute(base.order_by(User.last_name, User.first_name).offset(skip).limit(limit))
    ).scalars().all()

    return users, total


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User:
    result = await db.execute(
        select(User)
        .options(selectinload(User.role_assignments).selectinload(UserRoleAssignment.role))
        .where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user


async def create_user(db: AsyncSession, payload) -> User:
    repo = UserRepository(db)

    if await repo.get_by_email(payload.email):
        raise HTTPException(400, "Email already registered")

    role = await _get_role_by_name(db, payload.role)

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone=payload.phone,
        is_active=True,
    )
    await repo.add(user)

    db.add(UserRoleAssignment(user_id=user.id, role_id=role.id))
    await db.commit()

    return await get_user_by_id(db, user.id)


async def update_user(db: AsyncSession, user_id: UUID, payload) -> User:
    user = await get_user_by_id(db, user_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    await db.commit()
    return await get_user_by_id(db, user_id)


async def activate_user(db: AsyncSession, user_id: UUID) -> User:
    user = await get_user_by_id(db, user_id)
    user.is_active = True
    await db.commit()
    return await get_user_by_id(db, user_id)


async def deactivate_user(db: AsyncSession, user_id: UUID) -> User:
    user = await get_user_by_id(db, user_id)
    user.is_active = False
    await db.commit()
    return await get_user_by_id(db, user_id)


async def reset_password(db: AsyncSession, user_id: UUID, new_password: str) -> None:
    user = await get_user_by_id(db, user_id)
    user.password_hash = hash_password(new_password)
    await db.commit()
