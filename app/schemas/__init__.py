from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest, TokenData
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.schemas.student import StudentCreate, StudentResponse
from app.schemas.teacher import TeacherCreate, TeacherResponse, TeacherUpdate
from app.schemas.class_ import ClassCreate, ClassResponse, SectionCreate, SectionResponse
from app.schemas.subject import SubjectCreate, SubjectResponse, ClassSubjectCreate
from app.schemas.exam import ExamCreate, ExamResponse, ExamSubjectCreate, MarkEntryRequest, MarkResponse