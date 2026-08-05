from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any


WORKLOAD_RUN_HISTORY: list[dict[str, Any]] = []


def record_workload_run(entry: dict[str, Any]) -> dict[str, Any]:
    enriched = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **entry,
    }
    WORKLOAD_RUN_HISTORY.insert(0, enriched)
    del WORKLOAD_RUN_HISTORY[20:]
    return enriched


def get_workload_run_history(limit: int | None = None) -> list[dict[str, Any]]:
    if limit is None:
        return list(WORKLOAD_RUN_HISTORY)
    return list(WORKLOAD_RUN_HISTORY[:limit])


def get_latest_workload_run() -> dict[str, Any] | None:
    return WORKLOAD_RUN_HISTORY[0] if WORKLOAD_RUN_HISTORY else None


def summarize_runs(runs: Iterable[dict[str, Any]]) -> dict[str, Any]:
    run_list = list(runs)
    if not run_list:
        return {
            "run_count": 0,
            "average_conflicts": 0.0,
            "average_utilization": 0.0,
            "best_fitness": 0.0,
            "latest_profile": None,
        }

    run_count = len(run_list)
    average_conflicts = round(sum(float(run.get("conflicts", 0)) for run in run_list) / run_count, 2)
    average_utilization = round(sum(float(run.get("utilization_rate", 0)) for run in run_list) / run_count, 2)
    best_fitness = round(max(float(run.get("fitness", 0)) for run in run_list), 2)
    latest_profile = run_list[0].get("policy_profile")

    return {
        "run_count": run_count,
        "average_conflicts": average_conflicts,
        "average_utilization": average_utilization,
        "best_fitness": best_fitness,
        "latest_profile": latest_profile,
    }