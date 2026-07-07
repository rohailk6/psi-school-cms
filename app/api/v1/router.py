from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.students import router as students_router
from app.api.v1.endpoints.teachers import router as teachers_router
from app.api.v1.endpoints.classes import router as classes_router
from app.api.v1.endpoints.subjects import router as subjects_router
from app.api.v1.endpoints.exams import router as exams_router
from app.api.v1.endpoints.exams import marks_router
from app.api.v1.endpoints.academic_years import router as academic_years_router
from app.api.v1.endpoints.roles import router as roles_router
from app.api.v1.endpoints.results import router as results_router
from app.api.v1.endpoints.dashboard import router as dashboard_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(users_router)
api_router.include_router(students_router)
api_router.include_router(teachers_router)
api_router.include_router(classes_router)
api_router.include_router(subjects_router)
api_router.include_router(exams_router)
api_router.include_router(marks_router)
api_router.include_router(academic_years_router)
api_router.include_router(roles_router)
api_router.include_router(results_router)
api_router.include_router(dashboard_router)
