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
    """Get KPI metrics history."""
    allocations = db.query(Allocation).all()
    faculty_list = db.query(Faculty).all()
    
    kpi_points = []
    
    # Faculty utilization KPI
    now = datetime.utcnow()
    for i in range(7):
        date = (now - timedelta(days=6-i)).strftime("%Y-%m-%d")
        kpi_points.append(KPIDataPoint(
            timestamp=date,
            metric_name="faculty_utilization",
            value=85 + (i * 2) % 10  # Mock data
        ))
    
    # Match quality KPI
    for i in range(7):
        date = (now - timedelta(days=6-i)).strftime("%Y-%m-%d")
        avg_match = (sum(a.match_quality for a in allocations) / len(allocations)
                    if allocations else 0)
        kpi_points.append(KPIDataPoint(
            timestamp=date,
            metric_name="avg_match_quality",
            value=avg_match * 100
        ))
    
    # Conflict frequency KPI
    for i in range(7):
        date = (now - timedelta(days=6-i)).strftime("%Y-%m-%d")
        conflict_count = sum(1 for a in allocations if a.conflict_score > 0)
        kpi_points.append(KPIDataPoint(
            timestamp=date,
            metric_name="conflict_frequency",
            value=conflict_count
        ))
    
    metric_summary = {
        "avg_utilization": 87.5,
        "avg_match_quality": 0.91,
        "total_conflicts": sum(1 for a in allocations if a.conflict_score > 0),
        "faculty_count": len(faculty_list)
    }
    
    return KPIHistory(
        kpi_points=kpi_points,
        metric_summary=metric_summary
    )


@router.get("/conflict-analysis")
def analyze_conflicts(db: Session = Depends(get_db)):
    """Analyze conflicts in current allocations."""
    allocations = db.query(Allocation).all()
    
    conflicts_by_faculty = {}
    for alloc in allocations:
        if alloc.conflict_score > 0:
            fac_name = alloc.faculty.full_name
            if fac_name not in conflicts_by_faculty:
                conflicts_by_faculty[fac_name] = []
            conflicts_by_faculty[fac_name].append({
                "section": alloc.section.section_code,
                "conflict_score": alloc.conflict_score,
                "details": f"Conflict: {alloc.conflict_score:.0%} severity"
            })
    
    return {
        "total_conflicts": sum(1 for a in allocations if a.conflict_score > 0),
        "conflicts_by_faculty": conflicts_by_faculty,
        "timestamp": datetime.utcnow()
    }
