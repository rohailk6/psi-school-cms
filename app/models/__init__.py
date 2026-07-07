# Import order matters here — SQLAlchemy needs to see all models
# before it can resolve foreign key relationships between them.
# If you add a new model file, add its import here.

from app.models.base import BaseModel
from app.models.user import (
    User,
    Role,
    Permission,
    RolePermission,
    UserRoleAssignment,
    RefreshToken,
)
from app.models.school import AcademicYear
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.class_ import Class, Section, StudentEnrollment
from app.models.subject import Subject, ClassSubject, TeacherAssignment
from app.models.exam import Exam, ExamSubject, Mark
