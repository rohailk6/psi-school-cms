from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import require_permission
from app.services import result_service

router = APIRouter(prefix="/results", tags=["Results"])


@router.get("/student/{student_id}")
async def student_results(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_permission("marks:read"),
):
    """
    All exam results for a student, grouped by exam.
    Grades are computed on the fly — never stored.
    """
    return await result_service.get_student_results(db, student_id)


@router.get("/exam/{exam_id}")
async def exam_results(
    exam_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_permission("marks:read"),
):
    """
    Full result sheet for an exam — every student, every subject.
    Used by admin to generate the class result.
    """
    return await result_service.get_exam_results(db, exam_id)


@router.get("/report-card/{student_id}/{exam_id}")
async def report_card(
    student_id: UUID,
    exam_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_permission("marks:read"),
):
    """
    Detailed report card for one student in one exam.
    Includes class/section, per-subject breakdown, totals, and overall grade.
    """
    return await result_service.get_report_card(db, student_id, exam_id)
