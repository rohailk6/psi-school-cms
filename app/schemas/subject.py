from __future__ import annotations
from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class SubjectCreate(BaseModel):
    name: str
    code: str
    description: Optional[str] = None


class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None


class SubjectResponse(BaseModel):
    id: UUID
    name: str
    code: str
    description: Optional[str] = None

    model_config = {"from_attributes": True}


class ClassSubjectCreate(BaseModel):
    subject_id: UUID
    academic_year_id: UUID
    is_elective: bool = False


class ClassSubjectResponse(BaseModel):
    id: UUID
    class_id: UUID
    subject_id: UUID
    academic_year_id: UUID
    is_elective: bool

    model_config = {"from_attributes": True}


class TeacherAssignmentCreate(BaseModel):
    teacher_id: UUID
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
    created_at: datetime

    model_config = {"from_attributes": True}
