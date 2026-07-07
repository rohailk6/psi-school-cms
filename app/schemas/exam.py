from __future__ import annotations
from uuid import UUID
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel


class ExamCreate(BaseModel):
    academic_year_id: UUID
    class_id: UUID
    name: str
    start_date: date
    end_date: date


class ExamUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None


class ExamResponse(BaseModel):
    id: UUID
    academic_year_id: UUID
    class_id: UUID
    name: str
    start_date: date
    end_date: date
    status: str
    created_by: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ExamSubjectCreate(BaseModel):
    subject_id: UUID
    max_marks: float
    passing_marks: float
    exam_date: Optional[date] = None
    duration_mins: Optional[int] = None


class ExamSubjectResponse(BaseModel):
    id: UUID
    exam_id: UUID
    subject_id: UUID
    max_marks: float
    passing_marks: float
    exam_date: Optional[date] = None
    duration_mins: Optional[int] = None

    model_config = {"from_attributes": True}


class MarkUpdate(BaseModel):
    obtained_marks: Optional[float] = None
    is_absent: bool = False
    remarks: Optional[str] = None


class MarkEntry(BaseModel):
    student_id: UUID
    obtained_marks: Optional[float] = None
    is_absent: bool = False
    remarks: Optional[str] = None


class MarkEntryRequest(BaseModel):
    entries: List[MarkEntry]


class MarkResponse(BaseModel):
    id: UUID
    exam_subject_id: UUID
    student_id: UUID
    obtained_marks: Optional[float] = None
    is_absent: bool
    remarks: Optional[str] = None
    entered_by: Optional[UUID] = None

    model_config = {"from_attributes": True}
