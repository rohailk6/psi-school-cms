from __future__ import annotations

from datetime import date as date_type, datetime, timezone
from uuid import UUID
from typing import List, Optional, Sequence, Tuple

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.student import Student
from app.models.class_ import StudentEnrollment
from app.repositories.student import StudentRepository
from app.repositories.class_ import SectionRepository, EnrollmentRepository
from app.schemas.student import StudentCreate, StudentUpdate, EnrollStudentRequest
from app.core.security import hash_password

_USER_FIELDS = {"first_name", "last_name"}


async def get_students(
    db: AsyncSession, skip: int = 0, limit: int = 20, search: Optional[str] = None
) -> Tuple[Sequence[Student], int]:
    repo = StudentRepository(db)
    return await repo.search(search, skip, limit)


async def get_student_by_id(db: AsyncSession, student_id: UUID) -> Student:
    repo = StudentRepository(db)
    student = await repo.get_active_by_id(student_id)
    if not student:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Student not found")
    return student


async def create_student(db: AsyncSession, payload: StudentCreate) -> Student:
    repo = StudentRepository(db)

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        first_name=payload.first_name,
        last_name=payload.last_name,
        is_active=True,
    )
    await repo.add(user)  # flush → user.id is now populated

    admission_number = await repo.generate_admission_number()
    student = Student(
        user_id=user.id,
        admission_number=admission_number,
        date_of_birth=payload.date_of_birth,
        gender=payload.gender,
        guardian_name=payload.guardian_name,
        guardian_phone=payload.guardian_phone,
        guardian_email=payload.guardian_email,
        address=payload.address,
    )
    await repo.add(student)
    await db.commit()

    return await repo.get_active_by_id(student.id)


async def update_student(db: AsyncSession, student_id: UUID, payload: StudentUpdate) -> Student:
    repo = StudentRepository(db)
    student = await get_student_by_id(db, student_id)
    updates = payload.model_dump(exclude_unset=True)

    for field, value in updates.items():
        if field in _USER_FIELDS:
            setattr(student.user, field, value)
        else:
            setattr(student, field, value)

    await db.commit()
    return await repo.get_active_by_id(student_id)


async def delete_student(db: AsyncSession, student_id: UUID) -> None:
    student = await get_student_by_id(db, student_id)
    student.deleted_at = datetime.now(timezone.utc)
    student.user.is_active = False
    await db.commit()


async def enroll_student(
    db: AsyncSession, student_id: UUID, payload: EnrollStudentRequest
) -> StudentEnrollment:
    section_repo = SectionRepository(db)
    enrollment_repo = EnrollmentRepository(db)

    section = await section_repo.get_by_id(payload.section_id)
    if not section:
        raise HTTPException(404, "Section not found")

    existing = await enrollment_repo.get_by_student_and_year(
        student_id, payload.academic_year_id
    )
    if existing:
        raise HTTPException(400, "Student already enrolled for this academic year")

    enrollment = StudentEnrollment(
        student_id=student_id,
        class_id=payload.class_id,
        section_id=payload.section_id,
        academic_year_id=payload.academic_year_id,
        enrollment_date=payload.enrollment_date or date_type.today(),
        status="active",
    )
    await enrollment_repo.add(enrollment)
    await db.commit()
    return enrollment


async def get_student_enrollments(
    db: AsyncSession, student_id: UUID
) -> Sequence[StudentEnrollment]:
    repo = EnrollmentRepository(db)
    return await repo.list_by_student(student_id)
