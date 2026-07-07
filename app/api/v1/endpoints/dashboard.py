from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    """
    Summary counts for the main dashboard.
    Accessible to any authenticated user (teachers/admins both see the landing page).
    """
    return await dashboard_service.get_stats(db)
