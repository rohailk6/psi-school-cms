from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student
from app.models.teacher import Teacher
from app.models.class_ import Class
from app.models.exam import Exam
from app.models.school import AcademicYear


async def get_stats(db: AsyncSession) -> dict:
    total_students = (await db.execute(
        select(func.count()).select_from(Student).where(Student.deleted_at.is_(None))
    )).scalar_one()

    total_teachers = (await db.execute(
        select(func.count()).select_from(Teacher).where(Teacher.deleted_at.is_(None))
    )).scalar_one()

    total_classes = (await db.execute(
        select(func.count()).select_from(Class)
    )).scalar_one()

    active_year_result = await db.execute(
        select(AcademicYear.name).where(AcademicYear.is_active.is_(True))
    )
    active_year = active_year_result.scalar_one_or_none()

    exam_counts = (await db.execute(
        select(Exam.status, func.count().label("n"))
        .group_by(Exam.status)
    )).all()
    by_status = {row.status: row.n for row in exam_counts}

    return {
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_classes": total_classes,
        "active_academic_year": active_year,
        "exams": {
            "total": sum(by_status.values()),
            "draft": by_status.get("draft", 0),
            "published": by_status.get("published", 0),
            "ongoing": by_status.get("ongoing", 0),
            "completed": by_status.get("completed", 0),
            "cancelled": by_status.get("cancelled", 0),
        },
    }
