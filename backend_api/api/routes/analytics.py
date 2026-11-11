"""Database-backed current workload analytics (no fabricated history)."""
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend_api.core.database import get_db
from backend_api.models import Allocation, Faculty
from backend_api.schemas import KPIHistory, KPIDataPoint

router = APIRouter()


@router.get("/kpi-history", response_model=KPIHistory)
def get_kpi_history(db: Session = Depends(get_db)):
    """Return current KPIs from approved allocations; no synthetic history is fabricated."""
    faculty_rows = db.query(Faculty).all()
    allocations = (
        db.query(Allocation)
        .filter(Allocation.approval_status == "approved")
        .all()
    )
    assigned_units = {}
    for row in allocations:
        if row.section is None or row.section.subject is None:
            continue
        assigned_units[row.faculty_id] = (
            assigned_units.get(row.faculty_id, 0) + int(row.section.subject.units)
        )

    utilization_values = [
        (assigned_units.get(faculty.id, 0) / faculty.max_units) * 100
        for faculty in faculty_rows
        if faculty.max_units and faculty.max_units > 0
    ]
    average_utilization = (
        sum(utilization_values) / len(utilization_values)
        if utilization_values else 0.0
    )
    average_match = (
        sum(float(row.match_quality or 0) for row in allocations) / len(allocations)
        if allocations else 0.0
    )
    conflict_count = sum(1 for row in allocations if (row.conflict_score or 0) > 0)
    observed_at = datetime.utcnow().isoformat()

    return KPIHistory(
        kpi_points=[
            KPIDataPoint(timestamp=observed_at, metric_name="faculty_utilization", value=average_utilization),
            KPIDataPoint(timestamp=observed_at, metric_name="avg_match_quality", value=average_match * 100),
            KPIDataPoint(timestamp=observed_at, metric_name="conflict_frequency", value=conflict_count),
        ],
        metric_summary={
            "avg_utilization": average_utilization,
            "avg_match_quality": average_match,
            "total_conflicts": conflict_count,
            "faculty_count": len(faculty_rows),
            "history_available": False,
            "allocation_scope": "approved",
        },
    )


@router.get("/conflict-analysis")
def analyze_conflicts(db: Session = Depends(get_db)):
    """Return recorded conflict flags for approved allocations."""
    allocations = (
        db.query(Allocation)
        .filter(Allocation.approval_status == "approved")
        .all()
    )
    by_faculty = {}
    for row in allocations:
        if (row.conflict_score or 0) <= 0 or row.faculty is None or row.section is None:
            continue
        name = row.faculty.full_name
        by_faculty.setdefault(name, []).append({
            "section": row.section.section_code,
            "conflict_score": row.conflict_score,
            "details": f"Recorded conflict score: {row.conflict_score:.0%}",
        })
    return {
        "total_conflicts": sum(1 for row in allocations if (row.conflict_score or 0) > 0),
        "conflicts_by_faculty": by_faculty,
        "timestamp": datetime.utcnow(),
        "source": "approved_allocation_records",
    }
