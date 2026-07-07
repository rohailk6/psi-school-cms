from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID
from typing import List, Sequence, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.teacher import Teacher
from app.models.subject import TeacherAssignment
from app.repositories.teacher import TeacherRepository
from app.repositories.subject import TeacherAssignmentRepository
from app.schemas.teacher import TeacherCreate, TeacherUpdate, AssignTeacherRequest
from app.core.security import hash_password

_USER_FIELDS = {"first_name", "last_name", "phone"}


async def get_teachers(
    db: AsyncSession, skip: int = 0, limit: int = 20, search: Optional[str] = None
) -> Tuple[Sequence[Teacher], int]:
    repo = TeacherRepository(db)
    return await repo.search(search, skip, limit)


async def get_teacher_by_id(db: AsyncSession, teacher_id: UUID) -> Teacher:
    repo = TeacherRepository(db)
    teacher = await repo.get_active_by_id(teacher_id)
    if not teacher:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Teacher not found")
    return teacher


async def create_teacher(db: AsyncSession, payload: TeacherCreate) -> Teacher:
    repo = TeacherRepository(db)

    if await repo.get_by_employee_id(payload.employee_id):
        raise HTTPException(400, "Employee ID already exists")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone=payload.phone,
        is_active=True,
    )
    await repo.add(user)  # flush → user.id populated

    teacher = Teacher(
        user_id=user.id,
        employee_id=payload.employee_id,
        qualification=payload.qualification,
        specialization=payload.specialization,
        joining_date=payload.joining_date,
    )
    await repo.add(teacher)
    await db.commit()

    return await repo.get_active_by_id(teacher.id)


async def update_teacher(db: AsyncSession, teacher_id: UUID, payload: TeacherUpdate) -> Teacher:
    repo = TeacherRepository(db)
    teacher = await get_teacher_by_id(db, teacher_id)
    updates = payload.model_dump(exclude_unset=True)

    for field, value in updates.items():
        if field in _USER_FIELDS:
            setattr(teacher.user, field, value)
        else:
            setattr(teacher, field, value)

    await db.commit()
    return await repo.get_active_by_id(teacher_id)


async def delete_teacher(db: AsyncSession, teacher_id: UUID) -> None:
    teacher = await get_teacher_by_id(db, teacher_id)
    teacher.deleted_at = datetime.now(timezone.utc)
    teacher.user.is_active = False
    await db.commit()


async def assign_teacher(
    db: AsyncSession, teacher_id: UUID, payload: AssignTeacherRequest
) -> TeacherAssignment:
    assignment_repo = TeacherAssignmentRepository(db)

    existing = await assignment_repo.get_existing(
        teacher_id=teacher_id,
        class_id=payload.class_id,
        section_id=payload.section_id,
        subject_id=payload.subject_id,
        academic_year_id=payload.academic_year_id,
    )
    if existing:
        raise HTTPException(400, "Teacher already assigned to this class/section/subject/year")

    assignment = TeacherAssignment(
        teacher_id=teacher_id,
        class_id=payload.class_id,
        section_id=payload.section_id,
        subject_id=payload.subject_id,
        academic_year_id=payload.academic_year_id,
        is_class_teacher=payload.is_class_teacher,
    )
    await assignment_repo.add(assignment)
    await db.commit()
    return assignment


async def get_teacher_assignments(
    db: AsyncSession, teacher_id: UUID
) -> Sequence[TeacherAssignment]:
    repo = TeacherAssignmentRepository(db)
    return await repo.list_by_teacher(teacher_id)
