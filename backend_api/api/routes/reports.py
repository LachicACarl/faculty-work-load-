"""Reports and export endpoints."""
import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend_api.core.database import get_db
from backend_api.models import Allocation, Faculty
from backend_api.schemas import WorkloadSummaryRow

router = APIRouter()


def _build_workload_summary(db: Session):
    faculty_rows = db.query(Faculty).order_by(Faculty.full_name.asc()).all()
    allocations = (
        db.query(Allocation)
        .filter(Allocation.approval_status == "approved")
        .all()
    )
    by_faculty = {faculty.id: [] for faculty in faculty_rows}
    for allocation in allocations:
        if allocation.faculty_id in by_faculty:
            by_faculty[allocation.faculty_id].append(allocation)

    summary = []
    for faculty in faculty_rows:
        faculty_allocations = by_faculty[faculty.id]
        assigned_units = sum(
            int(item.section.subject.units)
            for item in faculty_allocations
            if item.section is not None and item.section.subject is not None
        )
        max_units = int(faculty.max_units or 0)
        utilization = (assigned_units / max_units * 100) if max_units > 0 else 0.0
        matches = [float(item.match_quality or 0) for item in faculty_allocations]
        conflicts = sum(1 for item in faculty_allocations if (item.conflict_score or 0) > 0)
        summary.append(
            WorkloadSummaryRow(
                faculty_name=faculty.full_name,
                employment_type=faculty.employment_type,
                assigned_units=assigned_units,
                max_units=max_units,
                utilization_percent=utilization,
                num_sections=len(faculty_allocations),
                avg_match_quality=sum(matches) / len(matches) if matches else 0.0,
                conflicts=conflicts,
            )
        )
    return summary


@router.get("/workload-summary.csv")
def export_workload_summary(db: Session = Depends(get_db)):
    """Export approved allocations only; proposals are not counted as active workload."""
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow([
        "Faculty Name", "Employment Type", "Approved Assigned Units", "Max Units",
        "Utilization %", "Approved Sections", "Avg Match Quality", "Recorded Conflicts",
    ])
    for row in _build_workload_summary(db):
        writer.writerow([
            row.faculty_name,
            row.employment_type,
            row.assigned_units,
            row.max_units,
            f"{row.utilization_percent:.1f}%",
            row.num_sections,
            f"{row.avg_match_quality:.3f}",
            row.conflicts,
        ])
    payload = output.getvalue()
    output.close()
    return StreamingResponse(
        iter([payload]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="workload_summary.csv"'},
    )


@router.get("/workload-summary")
def get_workload_summary(db: Session = Depends(get_db)):
    """Return a summary of approved workload allocations."""
    return _build_workload_summary(db)
