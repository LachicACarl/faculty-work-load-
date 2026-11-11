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
    """Aggregate active institutional records and approved workload only."""
    faculty_rows = db.query(Faculty).all()
    section_rows = db.query(Section).all()
    subject_rows = db.query(Subject).all()
    approved = (
        db.query(Allocation)
        .filter(Allocation.approval_status == "approved")
        .all()
    )

    full_time = sum(1 for row in faculty_rows if row.employment_type == "full-time")
    part_time = sum(1 for row in faculty_rows if row.employment_type == "part-time")
    average_match = (
        sum(float(row.match_quality or 0) for row in approved) / len(approved)
        if approved else 0.0
    )
    approved_section_ids = {row.section_id for row in approved}
    total_section_units = sum(
        int(row.subject.units) for row in section_rows if row.subject is not None
    )
    approved_units = sum(
        int(row.section.subject.units)
        for row in approved
        if row.section is not None and row.section.subject is not None
    )
    average_utilization = (
        approved_units / total_section_units * 100
        if total_section_units else 0.0
    )

    return InstitutionalSnapshot(
        total_faculty=len(faculty_rows),
        total_sections=len(section_rows),
        total_subjects=len(subject_rows),
        faculty_full_time=full_time,
        faculty_part_time=part_time,
        avg_specialization_match=average_match,
        total_workload_units=total_section_units,
        avg_utilization=average_utilization,
        timestamp=datetime.utcnow(),
    )
