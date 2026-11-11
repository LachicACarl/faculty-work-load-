"""Institutional data and workload snapshots."""
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend_api.core.database import get_db
from backend_api.models import Allocation, Faculty, Section, Subject
from backend_api.schemas import InstitutionalSnapshot

router = APIRouter()


@router.get("/snapshot", response_model=InstitutionalSnapshot)
def get_institutional_snapshot(db: Session = Depends(get_db)):
    """Aggregate current database records without using subject catalog totals as workload."""
    faculty_list = db.query(Faculty).all()
    sections_list = db.query(Section).all()
    subjects_list = db.query(Subject).all()
    allocations = db.query(Allocation).all()

    full_time = sum(1 for item in faculty_list if item.employment_type == "full-time")
    part_time = sum(1 for item in faculty_list if item.employment_type == "part-time")
    avg_match = (
        sum(item.match_quality for item in allocations) / len(allocations)
        if allocations else 0.0
    )

    assigned_section_ids = {
        item.section_id for item in allocations if item.approval_status != "flagged"
    }
    assigned_units = sum(
        item.subject.units for item in sections_list if item.id in assigned_section_ids
    )
    total_section_units = sum(item.subject.units for item in sections_list)
    utilization = (
        (assigned_units / total_section_units) * 100
        if total_section_units else 0.0
    )

    return InstitutionalSnapshot(
        total_faculty=len(faculty_list),
        total_sections=len(sections_list),
        total_subjects=len(subjects_list),
        faculty_full_time=full_time,
        faculty_part_time=part_time,
        avg_specialization_match=avg_match,
        total_workload_units=total_section_units,
        avg_utilization=utilization,
        timestamp=datetime.utcnow(),
    )
