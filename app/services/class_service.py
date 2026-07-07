from __future__ import annotations

from uuid import UUID
from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.class_ import Class, Section, StudentEnrollment
from app.repositories.class_ import ClassRepository, SectionRepository, EnrollmentRepository
from app.schemas.class_ import ClassCreate, ClassUpdate, SectionCreate, SectionUpdate


async def get_classes(db: AsyncSession) -> Sequence[Class]:
    repo = ClassRepository(db)
    return await repo.list_with_sections()


async def get_class_by_id(db: AsyncSession, class_id: UUID) -> Class:
    repo = ClassRepository(db)
    cls = await repo.get_by_id_with_sections(class_id)
    if not cls:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Class not found")
    return cls


async def create_class(db: AsyncSession, payload: ClassCreate) -> Class:
    repo = ClassRepository(db)
    cls = Class(**payload.model_dump())
    await repo.add(cls)
    await db.commit()
    return await repo.get_by_id_with_sections(cls.id)


async def update_class(db: AsyncSession, class_id: UUID, payload: ClassUpdate) -> Class:
    repo = ClassRepository(db)
    cls = await get_class_by_id(db, class_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(cls, field, value)
    await db.commit()
    return await repo.get_by_id_with_sections(class_id)


async def delete_class(db: AsyncSession, class_id: UUID) -> None:
    repo = ClassRepository(db)
    cls = await get_class_by_id(db, class_id)
    await repo.delete(cls)
    await db.commit()


async def get_sections_by_class(db: AsyncSession, class_id: UUID) -> Sequence[Section]:
    repo = SectionRepository(db)
    return await repo.list_by_class(class_id)


async def get_section_by_id(db: AsyncSession, section_id: UUID) -> Section:
    repo = SectionRepository(db)
    section = await repo.get_by_id(section_id)
    if not section:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Section not found")
    return section


async def create_section(db: AsyncSession, class_id: UUID, payload: SectionCreate) -> Section:
    repo = SectionRepository(db)
    section = Section(class_id=class_id, **payload.model_dump())
    await repo.add(section)
    await db.commit()
    return section


async def update_section(
    db: AsyncSession, section_id: UUID, payload: SectionUpdate
) -> Section:
    section = await get_section_by_id(db, section_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(section, field, value)
    await db.commit()
    return section


async def delete_section(db: AsyncSession, section_id: UUID) -> None:
    repo = SectionRepository(db)
    section = await get_section_by_id(db, section_id)
    await repo.delete(section)
    await db.commit()


async def get_section_students(
    db: AsyncSession, section_id: UUID
) -> Sequence[StudentEnrollment]:
    repo = EnrollmentRepository(db)
    return await repo.list_active_by_section(section_id)
