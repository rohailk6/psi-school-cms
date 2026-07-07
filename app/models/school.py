from __future__ import annotations

from datetime import date
from typing import List

from sqlalchemy import Boolean, CheckConstraint, Date, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class AcademicYear(BaseModel):
    """
    Represents one school year, e.g. '2024-2025'.

    Why is this a DB entity and not just a config value?
    Because every piece of transactional data — enrollments, teacher
    assignments, class-subject mappings, exams — must be scoped to a
    specific year. Hard-coding the year would make historical data
    impossible to query correctly.

    Only one year can be is_active=True at a time. The service layer
    enforces this with an atomic swap (set new active, clear old active
    in a single transaction).
    """
    __tablename__ = "academic_years"

    name: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    # e.g. "2024-2025"
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        UniqueConstraint("name", name="uq_academic_year_name"),
        CheckConstraint("end_date > start_date", name="ck_academic_year_dates"),
        # DB-level guard so no migration can ever create an invalid year
    )

    # Relationships — these are convenience navigations, not load triggers
    class_subjects: Mapped[List["ClassSubject"]] = relationship(
        back_populates="academic_year"
    )
    enrollments: Mapped[List["StudentEnrollment"]] = relationship(
        back_populates="academic_year"
    )
    teacher_assignments: Mapped[List["TeacherAssignment"]] = relationship(
        back_populates="academic_year"
    )
    exams: Mapped[List["Exam"]] = relationship(back_populates="academic_year")
