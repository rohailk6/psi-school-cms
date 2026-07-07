from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    CheckConstraint, Date, DateTime, ForeignKey,
    Numeric, SmallInteger, String, Text, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Exam(BaseModel):
    """
    An examination event for a specific class in an academic year.
    e.g. 'Mid-Term 2024', 'Final Exam 2024' for Grade 5.

    STATUS STATE MACHINE (replaces old is_locked + is_published booleans):

        draft → published → ongoing → completed
                               ↘ cancelled (from any state)

    Why a state machine instead of two booleans?
    The old design had 4 boolean combinations, but only 3 were valid:
      (locked=False, published=False) = draft
      (locked=True,  published=False) = ???  impossible state
      (locked=True,  published=True)  = published
      (locked=False, published=True)  = ???  another impossible state

    A single status string makes the state machine explicit and prevents
    impossible combinations at the DB level via CHECK constraint.

    class_id: An exam belongs to one class. If you need to run the same
    exam across multiple classes, each class gets its own Exam row —
    because marks are per-student and each class has different students.
    """
    __tablename__ = "exams"

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id"),
        nullable=False,
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("classes.id"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # e.g. "Mid-Term Examination 2024"

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="draft"
        # values: draft | published | ongoing | completed | cancelled
    )

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
        # which admin/teacher created this exam
    )

    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_exam_dates"),
        CheckConstraint(
            "status IN ('draft', 'published', 'ongoing', 'completed', 'cancelled')",
            name="ck_exam_status",
        ),
    )

    # Relationships
    academic_year: Mapped["AcademicYear"] = relationship(back_populates="exams")
    class_: Mapped["Class"] = relationship(back_populates="exams")
    exam_subjects: Mapped[List["ExamSubject"]] = relationship(
        back_populates="exam",
        cascade="all, delete-orphan",
    )


class ExamSubject(BaseModel):
    """
    Configures one subject within an exam — its date, duration, and mark limits.

    KEY CHANGE: references subject_id directly (not class_subject_id).

    Old approach referenced class_subject_id, which is already scoped to
    (class + subject + academic_year). But that made queries awkward:
    to know 'which subject is this?', you had to join through class_subjects.

    New approach: store subject_id directly. The implicit scoping comes from
    the parent Exam already carrying class_id + academic_year_id.

    max_marks / passing_marks live HERE (not on ClassSubject) because:
    • Mid-Term might be out of 50, Final out of 100 for the same subject
    • The check constraint guarantees passing_marks ≤ max_marks at DB level
    """
    __tablename__ = "exam_subjects"

    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
    )
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id"),
        nullable=False,
    )
    max_marks: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    passing_marks: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    exam_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    duration_mins: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)

    __table_args__ = (
        UniqueConstraint("exam_id", "subject_id", name="uq_exam_subject"),
        CheckConstraint(
            "passing_marks <= max_marks AND max_marks > 0",
            name="ck_exam_subject_marks",
        ),
    )

    # Relationships
    exam: Mapped["Exam"] = relationship(back_populates="exam_subjects")
    subject: Mapped["Subject"] = relationship(back_populates="exam_subjects")
    marks: Mapped[List["Mark"]] = relationship(
        back_populates="exam_subject",
        cascade="all, delete-orphan",
    )


class Mark(BaseModel):
    """
    The actual marks a student scored in one ExamSubject.
    Table name: 'marks' (renamed from 'exam_results').

    KEY CHANGES:
    • obtained_marks renamed from marks_obtained (clearer)
    • grade column REMOVED — grades are computed not stored.
      Storing a computed grade creates a sync hazard: if grade boundaries
      change (principal adjusts the grading scale), stored grades go stale.
      Instead, the API computes grade from obtained_marks/max_marks at
      query time or generates a report card on-the-fly.
    • is_published REMOVED — the Exam.status field covers this at the
      exam level. Individual mark-level publishing is over-engineering
      for a school this size.
    • remarks added — teacher notes about the student's performance.

    The CHECK constraint ensures marks and absence are consistent:
    • A present student must have a numeric mark
    • An absent student must NOT have a mark
    This prevents the data inconsistency of is_absent=True with obtained_marks=85.
    """
    __tablename__ = "marks"

    exam_subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exam_subjects.id", ondelete="CASCADE"),
        nullable=False,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("student_profiles.id"),
        nullable=False,
    )
    obtained_marks: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        # NULL when is_absent=True — enforced by CHECK constraint below
    )
    is_absent: Mapped[bool] = mapped_column(nullable=False, default=False)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    entered_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
        # set when marks are edited after initial entry
    )

    __table_args__ = (
        UniqueConstraint("exam_subject_id", "student_id", name="uq_mark_exam_student"),
        CheckConstraint(
            # exactly one of: (absent with no marks) OR (present with marks)
            "(is_absent = TRUE AND obtained_marks IS NULL) OR "
            "(is_absent = FALSE AND obtained_marks IS NOT NULL)",
            name="ck_mark_consistency",
        ),
    )

    # Relationships
    exam_subject: Mapped["ExamSubject"] = relationship(back_populates="marks")
    student: Mapped["Student"] = relationship(back_populates="marks")
