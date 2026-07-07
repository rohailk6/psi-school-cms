from __future__ import annotations

from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.exam import Exam, ExamSubject, Mark
from app.repositories.base import BaseRepository


class ExamRepository(BaseRepository[Exam]):
    model = Exam

    async def get_by_id_with_subjects(self, exam_id: UUID) -> Optional[Exam]:
        result = await self.db.execute(
            select(Exam)
            .options(selectinload(Exam.exam_subjects))
            .where(Exam.id == exam_id)
        )
        return result.scalar_one_or_none()

    async def list_by_year(
        self, academic_year_id: Optional[UUID] = None
    ) -> Sequence[Exam]:
        query = select(Exam).order_by(Exam.start_date.desc())
        if academic_year_id:
            query = query.where(Exam.academic_year_id == academic_year_id)
        result = await self.db.execute(query)
        return result.scalars().all()


class ExamSubjectRepository(BaseRepository[ExamSubject]):
    model = ExamSubject

    async def get_by_exam_and_subject(
        self, exam_id: UUID, subject_id: UUID
    ) -> Optional[ExamSubject]:
        result = await self.db.execute(
            select(ExamSubject).where(
                ExamSubject.exam_id == exam_id,
                ExamSubject.subject_id == subject_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_exam(self, exam_id: UUID) -> Sequence[ExamSubject]:
        result = await self.db.execute(
            select(ExamSubject).where(ExamSubject.exam_id == exam_id)
        )
        return result.scalars().all()


class MarkRepository(BaseRepository[Mark]):
    model = Mark

    async def get_by_exam_subject_and_student(
        self, exam_subject_id: UUID, student_id: UUID
    ) -> Optional[Mark]:
        result = await self.db.execute(
            select(Mark).where(
                Mark.exam_subject_id == exam_subject_id,
                Mark.student_id == student_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_exam_subject(self, exam_subject_id: UUID) -> Sequence[Mark]:
        result = await self.db.execute(
            select(Mark).where(Mark.exam_subject_id == exam_subject_id)
        )
        return result.scalars().all()

    async def list_by_student(self, student_id: UUID) -> Sequence[Mark]:
        result = await self.db.execute(
            select(Mark)
            .options(selectinload(Mark.exam_subject))
            .where(Mark.student_id == student_id)
        )
        return result.scalars().all()
