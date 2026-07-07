from __future__ import annotations

from uuid import UUID
from typing import Optional, Sequence

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subject import Subject, ClassSubject
from app.repositories.subject import SubjectRepository, ClassSubjectRepository
from app.schemas.subject import SubjectCreate, SubjectUpdate, ClassSubjectCreate


async def get_subjects(db: AsyncSession) -> Sequence[Subject]:
    repo = SubjectRepository(db)
    return await repo.list_all()


async def get_subject_by_id(db: AsyncSession, subject_id: UUID) -> Subject:
    repo = SubjectRepository(db)
    subject = await repo.get_by_id(subject_id)
    if not subject:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Subject not found")
    return subject


async def create_subject(db: AsyncSession, payload: SubjectCreate) -> Subject:
    repo = SubjectRepository(db)
    if await repo.get_by_code(payload.code):
        raise HTTPException(400, "Subject code already exists")
    subject = Subject(**payload.model_dump())
    await repo.add(subject)
    await db.commit()
    return subject


async def update_subject(
    db: AsyncSession, subject_id: UUID, payload: SubjectUpdate
) -> Subject:
    subject = await get_subject_by_id(db, subject_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(subject, field, value)
    await db.commit()
    return subject


async def delete_subject(db: AsyncSession, subject_id: UUID) -> None:
    repo = SubjectRepository(db)
    subject = await get_subject_by_id(db, subject_id)
    await repo.delete(subject)
    await db.commit()


async def get_class_subjects(
    db: AsyncSession, class_id: UUID, academic_year_id: Optional[UUID] = None
) -> Sequence[ClassSubject]:
    repo = ClassSubjectRepository(db)
    if academic_year_id:
        return await repo.list_by_class_and_year(class_id, academic_year_id)
    return await repo.list_by_class(class_id)


async def assign_subject_to_class(
    db: AsyncSession, class_id: UUID, payload: ClassSubjectCreate
) -> ClassSubject:
    repo = ClassSubjectRepository(db)

    existing = await repo.get_by_class_subject_year(
        class_id, payload.subject_id, payload.academic_year_id
    )
    if existing:
        raise HTTPException(
            400, "Subject already assigned to this class for this academic year"
        )

    cs = ClassSubject(class_id=class_id, **payload.model_dump())
    await repo.add(cs)
    await db.commit()
    return cs


async def remove_subject_from_class(
    db: AsyncSession, class_subject_id: UUID
) -> None:
    repo = ClassSubjectRepository(db)
    cs = await repo.get_by_id(class_subject_id)
    if not cs:
        raise HTTPException(404, "Class subject not found")
    await repo.delete(cs)
    await db.commit()
