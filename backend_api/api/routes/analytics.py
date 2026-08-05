from fastapi import APIRouter

from backend_api.api.runtime_state import get_workload_run_history, summarize_runs

router = APIRouter()


@router.get("/kpi-history")
def kpi_history() -> dict[str, object]:
    runs = get_workload_run_history()
    summary = summarize_runs(runs)

    return {
        "summary": summary,
        "runs": runs,
        "trend": [
            {
                "label": f"Run {index + 1}",
                "fitness": run.get("fitness", 0),
                "conflicts": run.get("conflicts", 0),
                "utilization_rate": run.get("utilization_rate", 0),
            }
            for index, run in enumerate(reversed(runs))
        ],
    }