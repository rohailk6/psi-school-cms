from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.school import AcademicYear
from app.repositories.base import BaseRepository


class AcademicYearRepository(BaseRepository[AcademicYear]):
    model = AcademicYear

    async def get_by_name(self, name: str) -> Optional[AcademicYear]:
        result = await self.db.execute(
            select(AcademicYear).where(AcademicYear.name == name)
        )
        return result.scalar_one_or_none()

    async def get_active(self) -> Optional[AcademicYear]:
        """Returns the single currently active academic year, or None."""
        result = await self.db.execute(
            select(AcademicYear).where(AcademicYear.is_active.is_(True))
        )
        return result.scalar_one_or_none()

    async def list_all(self, offset: int = 0, limit: int = 100) -> Sequence[AcademicYear]:
        result = await self.db.execute(
            select(AcademicYear)
            .order_by(AcademicYear.start_date.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()
