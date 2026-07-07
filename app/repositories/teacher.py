from __future__ import annotations

from typing import Optional, Sequence, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.teacher import Teacher
from app.models.user import User
from app.repositories.base import BaseRepository


class TeacherRepository(BaseRepository[Teacher]):
    model = Teacher

    async def get_active_by_id(self, teacher_id) -> Optional[Teacher]:
        """Returns a non-deleted teacher with User loaded, or None."""
        result = await self.db.execute(
            select(Teacher)
            .join(Teacher.user)
            .options(selectinload(Teacher.user))
            .where(Teacher.id == teacher_id, Teacher.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_employee_id(self, employee_id: str) -> Optional[Teacher]:
        result = await self.db.execute(
            select(Teacher).where(Teacher.employee_id == employee_id)
        )
        return result.scalar_one_or_none()

    async def search(
        self, pattern: Optional[str], skip: int, limit: int
    ) -> Tuple[Sequence[Teacher], int]:
        """
        Paginated search across first_name, last_name, employee_id.
        Only returns non-deleted teachers.
        """
        base = (
            select(Teacher)
            .join(Teacher.user)
            .where(Teacher.deleted_at.is_(None))
        )
        if pattern:
            p = f"%{pattern}%"
            filt = or_(
                User.first_name.ilike(p),
                User.last_name.ilike(p),
                Teacher.employee_id.ilike(p),
            )
            base = base.where(filt)

        total = (
            await self.db.execute(select(func.count()).select_from(base.subquery()))
        ).scalar_one()

        rows = (
            await self.db.execute(
                base.options(selectinload(Teacher.user))
                .order_by(User.last_name, User.first_name)
                .offset(skip)
                .limit(limit)
            )
        ).scalars().all()

        return rows, total
