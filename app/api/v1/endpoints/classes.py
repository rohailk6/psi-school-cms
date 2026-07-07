from __future__ import annotations
from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import require_admin
from app.schemas.class_ import (
    ClassCreate, ClassUpdate, ClassResponse,
    SectionCreate, SectionUpdate, SectionResponse,
)
from app.schemas.student import EnrollmentResponse
from app.services import class_service

router = APIRouter(prefix="/classes", tags=["Classes & Sections"])


# ── Classes ───────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[ClassResponse])
async def list_classes(
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    return await class_service.get_classes(db)


@router.post("/", response_model=ClassResponse, status_code=201)
async def create_class(
    payload: ClassCreate,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    return await class_service.create_class(db, payload)


@router.get("/{class_id}", response_model=ClassResponse)
async def get_class(
    class_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    return await class_service.get_class_by_id(db, class_id)


@router.patch("/{class_id}", response_model=ClassResponse)
async def update_class(
    class_id: UUID,
    payload: ClassUpdate,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    return await class_service.update_class(db, class_id, payload)


@router.delete("/{class_id}", status_code=204)
async def delete_class(
    class_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    await class_service.delete_class(db, class_id)


# ── Sections ──────────────────────────────────────────────────────────────────

@router.get("/{class_id}/sections", response_model=List[SectionResponse])
async def list_sections(
    class_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    return await class_service.get_sections_by_class(db, class_id)


@router.post("/{class_id}/sections", response_model=SectionResponse, status_code=201)
async def create_section(
    class_id: UUID,
    payload: SectionCreate,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    return await class_service.create_section(db, class_id, payload)


@router.patch("/sections/{section_id}", response_model=SectionResponse)
async def update_section(
    section_id: UUID,
    payload: SectionUpdate,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    return await class_service.update_section(db, section_id, payload)


@router.delete("/sections/{section_id}", status_code=204)
async def delete_section(
    section_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    await class_service.delete_section(db, section_id)


@router.get("/sections/{section_id}/students", response_model=List[EnrollmentResponse])
async def get_section_students(
    section_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_admin,
):
    """List all currently enrolled students in a section."""
    return await class_service.get_section_students(db, section_id)