from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship, declarative_base
from pydantic import BaseModel, EmailStr

Base = declarative_base()

# ==========================================
# SQLAlchemy Database Models
# ==========================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="student")  # "student" or "teacher"

    courses = relationship("Course", back_populates="teacher", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="student", cascade="all, delete-orphan")


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    teacher_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    teacher = relationship("User", back_populates="courses")
    lessons = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)

    course = relationship("Course", back_populates="lessons")
    submissions = relationship("Submission", back_populates="lesson", cascade="all, delete-orphan")


class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    student_text = Column(Text, nullable=False)
    feedback = Column(Text, nullable=True)
    grade = Column(Integer, nullable=True)
    provider_used = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    lesson = relationship("Lesson", back_populates="submissions")
    student = relationship("User", back_populates="submissions")


# ==========================================
# Pydantic Schemas for FastAPI API Request/Response validation
# ==========================================

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str  # "student" or "teacher"

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    role: str

    class Config:
        from_attributes = True


class CourseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    teacher_id: int

class CourseResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    teacher_id: int

    class Config:
        from_attributes = True


class LessonCreate(BaseModel):
    title: str
    content: str

class LessonResponse(BaseModel):
    id: int
    course_id: int
    title: str
    content: str
    summary: Optional[str] = None

    class Config:
        from_attributes = True


class SubmissionCreate(BaseModel):
    student_id: int
    student_text: str
    provider: Optional[str] = "gemini"  # "gemini" or "groq"

class SubmissionResponse(BaseModel):
    id: int
    lesson_id: int
    student_id: int
    student_text: str
    feedback: Optional[str] = None
    grade: Optional[int] = None
    provider_used: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Detailed response schemas including nested models
class LessonDetailResponse(LessonResponse):
    course: CourseResponse

    class Config:
        from_attributes = True

class CourseDetailResponse(CourseResponse):
    lessons: List[LessonResponse] = []

    class Config:
        from_attributes = True
