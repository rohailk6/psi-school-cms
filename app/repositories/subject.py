from __future__ import annotations

from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subject import Subject, ClassSubject, TeacherAssignment
from app.repositories.base import BaseRepository


class SubjectRepository(BaseRepository[Subject]):
    model = Subject

    async def get_by_code(self, code: str) -> Optional[Subject]:
        result = await self.db.execute(
            select(Subject).where(Subject.code == code)
        )
        return result.scalar_one_or_none()

    async def list_all(self, offset: int = 0, limit: int = 200) -> Sequence[Subject]:
        result = await self.db.execute(
            select(Subject).order_by(Subject.name).offset(offset).limit(limit)
        )
        return result.scalars().all()


class ClassSubjectRepository(BaseRepository[ClassSubject]):
    model = ClassSubject

    async def get_by_class_subject_year(
        self, class_id: UUID, subject_id: UUID, academic_year_id: UUID
    ) -> Optional[ClassSubject]:
        """Used to enforce the unique constraint before inserting."""
        result = await self.db.execute(
            select(ClassSubject).where(
                ClassSubject.class_id == class_id,
                ClassSubject.subject_id == subject_id,
                ClassSubject.academic_year_id == academic_year_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_class(self, class_id: UUID) -> Sequence[ClassSubject]:
        result = await self.db.execute(
            select(ClassSubject).where(ClassSubject.class_id == class_id)
        )
        return result.scalars().all()

    async def list_by_class_and_year(
        self, class_id: UUID, academic_year_id: UUID
    ) -> Sequence[ClassSubject]:
        result = await self.db.execute(
            select(ClassSubject).where(
                ClassSubject.class_id == class_id,
                ClassSubject.academic_year_id == academic_year_id,
            )
        )
        return result.scalars().all()


class TeacherAssignmentRepository(BaseRepository[TeacherAssignment]):
    model = TeacherAssignment

    async def get_existing(
        self,
        teacher_id: UUID,
        class_id: UUID,
        section_id: Optional[UUID],
        subject_id: UUID,
        academic_year_id: UUID,
    ) -> Optional[TeacherAssignment]:
        """Checks for duplicate before inserting a new assignment."""
        result = await self.db.execute(
            select(TeacherAssignment).where(
                TeacherAssignment.teacher_id == teacher_id,
                TeacherAssignment.class_id == class_id,
                TeacherAssignment.section_id == section_id,
                TeacherAssignment.subject_id == subject_id,
                TeacherAssignment.academic_year_id == academic_year_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_teacher(self, teacher_id: UUID) -> Sequence[TeacherAssignment]:
        result = await self.db.execute(
            select(TeacherAssignment).where(
                TeacherAssignment.teacher_id == teacher_id
            )
        )
        return result.scalars().all()
