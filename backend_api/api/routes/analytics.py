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
    """Return current observed KPIs; historical trend requires dated run records."""
    allocations = db.query(Allocation).all()
    faculty_list = db.query(Faculty).all()

    assigned_units = {}
    for allocation in allocations:
        assigned_units[allocation.faculty_id] = (
            assigned_units.get(allocation.faculty_id, 0)
            + int(allocation.section.subject.units)
        )

    utilization_values = [
        (units / faculty.max_units) * 100
        for faculty in faculty_list
        if faculty.max_units and faculty.max_units > 0
        for units in [assigned_units.get(faculty.id, 0)]
    ]
    avg_utilization = (
        sum(utilization_values) / len(utilization_values)
        if utilization_values else 0.0
    )
    avg_match = (
        sum(item.match_quality for item in allocations) / len(allocations)
        if allocations else 0.0
    )
    conflict_count = sum(1 for item in allocations if (item.conflict_score or 0) > 0)

    now = datetime.utcnow().isoformat()
    points = [
        KPIDataPoint(timestamp=now, metric_name="faculty_utilization", value=avg_utilization),
        KPIDataPoint(timestamp=now, metric_name="avg_match_quality", value=avg_match * 100),
        KPIDataPoint(timestamp=now, metric_name="conflict_frequency", value=conflict_count),
    ]

    return KPIHistory(
        kpi_points=points,
        metric_summary={
            "avg_utilization": avg_utilization,
            "avg_match_quality": avg_match,
            "total_conflicts": conflict_count,
            "faculty_count": len(faculty_list),
            "history_available": False,
        },
    )


@router.get("/conflict-analysis")
def analyze_conflicts(db: Session = Depends(get_db)):
    """Return recorded conflict flags for the current allocation set."""
    allocations = db.query(Allocation).all()
    conflicts_by_faculty = {}
    for allocation in allocations:
        if (allocation.conflict_score or 0) > 0:
            faculty_name = allocation.faculty.full_name
            conflicts_by_faculty.setdefault(faculty_name, []).append({
                "section": allocation.section.section_code,
                "conflict_score": allocation.conflict_score,
                "details": f"Recorded conflict score: {allocation.conflict_score:.0%}",
            })

    return {
        "total_conflicts": sum(1 for item in allocations if (item.conflict_score or 0) > 0),
        "conflicts_by_faculty": conflicts_by_faculty,
        "timestamp": datetime.utcnow(),
        "source": "allocation_records",
    }
