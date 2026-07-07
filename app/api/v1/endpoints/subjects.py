from __future__ import annotations
from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import require_admin
from app.schemas.subject import (
    SubjectCreate, SubjectUpdate, SubjectResponse,
    ClassSubjectCreate, ClassSubjectResponse,
)
from app.services import subject_service

router = APIRouter(prefix="/subjects", tags=["Subjects"])


@router.get("/", response_model=List[SubjectResponse])
async def list_subjects(
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    return await subject_service.get_subjects(db)


@router.post("/", response_model=SubjectResponse, status_code=201)
async def create_subject(
    payload: SubjectCreate,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    return await subject_service.create_subject(db, payload)


@router.get("/{subject_id}", response_model=SubjectResponse)
async def get_subject(
    subject_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    return await subject_service.get_subject_by_id(db, subject_id)


@router.patch("/{subject_id}", response_model=SubjectResponse)
async def update_subject(
    subject_id: UUID,
    payload: SubjectUpdate,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    return await subject_service.update_subject(db, subject_id, payload)


@router.delete("/{subject_id}", status_code=204)
async def delete_subject(
    subject_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    await subject_service.delete_subject(db, subject_id)


# ── Assign subject to a class ─────────────────────────────────────────────────

@router.get("/class/{class_id}", response_model=List[ClassSubjectResponse])
async def list_class_subjects(
    class_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    return await subject_service.get_class_subjects(db, class_id)


@router.post("/class/{class_id}", response_model=ClassSubjectResponse, status_code=201)
async def assign_subject_to_class(
    class_id: UUID,
    payload: ClassSubjectCreate,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    return await subject_service.assign_subject_to_class(db, class_id, payload)


@router.delete("/class-subject/{class_subject_id}", status_code=204)
async def remove_class_subject(
    class_subject_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    await subject_service.remove_subject_from_class(db, class_subject_id)