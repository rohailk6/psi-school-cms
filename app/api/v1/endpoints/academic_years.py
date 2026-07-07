from __future__ import annotations

from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import require_permission
from app.services import academic_year_service

router = APIRouter(prefix="/academic-years", tags=["Academic Years"])


class AcademicYearCreate(BaseModel):
    name: str        # e.g. "2025-2026"
    start_date: date
    end_date: date


class AcademicYearUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class AcademicYearResponse(BaseModel):
    id: UUID
    name: str
    start_date: date
    end_date: date
    is_active: bool

    model_config = {"from_attributes": True}


@router.get("/", response_model=List[AcademicYearResponse])
async def list_academic_years(
    db: AsyncSession = Depends(get_db),
    _=require_permission("academic_years:read"),
):
    return await academic_year_service.list_academic_years(db)


@router.post("/", response_model=AcademicYearResponse, status_code=201)
async def create_academic_year(
    payload: AcademicYearCreate,
    db: AsyncSession = Depends(get_db),
    _=require_permission("academic_years:write"),
):
    return await academic_year_service.create_academic_year(db, payload)


@router.get("/{year_id}", response_model=AcademicYearResponse)
async def get_academic_year(
    year_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_permission("academic_years:read"),
):
    return await academic_year_service.get_academic_year_by_id(db, year_id)


@router.patch("/{year_id}", response_model=AcademicYearResponse)
async def update_academic_year(
    year_id: UUID,
    payload: AcademicYearUpdate,
    db: AsyncSession = Depends(get_db),
    _=require_permission("academic_years:write"),
):
    return await academic_year_service.update_academic_year(db, year_id, payload)


@router.delete("/{year_id}", status_code=204)
async def delete_academic_year(
    year_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_permission("academic_years:delete"),
):
    await academic_year_service.delete_academic_year(db, year_id)


@router.post("/{year_id}/activate", response_model=AcademicYearResponse)
async def activate_academic_year(
    year_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=require_permission("academic_years:write"),
):
    """Set this as the active academic year. All others are deactivated atomically."""
    return await academic_year_service.activate_academic_year(db, year_id)
