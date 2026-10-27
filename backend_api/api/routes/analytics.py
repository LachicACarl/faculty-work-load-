"""Analytics and KPI endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from backend_api.core.database import get_db
from backend_api.models import Allocation, Faculty, Section, Subject
from backend_api.schemas import KPIHistory, KPIDataPoint

router = APIRouter()


@router.get("/kpi-history", response_model=KPIHistory)
def get_kpi_history(db: Session = Depends(get_db)):
    """Return current database aggregates; historical observations are not stored."""
    allocations = db.query(Allocation).all()
    faculty_list = db.query(Faculty).all()

    assigned_units_by_faculty = {faculty.id: 0 for faculty in faculty_list}
    for allocation in allocations:
        faculty_id = allocation.faculty_id
        if faculty_id in assigned_units_by_faculty:
            assigned_units_by_faculty[faculty_id] += (getattr(getattr(allocation.section, "subject", None), "units", None) or 0)

    utilization_values = [
        assigned_units_by_faculty[faculty.id] / (faculty.max_units or 1) * 100
        for faculty in faculty_list
        if (faculty.max_units or 0) > 0
    ]
    avg_utilization = (
        sum(utilization_values) / len(utilization_values)
        if utilization_values else 0.0
    )
    avg_match_quality = (
        sum(allocation.match_quality or 0.0 for allocation in allocations) / len(allocations)
        if allocations else 0.0
    )
    total_conflicts = sum(
        1 for allocation in allocations if (allocation.conflict_score or 0) > 0
    )

    return KPIHistory(
        kpi_points=[],
        metric_summary={
            "data_source": "current_database_aggregates",
            "avg_utilization": avg_utilization,
            "avg_match_quality": avg_match_quality,
            "total_conflicts": total_conflicts,
            "faculty_count": len(faculty_list),
            "allocation_count": len(allocations),
        },
    )
@router.get("/conflict-analysis")
def analyze_conflicts(db: Session = Depends(get_db)):
    """Analyze conflicts in current allocations."""
    allocations = db.query(Allocation).all()
    
    conflicts_by_faculty = {}
    for alloc in allocations:
        if (alloc.conflict_score or 0) > 0:
            fac_name = getattr(alloc.faculty, "full_name", None) or "Unknown faculty"
            if fac_name not in conflicts_by_faculty:
                conflicts_by_faculty[fac_name] = []
            conflicts_by_faculty[fac_name].append({
                "section": getattr(alloc.section, "section_code", None),
                "conflict_score": alloc.conflict_score or 0.0,
                "details": f"Conflict: {(alloc.conflict_score or 0.0):.0%} severity"
            })
    
    return {
        "total_conflicts": sum(1 for a in allocations if (a.conflict_score or 0) > 0),
        "conflicts_by_faculty": conflicts_by_faculty,
        "timestamp": datetime.utcnow()
    }
