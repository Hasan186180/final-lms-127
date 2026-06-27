from fastapi import FastAPI, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from typing import List, Optional
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
import models
from database import get_db, init_db, hash_password, verify_password
import ai_service

# Load environment variables (.env)
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables on startup
    init_db()
    yield


app = FastAPI(
    title="LMS Yapay Zeka API",
    description="Learning Management System (LMS) AI Services Backend",
    version="1.0.0",
    lifespan=lifespan
)

# ==========================================
# Authentication Endpoints
# ==========================================

@app.post("/register", response_model=models.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: models.UserCreate, db: Session = Depends(get_db)):
    # Check if username or email already exists
    existing_username = db.query(models.User).filter(models.User.username == user.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu kullanıcı adı zaten alınmış."
        )
    
    existing_email = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu e-posta adresi zaten kayıtlı."
        )

    # Hash password and create user
    hashed_pwd = hash_password(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_pwd,
        role=user.role.lower()
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/login", response_model=models.UserResponse)
def login(credentials: models.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == credentials.username).first()
    if not db_user or not verify_password(credentials.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya şifre hatalı."
        )
    return db_user


# ==========================================
# Course & Lesson Management Endpoints
# ==========================================

@app.post("/courses", response_model=models.CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(course: models.CourseCreate, db: Session = Depends(get_db)):
    # Verify teacher exists
    teacher = db.query(models.User).filter(models.User.id == course.teacher_id).first()
    if not teacher or teacher.role != "teacher":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Geçerli bir eğitmen ID'si belirtilmeli."
        )
    
    db_course = models.Course(
        title=course.title,
        description=course.description,
        teacher_id=course.teacher_id
    )
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course


@app.get("/courses", response_model=List[models.CourseResponse])
def get_courses(db: Session = Depends(get_db)):
    return db.query(models.Course).all()


@app.get("/courses/{course_id}", response_model=models.CourseDetailResponse)
def get_course_detail(course_id: int, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kurs bulunamadı."
        )
    return course


@app.post("/courses/{course_id}/lessons", response_model=models.LessonResponse, status_code=status.HTTP_201_CREATED)
def create_lesson(course_id: int, lesson: models.LessonCreate, db: Session = Depends(get_db)):
    course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Kurs bulunamadı."
        )
    
    db_lesson = models.Lesson(
        course_id=course_id,
        title=lesson.title,
        content=lesson.content
    )
    db.add(db_lesson)
    db.commit()
    db.refresh(db_lesson)
    return db_lesson


@app.get("/courses/{course_id}/lessons", response_model=List[models.LessonResponse])
def get_lessons_by_course(course_id: int, db: Session = Depends(get_db)):
    return db.query(models.Lesson).filter(models.Lesson.course_id == course_id).all()


@app.get("/lessons/{lesson_id}", response_model=models.LessonResponse)
def get_lesson(lesson_id: int, db: Session = Depends(get_db)):
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ders bulunamadı."
        )
    return lesson


# ==========================================
# AI Operations Endpoints
# ==========================================

@app.post("/lessons/{lesson_id}/summarize")
def summarize_lesson(
    lesson_id: int, 
    provider: str = "gemini", 
    api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Ders bulunamadı.")
    
    if not api_key or api_key.strip() == "":
        api_key = os.getenv("GEMINI_API_KEY") if provider == "gemini" else os.getenv("GROQ_API_KEY")
        
    summary = ai_service.summarize_content(
        content=lesson.content,
        provider=provider,
        api_key=api_key
    )
    
    # Save the summary to database
    lesson.summary = summary
    db.commit()
    db.refresh(lesson)
    
    return {"summary": summary}


@app.post("/lessons/{lesson_id}/submissions", response_model=models.SubmissionResponse)
def submit_assignment(
    lesson_id: int,
    submission: models.SubmissionCreate,
    api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    # Verify lesson exists
    lesson = db.query(models.Lesson).filter(models.Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Ders bulunamadı.")
    
    # Verify student exists
    student = db.query(models.User).filter(models.User.id == submission.student_id).first()
    if not student or student.role != "student":
        raise HTTPException(status_code=400, detail="Ödev göndermek için geçerli bir öğrenci ID'si girilmelidir.")

    if not api_key or api_key.strip() == "":
        api_key = os.getenv("GEMINI_API_KEY") if submission.provider == "gemini" else os.getenv("GROQ_API_KEY")

    # Call AI service for evaluation
    ai_result = ai_service.analyze_submission(
        lesson_content=lesson.content,
        student_submission=submission.student_text,
        provider=submission.provider,
        api_key=api_key
    )

    db_submission = models.Submission(
        lesson_id=lesson_id,
        student_id=submission.student_id,
        student_text=submission.student_text,
        feedback=ai_result.get("feedback"),
        grade=ai_result.get("grade"),
        provider_used=submission.provider
    )
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    return db_submission


@app.get("/submissions/student/{student_id}", response_model=List[models.SubmissionResponse])
def get_student_submissions(student_id: int, db: Session = Depends(get_db)):
    return db.query(models.Submission).filter(models.Submission.student_id == student_id).all()


@app.get("/submissions/lesson/{lesson_id}", response_model=List[models.SubmissionResponse])
def get_lesson_submissions(lesson_id: int, db: Session = Depends(get_db)):
    return db.query(models.Submission).filter(models.Submission.lesson_id == lesson_id).all()
