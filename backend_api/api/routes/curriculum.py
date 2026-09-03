"""Curriculum (subjects and sections) management endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend_api.core.database import get_db
from backend_api.models import Subject, Section
from backend_api.schemas import SubjectResponse, SectionResponse

router = APIRouter()


@router.post("/subjects", response_model=SubjectResponse)
def create_subject(subject: SubjectResponse, db: Session = Depends(get_db)):
    """Create a new subject."""
    db_subject = Subject(
        code=subject.code,
        name=subject.name,
        units=subject.units,
        required_specialization=subject.required_specialization,
        min_class_size=subject.min_class_size,
        max_class_size=subject.max_class_size,
        active=subject.active
    )
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject


@router.get("/subjects", response_model=List[SubjectResponse])
def list_subjects(db: Session = Depends(get_db)):
    """List all subjects."""
    subjects = db.query(Subject).filter(Subject.active == True).all()
    return subjects


@router.post("/sections", response_model=SectionResponse)
def create_section(section: SectionResponse, db: Session = Depends(get_db)):
    """Create a new section."""
    db_section = Section(
        subject_id=section.subject_id,
        section_code=section.section_code,
        semester=section.semester,
        schedule_day=section.schedule_day,
        schedule_start_time=section.schedule_start_time,
        schedule_end_time=section.schedule_end_time,
        room=section.room,
        enrollment=section.enrollment,
        assigned=section.assigned
    )
    db.add(db_section)
    db.commit()
    db.refresh(db_section)
    return db_section


@router.get("/sections", response_model=List[SectionResponse])
def list_sections(semester: str = None, db: Session = Depends(get_db)):
    """List sections, optionally filtered by semester."""
    query = db.query(Section)
    if semester:
        query = query.filter(Section.semester == semester)
    sections = query.all()
    return sections


@router.get("/sections/{section_id}", response_model=SectionResponse)
def get_section(section_id: int, db: Session = Depends(get_db)):
    """Get section details."""
    section = db.query(Section).filter(Section.id == section_id).first()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")
    return section
