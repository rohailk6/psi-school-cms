from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import require_admin, require_permission
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services import user_service

router = APIRouter(prefix="/users", tags=["Users"])


class PaginatedUsers(BaseModel):
    total: int
    skip: int
    limit: int
    data: List[UserResponse]


class PasswordResetRequest(BaseModel):
    new_password: str


@router.get("/", response_model=PaginatedUsers)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    role: Optional[str] = Query(None, description="Filter by role name"),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _=require_permission("users:read"),
):
    users, total = await user_service.list_users(db, skip=skip, limit=limit, role=role, search=search)
    return PaginatedUsers(
        total=total, skip=skip, limit=limit,
        data=[UserResponse.model_validate(u) for u in users],
    )


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    _=require_permission("users:write"),
):
    return await user_service.create_user(db, payload)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_permission("users:read"),
):
    return await user_service.get_user_by_id(db, user_id)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _=require_permission("users:write"),
):
    return await user_service.update_user(db, user_id, payload)


@router.post("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_permission("users:write"),
):
    return await user_service.activate_user(db, user_id)


@router.post("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_permission("users:write"),
):
    return await user_service.deactivate_user(db, user_id)


@router.post("/{user_id}/reset-password", status_code=204)
async def reset_password(
    user_id: UUID,
    payload: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
    _=require_permission("users:write"),
):
    await user_service.reset_password(db, user_id, payload.new_password)

