from __future__ import annotations
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import require_admin
from app.schemas.student import (
    StudentCreate, StudentUpdate, StudentResponse,
    EnrollStudentRequest, EnrollmentResponse, PaginatedStudents,
)
from app.services import student_service

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("/", response_model=PaginatedStudents)
async def list_students(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    """List all students with optional name search and pagination."""
    students, total = await student_service.get_students(db, skip=skip, limit=limit, search=search)
    return PaginatedStudents(
        total=total, skip=skip, limit=limit,
        data=[StudentResponse.model_validate(s) for s in students],
    )


@router.post("/", response_model=StudentResponse, status_code=201)
async def create_student(
    payload: StudentCreate,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    """Create a student and their login account in one request."""
    return await student_service.create_student(db, payload)


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    return await student_service.get_student_by_id(db, student_id)


@router.patch("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: UUID,
    payload: StudentUpdate,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    return await student_service.update_student(db, student_id, payload)


@router.delete("/{student_id}", status_code=204)
async def delete_student(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    await student_service.delete_student(db, student_id)


@router.post("/{student_id}/enroll", response_model=EnrollmentResponse, status_code=201)
async def enroll_student(
    student_id: UUID,
    payload: EnrollStudentRequest,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    """Enroll a student into a section."""
    return await student_service.enroll_student(db, student_id, payload)


@router.get("/{student_id}/enrollments", response_model=list[EnrollmentResponse])
async def get_student_enrollments(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    return await student_service.get_student_enrollments(db, student_id)