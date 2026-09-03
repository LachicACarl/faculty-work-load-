"""Faculty management endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend_api.core.database import get_db
from backend_api.models import Faculty, Qualification, Availability
from backend_api.schemas import FacultyCreate, FacultyResponse, FacultyList

router = APIRouter()


@router.post("/", response_model=FacultyResponse)
def create_faculty(faculty: FacultyCreate, db: Session = Depends(get_db)):
    """Create a new faculty member."""
    db_faculty = Faculty(
        employee_id=faculty.employee_id,
        full_name=faculty.full_name,
        employment_type=faculty.employment_type,
        tenure_status=faculty.tenure_status,
        max_units=faculty.max_units,
        overload_allowed=faculty.overload_allowed,
        available=faculty.available
    )
    
    # Add qualifications
    for qual in faculty.qualifications or []:
        db_qual = Qualification(
            degree=qual.degree,
            specialization=qual.specialization,
            institution=qual.institution,
            year_awarded=qual.year_awarded,
            proficiency_level=qual.proficiency_level
        )
        db_faculty.qualifications.append(db_qual)
    
    # Add availability
    for avail in faculty.availability or []:
        db_avail = Availability(
            day_of_week=avail.day_of_week,
            start_time=avail.start_time,
            end_time=avail.end_time,
            recurring=avail.recurring
        )
        db_faculty.availability.append(db_avail)
    
    db.add(db_faculty)
    db.commit()
    db.refresh(db_faculty)
    
    return db_faculty


@router.get("/", response_model=List[FacultyList])
def list_faculty(db: Session = Depends(get_db)):
    """List all faculty members."""
    faculty = db.query(Faculty).all()
    return faculty


@router.get("/{faculty_id}", response_model=FacultyResponse)
def get_faculty(faculty_id: int, db: Session = Depends(get_db)):
    """Get faculty details."""
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")
    return faculty


@router.put("/{faculty_id}", response_model=FacultyResponse)
def update_faculty(faculty_id: int, faculty: FacultyCreate, db: Session = Depends(get_db)):
    """Update faculty information."""
    db_faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not db_faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")
    
    db_faculty.full_name = faculty.full_name
    db_faculty.employment_type = faculty.employment_type
    db_faculty.tenure_status = faculty.tenure_status
    db_faculty.max_units = faculty.max_units
    db_faculty.overload_allowed = faculty.overload_allowed
    db_faculty.available = faculty.available
    
    db.commit()
    db.refresh(db_faculty)
    
    return db_faculty


@router.delete("/{faculty_id}")
def delete_faculty(faculty_id: int, db: Session = Depends(get_db)):
    """Delete faculty member."""
    db_faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not db_faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")
    
    db.delete(db_faculty)
    db.commit()
    
    return {"message": "Faculty deleted"}
