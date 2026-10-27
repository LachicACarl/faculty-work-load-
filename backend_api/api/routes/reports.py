"""Reports and export endpoints."""
from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session
import csv
import io

from backend_api.core.database import get_db
from backend_api.models import Allocation, Faculty
from backend_api.schemas import WorkloadSummaryRow

router = APIRouter()


@router.get("/workload-summary.csv")
def export_workload_summary(db: Session = Depends(get_db)):
    """Export workload summary as CSV."""
    allocations = db.query(Allocation).all()
    faculty_list = db.query(Faculty).all()
    
    # Calculate workload per faculty
    workload_data = {}
    for fac in faculty_list:
        workload_data[fac.id] = {
            "faculty_name": fac.full_name,
            "employment_type": fac.employment_type,
            "assigned_units": 0,
            "max_units": fac.max_units,
            "num_sections": 0,
            "match_qualities": []
        }
    
    for alloc in allocations:
        fac_id = alloc.faculty_id
        if fac_id in workload_data:
            workload_data[fac_id]["assigned_units"] += (getattr(getattr(alloc.section, "subject", None), "units", None) or 0)
            workload_data[fac_id]["num_sections"] += 1
            workload_data[fac_id]["match_qualities"].append(alloc.match_quality or 0.0)
    
    # Generate CSV content
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        "Faculty Name", "Employment Type", "Assigned Units", "Max Units",
        "Utilization %", "Sections", "Avg Match Quality", "Conflicts"
    ])
    
    for fac_id, data in workload_data.items():
        util_pct = (data["assigned_units"] / data["max_units"] * 100) if (data["max_units"] or 0) > 0 else 0
        avg_match = sum(data["match_qualities"]) / len(data["match_qualities"]) if data["match_qualities"] else 0
        conflicts = sum(1 for a in allocations if a.faculty_id == fac_id and (a.conflict_score or 0) > 0)
        
        writer.writerow([
            data["faculty_name"],
            data["employment_type"],
            data["assigned_units"],
            data["max_units"],
            f"{util_pct:.1f}%",
            data["num_sections"],
            f"{avg_match:.2f}",
            conflicts
        ])
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="workload_summary.csv"'},
    )


@router.get("/workload-summary")
def get_workload_summary(db: Session = Depends(get_db)):
    """Get workload summary as JSON."""
    allocations = db.query(Allocation).all()
    faculty_list = db.query(Faculty).all()
    
    summary = []
    
    for fac in faculty_list:
        fac_allocs = [a for a in allocations if a.faculty_id == fac.id]
        assigned_units = sum((getattr(getattr(a.section, "subject", None), "units", None) or 0) for a in fac_allocs)
        util_pct = (assigned_units / fac.max_units * 100) if (fac.max_units or 0) > 0 else 0
        avg_match = (sum((a.match_quality or 0.0) for a in fac_allocs) / len(fac_allocs)
                    if fac_allocs else 0)
        conflicts = sum(1 for a in fac_allocs if (a.conflict_score or 0) > 0)
        
        summary.append(WorkloadSummaryRow(
            faculty_name=fac.full_name,
            employment_type=fac.employment_type,
            assigned_units=assigned_units,
            max_units=fac.max_units if fac.max_units is not None else 0,
            utilization_percent=util_pct,
            num_sections=len(fac_allocs),
            avg_match_quality=avg_match,
            conflicts=conflicts
        ))
    
    return summary
