from __future__ import annotations
from uuid import UUID
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr


class TeacherUserInfo(BaseModel):
    """
    Subset of User fields embedded in teacher responses.
    Avoids requiring a second API call just to get the teacher's name.
    """
    id: UUID
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    is_active: bool

    model_config = {"from_attributes": True}


class TeacherCreate(BaseModel):
    """
    Creating a teacher creates both a User account and a Teacher profile.
    name/email/phone go to the User row; everything else to Teacher.
    """
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    employee_id: str
    qualification: Optional[str] = None
    specialization: Optional[str] = None
    joining_date: Optional[date] = None


class TeacherUpdate(BaseModel):
    """
    Updating a teacher may touch both the User row and the Teacher row.
    The service routes each field to the right table.
    """
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    qualification: Optional[str] = None
    specialization: Optional[str] = None
    joining_date: Optional[date] = None


class TeacherResponse(BaseModel):
    id: UUID
    user_id: UUID
    user: TeacherUserInfo
    # ^ embedded — always loaded via selectinload, so always present
    employee_id: str
    qualification: Optional[str] = None
    specialization: Optional[str] = None
    joining_date: Optional[date] = None
    deleted_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AssignTeacherRequest(BaseModel):
    class_id: UUID
    section_id: Optional[UUID] = None  # None = all sections
    subject_id: UUID
    academic_year_id: UUID
    is_class_teacher: bool = False


class TeacherAssignmentResponse(BaseModel):
    id: UUID
    teacher_id: UUID
    class_id: UUID
    section_id: Optional[UUID] = None
    subject_id: UUID
    academic_year_id: UUID
    is_class_teacher: bool

    model_config = {"from_attributes": True}


class PaginatedTeachers(BaseModel):
    total: int
    skip: int
    limit: int
    data: List[TeacherResponse]
