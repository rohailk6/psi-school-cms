from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.student import Student
from app.models.user import User
from app.repositories.base import BaseRepository


class StudentRepository(BaseRepository[Student]):
    model = Student

    async def get_active_by_id(self, student_id) -> Optional[Student]:
        """Returns a non-deleted student with User loaded, or None."""
        result = await self.db.execute(
            select(Student)
            .join(Student.user)
            .options(selectinload(Student.user))
            .where(Student.id == student_id, Student.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def search(
        self, pattern: Optional[str], skip: int, limit: int
    ) -> Tuple[Sequence[Student], int]:
        """
        Paginated search across admission_number, first_name, last_name.
        Returns (rows, total_count) for a single round-trip count.
        """
        base = (
            select(Student)
            .join(Student.user)
            .where(Student.deleted_at.is_(None))
        )
        if pattern:
            p = f"%{pattern}%"
            filt = or_(
                Student.admission_number.ilike(p),
                User.first_name.ilike(p),
                User.last_name.ilike(p),
            )
            base = base.where(filt)

        total = (
            await self.db.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()

        rows = (
            await self.db.execute(
                base.options(selectinload(Student.user))
                .order_by(Student.admission_number)
                .offset(skip)
                .limit(limit)
            )
        ).scalars().all()

        return rows, total

    async def generate_admission_number(self) -> str:
        """
        Generates the next PSI-{year}-{seq:04d} admission number.
        Queries the DB for the current maximum, then increments by 1.
        The UNIQUE constraint on admission_number is the ultimate safety net
        for concurrent inserts.
        """
        year = datetime.now().year
        prefix = f"PSI-{year}-"

        max_num = (
            await self.db.execute(
                select(func.max(Student.admission_number)).where(
                    Student.admission_number.like(f"{prefix}%")
                )
            )
        ).scalar_one_or_none()

        seq = int(max_num.split("-")[-1]) + 1 if max_num else 1
        return f"{prefix}{seq:04d}"
