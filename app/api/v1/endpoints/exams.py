from __future__ import annotations
from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import require_admin, require_teacher, get_current_user
from app.schemas.auth import TokenData
from app.schemas.exam import (
    ExamCreate, ExamUpdate, ExamResponse,
    ExamSubjectCreate, ExamSubjectResponse,
    MarkEntryRequest, MarkUpdate, MarkResponse,
)
from app.services import exam_service

router = APIRouter(prefix="/exams", tags=["Exams"])


@router.get("/", response_model=List[ExamResponse])
async def list_exams(
    academic_year_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    return await exam_service.get_exams(db, academic_year_id=academic_year_id)


@router.post("/", response_model=ExamResponse, status_code=201)
async def create_exam(
    payload: ExamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
    _=require_admin,
):
    return await exam_service.create_exam(db, payload, created_by=UUID(current_user.sub))


@router.get("/{exam_id}", response_model=ExamResponse)
async def get_exam(
    exam_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    return await exam_service.get_exam_by_id(db, exam_id)


@router.patch("/{exam_id}", response_model=ExamResponse)
async def update_exam(
    exam_id: UUID,
    payload: ExamUpdate,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    return await exam_service.update_exam(db, exam_id, payload)


@router.delete("/{exam_id}", status_code=204)
async def delete_exam(
    exam_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    await exam_service.delete_exam(db, exam_id)


@router.post("/{exam_id}/status", response_model=ExamResponse)
async def transition_status(
    exam_id: UUID,
    new_status: str = Query(..., description="Target status: published | ongoing | completed | cancelled"),
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    """Advance the exam through its status state machine."""
    return await exam_service.transition_exam_status(db, exam_id, new_status)


# ── Exam Subjects ─────────────────────────────────────────────────────────────

@router.get("/{exam_id}/subjects", response_model=List[ExamSubjectResponse])
async def list_exam_subjects(
    exam_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    return await exam_service.get_exam_subjects(db, exam_id)


@router.post("/{exam_id}/subjects", response_model=ExamSubjectResponse, status_code=201)
async def add_exam_subject(
    exam_id: UUID,
    payload: ExamSubjectCreate,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    return await exam_service.add_exam_subject(db, exam_id, payload)


# ── Mark Entry ────────────────────────────────────────────────────────────────

@router.post("/exam-subjects/{exam_subject_id}/marks", response_model=List[MarkResponse])
async def enter_marks(
    exam_subject_id: UUID,
    payload: MarkEntryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Teachers enter marks for multiple students in bulk."""
    return await exam_service.enter_marks(db, exam_subject_id, payload, UUID(current_user.sub))


@router.get("/exam-subjects/{exam_subject_id}/marks", response_model=List[MarkResponse])
async def get_marks(
    exam_subject_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    return await exam_service.get_marks_for_exam_subject(db, exam_subject_id)


@router.get("/student/{student_id}/marks", response_model=List[MarkResponse])
async def get_student_marks(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    return await exam_service.get_student_marks(db, student_id)


# ── Single mark update ────────────────────────────────────────────────────────

marks_router = APIRouter(prefix="/marks", tags=["Marks"])


@marks_router.put("/{mark_id}", response_model=MarkResponse)
async def update_mark(
    mark_id: UUID,
    payload: MarkUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenData = Depends(get_current_user),
):
    """Update a single mark entry (corrections after initial bulk entry)."""
    return await exam_service.update_mark(db, mark_id, payload, UUID(current_user.sub))
