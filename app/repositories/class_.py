from __future__ import annotations

from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.class_ import Class, Section, StudentEnrollment
from app.repositories.base import BaseRepository


class ClassRepository(BaseRepository[Class]):
    model = Class

    async def get_by_id_with_sections(self, class_id: UUID) -> Optional[Class]:
        result = await self.db.execute(
            select(Class)
            .options(selectinload(Class.sections))
            .where(Class.id == class_id)
        )
        return result.scalar_one_or_none()

    async def list_with_sections(self) -> Sequence[Class]:
        result = await self.db.execute(
            select(Class)
            .options(selectinload(Class.sections))
            .order_by(Class.numeric_level)
        )
        return result.scalars().all()


class SectionRepository(BaseRepository[Section]):
    model = Section

    async def list_by_class(self, class_id: UUID) -> Sequence[Section]:
        result = await self.db.execute(
            select(Section)
            .where(Section.class_id == class_id)
            .order_by(Section.name)
        )
        return result.scalars().all()


class EnrollmentRepository(BaseRepository[StudentEnrollment]):
    model = StudentEnrollment

    async def get_by_student_and_year(
        self, student_id: UUID, academic_year_id: UUID
    ) -> Optional[StudentEnrollment]:
        """Used to enforce the one-enrollment-per-student-per-year rule."""
        result = await self.db.execute(
            select(StudentEnrollment).where(
                StudentEnrollment.student_id == student_id,
                StudentEnrollment.academic_year_id == academic_year_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_active_by_section(self, section_id: UUID) -> Sequence[StudentEnrollment]:
        """Returns students currently enrolled (status='active') in a section."""
        result = await self.db.execute(
            select(StudentEnrollment)
            .options(selectinload(StudentEnrollment.student))
            .where(
                StudentEnrollment.section_id == section_id,
                StudentEnrollment.status == "active",
            )
        )
        return result.scalars().all()

    async def list_by_student(self, student_id: UUID) -> Sequence[StudentEnrollment]:
        result = await self.db.execute(
            select(StudentEnrollment)
            .options(selectinload(StudentEnrollment.section))
            .where(StudentEnrollment.student_id == student_id)
            .order_by(StudentEnrollment.enrollment_date.desc())
        )
        return result.scalars().all()
