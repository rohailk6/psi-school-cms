from __future__ import annotations

from typing import Sequence
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.school import AcademicYear
from app.repositories.school import AcademicYearRepository


async def list_academic_years(db: AsyncSession) -> Sequence[AcademicYear]:
    repo = AcademicYearRepository(db)
    return await repo.list_all()


async def get_academic_year_by_id(db: AsyncSession, year_id: UUID) -> AcademicYear:
    repo = AcademicYearRepository(db)
    year = await repo.get_by_id(year_id)
    if not year:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Academic year not found")
    return year


async def create_academic_year(db: AsyncSession, payload) -> AcademicYear:
    repo = AcademicYearRepository(db)
    if await repo.get_by_name(payload.name):
        raise HTTPException(400, f"Academic year '{payload.name}' already exists")
    year = AcademicYear(**payload.model_dump())
    await repo.add(year)
    await db.commit()
    return year


async def update_academic_year(db: AsyncSession, year_id: UUID, payload) -> AcademicYear:
    year = await get_academic_year_by_id(db, year_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(year, field, value)
    await db.commit()
    return year


async def delete_academic_year(db: AsyncSession, year_id: UUID) -> None:
    year = await get_academic_year_by_id(db, year_id)
    if year.is_active:
        raise HTTPException(400, "Cannot delete the currently active academic year")
    await db.delete(year)
    await db.commit()


async def activate_academic_year(db: AsyncSession, year_id: UUID) -> AcademicYear:
    """
    Sets one academic year as active and deactivates all others atomically.

    Why bulk-update instead of loading each row?
    We don't know how many years exist. A single UPDATE ... WHERE is one
    SQL statement regardless of row count — safer and faster.
    """
    year = await get_academic_year_by_id(db, year_id)

    # Clear all active flags in one UPDATE
    await db.execute(
        update(AcademicYear).values(is_active=False)
    )
    # Set the target year active
    year.is_active = True
    await db.commit()
    return year
