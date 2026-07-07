from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import Date, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Student(BaseModel):
    """
    Profile data specific to students.

    The User row holds credentials and personal identity (name, email).
    This table holds school-specific fields: admission number, guardian
    info, date of birth, etc.

    One-to-one with User: every student user has exactly one student profile,
    created automatically when the user is assigned the 'student' role.
    """
    __tablename__ = "student_profiles"
    # Renamed from "students" to match architecture (student_profiles table)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        # unique=True enforces the one-to-one relationship at DB level
    )

    admission_number: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        unique=True,
        # format: "PSI-2024-0001" — set by the service layer, not the user
    )

    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Guardian info lives here (not a separate Parent user account)
    # Architecture decision: parent is NOT a system user in this MVP
    guardian_name: Mapped[str] = mapped_column(String(200), nullable=False)
    guardian_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    guardian_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
        # soft delete — preserves FK references in enrollments and marks
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="student")
    enrollments: Mapped[List["StudentEnrollment"]] = relationship(
        back_populates="student"
    )
    marks: Mapped[List["Mark"]] = relationship(back_populates="student")
