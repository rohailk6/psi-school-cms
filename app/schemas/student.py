from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


class StudentCreate(BaseModel):
    """
    Creating a student also creates their User account.
    The service layer auto-generates the admission_number.
    Guardian info is required — there is no separate Parent user account.
    """
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    guardian_name: str
    guardian_phone: str
    guardian_email: Optional[str] = None
    address: Optional[str] = None


class StudentUpdate(BaseModel):
    """All fields optional — send only what needs updating."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    guardian_email: Optional[str] = None
    address: Optional[str] = None


class StudentUserInfo(BaseModel):
    """Subset of User fields embedded in student responses."""
    id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    is_active: bool

    model_config = {"from_attributes": True}


class StudentResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    user: StudentUserInfo
    admission_number: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    guardian_name: str
    guardian_phone: str
    guardian_email: Optional[str] = None
    address: Optional[str] = None
    deleted_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EnrollStudentRequest(BaseModel):
    class_id: uuid.UUID
    section_id: uuid.UUID
    academic_year_id: uuid.UUID
    enrollment_date: Optional[date] = None  # defaults to today if not provided


class EnrollmentResponse(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    class_id: uuid.UUID
    section_id: uuid.UUID
    academic_year_id: uuid.UUID
    enrollment_date: date
    status: str

    model_config = {"from_attributes": True}


class PaginatedStudents(BaseModel):
    total: int
    skip: int
    limit: int
    data: List[StudentResponse]
