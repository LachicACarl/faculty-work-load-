from csv import DictWriter
from io import StringIO

from fastapi import APIRouter, Response

from backend_api.api.runtime_state import get_latest_workload_run, get_workload_run_history, summarize_runs

router = APIRouter()


@router.get("/workload-summary")
def workload_summary() -> dict[str, object]:
    runs = get_workload_run_history()
    return {
        "summary": summarize_runs(runs),
        "latest_run": get_latest_workload_run(),
        "recent_runs": runs[:5],
    }


@router.get("/workload-summary.csv")
def workload_summary_csv() -> Response:
    runs = get_workload_run_history()
    buffer = StringIO()
    writer = DictWriter(
        buffer,
        fieldnames=[
            "timestamp",
            "policy_profile",
            "score",
            "fitness",
            "conflicts",
            "utilization_rate",
            "assigned_sections",
            "total_sections",
            "faculty_count",
            "recommendation_count",
        ],
    )
    writer.writeheader()
    for run in runs:
        writer.writerow(
            {
                "timestamp": run.get("timestamp", ""),
                "policy_profile": (run.get("policy_profile") or {}).get("name", ""),
                "score": run.get("score", 0),
                "fitness": run.get("fitness", 0),
                "conflicts": run.get("conflicts", 0),
                "utilization_rate": run.get("utilization_rate", 0),
                "assigned_sections": run.get("assigned_sections", 0),
                "total_sections": run.get("total_sections", 0),
                "faculty_count": run.get("faculty_count", 0),
                "recommendation_count": run.get("recommendation_count", 0),
            }
        )

    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="workload-summary.csv"'},
    )