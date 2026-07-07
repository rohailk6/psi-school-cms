from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, SmallInteger, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Subject(BaseModel):
    """
    A subject that can be taught — e.g. Mathematics, English, Physics.

    Subjects are global and reusable: the same 'Mathematics' subject
    is assigned to Grade 5, Grade 6, Grade 7, etc. via class_subjects.

    This avoids duplicating subjects per class or per year. If you
    rename a subject, it updates everywhere automatically.
    """
    __tablename__ = "subjects"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    # e.g. "MATH-01", "ENG-01" — used in report cards and APIs
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    class_subjects: Mapped[List["ClassSubject"]] = relationship(
        back_populates="subject"
    )
    teacher_assignments: Mapped[List["TeacherAssignment"]] = relationship(
        back_populates="subject"
    )
    exam_subjects: Mapped[List["ExamSubject"]] = relationship(
        back_populates="subject"
    )


class ClassSubject(BaseModel):
    """
    Assigns a subject to a class for a specific academic year.

    This is the per-year scoping mechanism.

    Example: 'Mathematics' is assigned to 'Grade 5' for '2024-2025'.
    Next year, a new ClassSubject row is created for '2025-2026'.
    The Subject row itself never changes.

    is_elective: when True, not all students in the class take this
    subject — individual enrollment logic handles optional subjects.

    Why no max_marks or pass_marks here?
    Those belong on ExamSubject, not ClassSubject. Different exams
    for the same class+subject can have different mark distributions
    (e.g., Mid-Term out of 50, Final out of 100).
    """
    __tablename__ = "class_subjects"

    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classes.id", ondelete="CASCADE"),
        nullable=False,
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id"),
        nullable=False,
    )
    is_elective: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    __table_args__ = (
        UniqueConstraint(
            "class_id", "subject_id", "academic_year_id",
            name="uq_class_subject_year",
            # a subject can only be assigned to a class once per year
        ),
    )

    # Relationships
    class_: Mapped["Class"] = relationship(back_populates="class_subjects")
    subject: Mapped["Subject"] = relationship(back_populates="class_subjects")
    academic_year: Mapped["AcademicYear"] = relationship(back_populates="class_subjects")


class TeacherAssignment(BaseModel):
    """
    Assigns a teacher to teach a subject in a class (optionally scoped
    to one section) for a specific academic year.

    Rules enforced here:
    • One teacher per class+section+subject per year (UNIQUE constraint)
    • section_id can be NULL meaning the teacher covers ALL sections
      (e.g. a specialist or part-time teacher)
    • is_class_teacher=True means this teacher is the homeroom/form teacher
      for that section — at most one per section per year (enforced in service)

    Why is this separate from ClassSubject?
    A teacher assignment is an employment/scheduling record.
    A class-subject assignment is a curriculum record.
    They change at different times and for different reasons.
    """
    __tablename__ = "teacher_assignments"

    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("teachers.id"),
        # will reference 'teacher_profiles' once teacher model is renamed
        nullable=False,
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classes.id"),
        nullable=False,
    )
    section_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sections.id"),
        nullable=True,
        # NULL = teaches this subject across all sections of the class
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id"),
        nullable=False,
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id"),
        nullable=False,
    )
    is_class_teacher: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
        # homeroom/form teacher flag — at most one per section per year
    )

    __table_args__ = (
        UniqueConstraint(
            "class_id", "section_id", "subject_id", "academic_year_id",
            name="uq_teacher_assignment",
            # prevents two teachers being assigned the same class+section+subject+year
        ),
    )

    # Relationships
    teacher: Mapped["Teacher"] = relationship(back_populates="assignments")
    class_: Mapped["Class"] = relationship(back_populates="teacher_assignments")
    section: Mapped[Optional["Section"]] = relationship(back_populates="teacher_assignments")
    subject: Mapped["Subject"] = relationship(back_populates="teacher_assignments")
    academic_year: Mapped["AcademicYear"] = relationship(back_populates="teacher_assignments")
