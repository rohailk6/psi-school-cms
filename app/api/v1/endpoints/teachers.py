from __future__ import annotations
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import require_admin
from app.schemas.teacher import (
    TeacherCreate, TeacherUpdate, TeacherResponse,
    AssignTeacherRequest, TeacherAssignmentResponse, PaginatedTeachers,
)
from app.services import teacher_service

router = APIRouter(prefix="/teachers", tags=["Teachers"])


@router.get("/", response_model=PaginatedTeachers)
async def list_teachers(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    teachers, total = await teacher_service.get_teachers(db, skip=skip, limit=limit, search=search)
    return PaginatedTeachers(
        total=total, skip=skip, limit=limit,
        data=[TeacherResponse.model_validate(t) for t in teachers],
    )


@router.post("/", response_model=TeacherResponse, status_code=201)
async def create_teacher(
    payload: TeacherCreate,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    """Create a teacher and their login account."""
    return await teacher_service.create_teacher(db, payload)


@router.get("/{teacher_id}", response_model=TeacherResponse)
async def get_teacher(
    teacher_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    return await teacher_service.get_teacher_by_id(db, teacher_id)


@router.patch("/{teacher_id}", response_model=TeacherResponse)
async def update_teacher(
    teacher_id: UUID,
    payload: TeacherUpdate,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    return await teacher_service.update_teacher(db, teacher_id, payload)


@router.delete("/{teacher_id}", status_code=204)
async def delete_teacher(
    teacher_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    """Soft-delete: deactivates the teacher and their user account."""
    await teacher_service.delete_teacher(db, teacher_id)


@router.post("/{teacher_id}/assign", response_model=TeacherAssignmentResponse, status_code=201)
async def assign_teacher(
    teacher_id: UUID,
    payload: AssignTeacherRequest,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    """Assign a teacher to a class subject + section."""
    return await teacher_service.assign_teacher(db, teacher_id, payload)


@router.get("/{teacher_id}/assignments", response_model=list[TeacherAssignmentResponse])
async def get_assignments(
    teacher_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    return await teacher_service.get_teacher_assignments(db, teacher_id)