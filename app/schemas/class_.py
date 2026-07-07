from __future__ import annotations
from uuid import UUID
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel


class SectionCreate(BaseModel):
    name: str
    capacity: Optional[int] = 40


class SectionUpdate(BaseModel):
    name: Optional[str] = None
    capacity: Optional[int] = None


class SectionResponse(BaseModel):
    id: UUID
    class_id: UUID
    name: str
    capacity: int

    model_config = {"from_attributes": True}


class ClassCreate(BaseModel):
    name: str
    numeric_level: int
    description: Optional[str] = None


class ClassUpdate(BaseModel):
    name: Optional[str] = None
    numeric_level: Optional[int] = None
    description: Optional[str] = None


class ClassResponse(BaseModel):
    id: UUID
    name: str
    numeric_level: int
    description: Optional[str] = None
    created_at: datetime
    sections: List[SectionResponse] = []

    model_config = {"from_attributes": True}


class EnrollmentCreate(BaseModel):
    student_id: UUID
    class_id: UUID
    section_id: UUID
    academic_year_id: UUID
    enrollment_date: date


class EnrollmentStatusUpdate(BaseModel):
    status: str
    # values: active | transferred | graduated | withdrawn


class EnrollmentResponse(BaseModel):
    id: UUID
    student_id: UUID
    class_id: UUID
    section_id: UUID
    academic_year_id: UUID
    enrollment_date: date
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
