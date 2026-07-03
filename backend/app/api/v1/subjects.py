from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.deps import get_db, get_current_user, require_role
from app.models.models import Subject, User
from app.schemas.schemas import SubjectCreate, SubjectUpdate, SubjectResponse

router = APIRouter()

@router.post("/", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
def create_subject(
    subject: SubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "teacher"]))
):
    """
    Create a new subject (Admin and Teacher only)
    """
    # Check if subject code already exists
    existing = db.query(Subject).filter(Subject.code == subject.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Subject with code {subject.code} already exists"
        )
    
    # Check if subject name already exists
    existing_name = db.query(Subject).filter(Subject.name == subject.name).first()
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Subject with name {subject.name} already exists"
        )
    
    db_subject = Subject(
        **subject.dict(),
        creator_id=current_user.id
    )
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject


@router.get("/", response_model=List[SubjectResponse])
def get_subjects(
    skip: int = 0,
    limit: int = 100,
    department: str = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all subjects with optional filtering
    """
    query = db.query(Subject)
    
    if active_only:
        query = query.filter(Subject.is_active == True)
    
    if department:
        query = query.filter(Subject.department == department)
    
    subjects = query.offset(skip).limit(limit).all()
    return subjects


@router.get("/{subject_id}", response_model=SubjectResponse)
def get_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific subject by ID
    """
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    return subject


@router.put("/{subject_id}", response_model=SubjectResponse)
def update_subject(
    subject_id: int,
    subject_update: SubjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "teacher"]))
):
    """
    Update a subject (Admin and Teacher only)
    """
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Check permissions (creator or admin)
    if current_user.role != "admin" and subject.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this subject"
        )
    
    # Check for duplicate code if updating
    if subject_update.code and subject_update.code != subject.code:
        existing = db.query(Subject).filter(Subject.code == subject_update.code).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subject with code {subject_update.code} already exists"
            )
    
    # Update fields
    update_data = subject_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(subject, field, value)
    
    db.commit()
    db.refresh(subject)
    return subject


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    """
    Delete a subject (Admin only)
    """
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Soft delete (deactivate)
    subject.is_active = False
    db.commit()
    return None


@router.get("/{subject_id}/statistics")
def get_subject_statistics(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get statistics for a subject
    """
    from app.models.models import Quiz, QuestionBank
    
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    total_quizzes = db.query(Quiz).filter(Quiz.subject_id == subject_id).count()
    active_quizzes = db.query(Quiz).filter(
        Quiz.subject_id == subject_id,
        Quiz.is_active == True
    ).count()
    
    total_questions = db.query(QuestionBank).filter(
        QuestionBank.subject_id == subject_id
    ).count()
    
    return {
        "subject_id": subject_id,
        "subject_name": subject.name,
        "subject_code": subject.code,
        "total_quizzes": total_quizzes,
        "active_quizzes": active_quizzes,
        "total_questions_in_bank": total_questions
    }
