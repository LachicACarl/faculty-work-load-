"""Faculty management endpoints."""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from backend_api.core.database import get_db
from backend_api.models import Faculty, Qualification, Availability
from backend_api.schemas import FacultyCreate, FacultyResponse, FacultyList

router = APIRouter()


@router.post("/", response_model=FacultyResponse, status_code=status.HTTP_201_CREATED)
def create_faculty(faculty: FacultyCreate, db: Session = Depends(get_db)):
    """Create faculty with related qualification and availability records."""
    duplicate = db.query(Faculty.id).filter(
        Faculty.employee_id == faculty.employee_id
    ).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="Employee ID already exists.")

    db_faculty = Faculty(
        employee_id=faculty.employee_id,
        full_name=faculty.full_name,
        employment_type=faculty.employment_type,
        tenure_status=faculty.tenure_status,
        max_units=faculty.max_units,
        overload_allowed=faculty.overload_allowed,
        available=faculty.available,
    )
    db_faculty.qualifications = [
        Qualification(**item.model_dump()) for item in faculty.qualifications
    ]
    db_faculty.availability = [
        Availability(**item.model_dump()) for item in faculty.availability
    ]
    db.add(db_faculty)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Employee ID already exists.")
    db.refresh(db_faculty)
    return db.query(Faculty).options(
        selectinload(Faculty.qualifications),
        selectinload(Faculty.availability),
    ).filter(Faculty.id == db_faculty.id).one()


@router.get("/", response_model=List[FacultyList])
def list_faculty(db: Session = Depends(get_db)):
    return db.query(Faculty).order_by(Faculty.full_name.asc()).all()


@router.get("/{faculty_id}", response_model=FacultyResponse)
def get_faculty(faculty_id: int, db: Session = Depends(get_db)):
    faculty = db.query(Faculty).options(
        selectinload(Faculty.qualifications),
        selectinload(Faculty.availability),
    ).filter(Faculty.id == faculty_id).first()
    if faculty is None:
        raise HTTPException(status_code=404, detail="Faculty not found.")
    return faculty


@router.put("/{faculty_id}", response_model=FacultyResponse)
def update_faculty(faculty_id: int, faculty: FacultyCreate, db: Session = Depends(get_db)):
    db_faculty = db.query(Faculty).options(
        selectinload(Faculty.qualifications),
        selectinload(Faculty.availability),
    ).filter(Faculty.id == faculty_id).first()
    if db_faculty is None:
        raise HTTPException(status_code=404, detail="Faculty not found.")

    duplicate = db.query(Faculty.id).filter(
        Faculty.employee_id == faculty.employee_id,
        Faculty.id != faculty_id,
    ).first()
    if duplicate:
        raise HTTPException(status_code=409, detail="Employee ID already exists.")

    db_faculty.employee_id = faculty.employee_id
    db_faculty.full_name = faculty.full_name
    db_faculty.employment_type = faculty.employment_type
    db_faculty.tenure_status = faculty.tenure_status
    db_faculty.max_units = faculty.max_units
    db_faculty.overload_allowed = faculty.overload_allowed
    db_faculty.available = faculty.available
    db_faculty.qualifications = [
        Qualification(**item.model_dump()) for item in faculty.qualifications
    ]
    db_faculty.availability = [
        Availability(**item.model_dump()) for item in faculty.availability
    ]

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Faculty record conflicts with an existing employee ID.")
    db.refresh(db_faculty)
    return db_faculty


@router.delete("/{faculty_id}", status_code=status.HTTP_200_OK)
def delete_faculty(faculty_id: int, db: Session = Depends(get_db)):
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if faculty is None:
        raise HTTPException(status_code=404, detail="Faculty not found.")
    if faculty.allocations:
        raise HTTPException(
            status_code=409,
            detail="Faculty with existing allocation history cannot be deleted. Mark the record unavailable instead.",
        )
    db.delete(faculty)
    db.commit()
    return {"message": "Faculty deleted."}
