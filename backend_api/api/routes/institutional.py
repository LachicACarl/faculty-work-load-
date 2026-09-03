"""Institutional data and snapshots."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from backend_api.core.database import get_db
from backend_api.models import Faculty, Section, Subject, Allocation
from backend_api.schemas import InstitutionalSnapshot

router = APIRouter()


@router.get("/snapshot", response_model=InstitutionalSnapshot)
def get_institutional_snapshot(db: Session = Depends(get_db)):
    """Get institutional snapshot with key metrics."""
    faculty_list = db.query(Faculty).all()
    sections_list = db.query(Section).all()
    subjects_list = db.query(Subject).all()
    allocations = db.query(Allocation).all()
    
    ft_count = sum(1 for f in faculty_list if f.employment_type == "full-time")
    pt_count = sum(1 for f in faculty_list if f.employment_type == "part-time")
    
    avg_match = (sum(a.match_quality for a in allocations) / len(allocations)
                if allocations else 0)
    
    total_units = sum(s.units for s in subjects_list)
    assigned_units = sum(s.subject.units for s in sections_list if s.assigned)
    avg_util = (assigned_units / total_units * 100) if total_units > 0 else 0
    
    return InstitutionalSnapshot(
        total_faculty=len(faculty_list),
        total_sections=len(sections_list),
        total_subjects=len(subjects_list),
        faculty_full_time=ft_count,
        faculty_part_time=pt_count,
        avg_specialization_match=avg_match,
        total_workload_units=total_units,
        avg_utilization=avg_util,
        timestamp=datetime.utcnow()
    )
