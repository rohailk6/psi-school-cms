from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.core.dependencies import require_admin
from app.models.user import Role, Permission

router = APIRouter(tags=["Roles & Permissions"])


class PermissionOut(BaseModel):
    id: UUID
    code: str
    resource: str
    action: str
    description: Optional[str] = None
    model_config = {"from_attributes": True}


class RoleOut(BaseModel):
    id: UUID
    name: str
    display_name: str
    description: Optional[str] = None
    is_system: bool
    permissions: List[PermissionOut] = []
    model_config = {"from_attributes": True}


@router.get("/roles", response_model=List[RoleOut])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    result = await db.execute(
        select(Role).options(selectinload(Role.permissions)).order_by(Role.name)
    )
    return result.scalars().all()


@router.get("/roles/{role_id}", response_model=RoleOut)
async def get_role(
    role_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    result = await db.execute(
        select(Role).options(selectinload(Role.permissions)).where(Role.id == role_id)
    )
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(404, "Role not found")
    return role


@router.get("/permissions", response_model=List[PermissionOut])
async def list_permissions(
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    result = await db.execute(
        select(Permission).order_by(Permission.resource, Permission.action)
    )
    return result.scalars().all()
