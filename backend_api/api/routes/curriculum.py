"""Curriculum (subjects and sections) management endpoints."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend_api.core.database import get_db
from backend_api.models import Subject, Section
from backend_api.schemas import SubjectBase, SubjectResponse, SectionBase, SectionResponse

router = APIRouter()


@router.post("/subjects", response_model=SubjectResponse, status_code=201)
def create_subject(subject: SubjectBase, db: Session = Depends(get_db)):
    """Create a subject from client-supplied fields; database IDs are server-owned."""
    existing = db.query(Subject).filter(Subject.code == subject.code).first()
    if existing:
        raise HTTPException(status_code=409, detail="Subject code already exists.")
    db_subject = Subject(**subject.model_dump())
    db.add(db_subject)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Subject code already exists.")
    db.refresh(db_subject)
    return db_subject


@router.get("/subjects", response_model=List[SubjectResponse])
def list_subjects(db: Session = Depends(get_db)):
    return (
        db.query(Subject)
        .filter(Subject.active.is_(True))
        .order_by(Subject.code.asc())
        .all()
    )


@router.post("/sections", response_model=SectionResponse, status_code=201)
def create_section(section: SectionBase, db: Session = Depends(get_db)):
    """Create a section after validating its subject and schedule."""
    subject = db.query(Subject).filter(
        Subject.id == section.subject_id,
        Subject.active.is_(True),
    ).first()
    if subject is None:
        raise HTTPException(status_code=404, detail="Active subject not found.")
    if section.enrollment < subject.min_class_size or section.enrollment > subject.max_class_size:
        raise HTTPException(
            status_code=422,
            detail="Section enrollment is outside the subject's configured class-size bounds.",
        )
    existing = db.query(Section).filter(
        Section.section_code == section.section_code,
        Section.semester == section.semester,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Section code already exists for this semester.")

    db_section = Section(**section.model_dump())
    db.add(db_section)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Section already exists.")
    db.refresh(db_section)
    return db_section


@router.get("/sections", response_model=List[SectionResponse])
def list_sections(semester: Optional[str] = None, db: Session = Depends(get_db)):
    """List sections, optionally filtered by semester."""
    query = db.query(Section)
    if semester:
        query = query.filter(Section.semester == semester)
    return query.order_by(Section.semester.asc(), Section.section_code.asc()).all()


@router.get("/sections/{section_id}", response_model=SectionResponse)
def get_section(section_id: int, db: Session = Depends(get_db)):
    section = db.query(Section).filter(Section.id == section_id).first()
    if section is None:
        raise HTTPException(status_code=404, detail="Section not found.")
    return section
