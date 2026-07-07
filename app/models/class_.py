from __future__ import annotations

import uuid
from datetime import date
from typing import List, Optional

from sqlalchemy import CheckConstraint, Date, ForeignKey, Integer, SmallInteger, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Class(BaseModel):
    """
    A grade level that persists across academic years.
    e.g. 'Grade 5', 'Grade 10', 'O-Level'.

    KEY CHANGE from old design: Class is no longer tied to a session.

    Old design: Class was recreated every year (Grade 5 in 2024, Grade 5 in 2025
    were two separate rows). This caused FK headaches and data duplication.

    New design: Class is a permanent entity. The per-year scoping is done
    by class_subjects (which subjects this class has THIS year) and
    student_enrollments (which students are IN this class THIS year).

    numeric_level is unique — no two classes can be at the same grade level.
    It's used for promotion logic and sorting.
    """
    __tablename__ = "classes"

    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    # e.g. "Grade 5" — human-readable label

    numeric_level: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        unique=True,
        # e.g. 5 — used for sorting and promotion (Grade 5 → Grade 6)
    )

    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    sections: Mapped[List["Section"]] = relationship(
        back_populates="class_", cascade="all, delete-orphan"
    )
    class_subjects: Mapped[List["ClassSubject"]] = relationship(
        back_populates="class_"
    )
    enrollments: Mapped[List["StudentEnrollment"]] = relationship(
        back_populates="class_"
    )
    teacher_assignments: Mapped[List["TeacherAssignment"]] = relationship(
        back_populates="class_"
    )
    exams: Mapped[List["Exam"]] = relationship(back_populates="class_")


class Section(BaseModel):
    """
    A division within a class — e.g. Grade 5A, Grade 5B, Grade 5C.

    Students are enrolled in a section, not directly in a class.
    This allows one class to have multiple groups of students, each
    potentially with a different class teacher.

    Section name is unique within a class (you can't have two 'A' sections
    in Grade 5) but the same letter can exist across classes (Grade 5A and
    Grade 6A are different sections).
    """
    __tablename__ = "sections"

    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(10), nullable=False)
    # e.g. "A", "B", "C"

    capacity: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=40,
        # service layer checks this before enrolling a new student
    )

    __table_args__ = (
        UniqueConstraint("class_id", "name", name="uq_section_class_name"),
        # Grade 5 can only have one section named "A"
    )

    # Relationships
    class_: Mapped["Class"] = relationship(back_populates="sections")
    enrollments: Mapped[List["StudentEnrollment"]] = relationship(
        back_populates="section"
    )
    teacher_assignments: Mapped[List["TeacherAssignment"]] = relationship(
        back_populates="section"
    )


class StudentEnrollment(BaseModel):
    """
    Links a student to a class+section for one academic year.

    A student can only be enrolled once per academic year (UNIQUE constraint).
    Their enrollment status tracks what happened: active, transferred,
    graduated, or withdrawn.

    Why store class_id here in addition to section_id?
    Convenience for queries — you can filter enrollments by class without
    joining through sections. section.class_id would work but adds a join.

    Why enrollment_date as a Date (not DateTime)?
    For school purposes, the day is what matters — time of day is irrelevant.
    """
    __tablename__ = "student_enrollments"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id"),
        nullable=False,
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classes.id"),
        nullable=False,
    )
    section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sections.id"),
        nullable=False,
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id"),
        nullable=False,
    )
    enrollment_date: Mapped[date] = mapped_column(
        Date, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active"
        # values: active | transferred | graduated | withdrawn
    )

    __table_args__ = (
        UniqueConstraint(
            "student_id", "academic_year_id",
            name="uq_enrollment_student_year",
            # one active enrollment per student per year
        ),
        CheckConstraint(
            "status IN ('active', 'transferred', 'graduated', 'withdrawn')",
            name="ck_enrollment_status",
        ),
    )

    # Relationships
    student: Mapped["Student"] = relationship(back_populates="enrollments")
    class_: Mapped["Class"] = relationship(back_populates="enrollments")
    section: Mapped["Section"] = relationship(back_populates="enrollments")
    academic_year: Mapped["AcademicYear"] = relationship(back_populates="enrollments")
