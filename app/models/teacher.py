from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import Date, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Teacher(BaseModel):
    """
    Profile data specific to teaching staff.

    Like Student, Teacher is a profile table — the User row holds
    identity (name, email, phone, is_active). This table holds
    school-employment-specific fields that have no meaning for
    non-teacher users.

    KEY CHANGES from old model:
    • full_name REMOVED — name lives on User.first_name + User.last_name.
      Storing it here was a sync hazard: if a teacher legally changes their
      name, you'd have to update two rows or get stale data in reports.
    • phone REMOVED — lives on User.phone (same reason).
    • is_active REMOVED — use deleted_at soft delete (same pattern as User).
      This preserves historical data: a deleted teacher's assignments and
      mark entries still reference a valid row.
    • qualification ADDED — e.g. "B.Ed", "M.Sc Mathematics"
    • joining_date ADDED — needed for seniority, payroll reports
    • deleted_at ADDED — soft delete (set on termination/resignation)
    """
    __tablename__ = "teachers"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        # unique=True enforces one-to-one: one user → one teacher profile
    )
    employee_id: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True
        # e.g. "PSI-TCH-001" — assigned by admin at hiring, never changes
    )
    qualification: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
        # e.g. "B.Ed", "M.Sc Mathematics, B.Ed"
    )
    specialization: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
        # e.g. "Mathematics", "English Literature"
    )
    joining_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True
        # when they joined the school — used for seniority and HR reports
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
        # soft delete — set on resignation/termination, never hard-delete
        # so historical assignments and mark entries stay intact
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="teacher")
    assignments: Mapped[List["TeacherAssignment"]] = relationship(
        back_populates="teacher"
    )
