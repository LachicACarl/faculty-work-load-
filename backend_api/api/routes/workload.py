from fastapi import APIRouter, HTTPException

from backend_api.api.runtime_state import record_workload_run
from backend_api.optimization_engine.genetic_algorithm import run_genetic_algorithm
from backend_api.optimization_engine.tabu_search import run_tabu_search
from backend_api.schemas.workload import ObjectiveWeights, OptimizeWorkloadRequest, PolicyProfileInput

router = APIRouter(prefix="/workload", tags=["Workload Allocation"])


SAMPLE_POLICY_PROFILES = [
    {
        "id": "balanced",
        "name": "Balanced Baseline",
        "description": "Keeps load balance and specialization in equilibrium.",
        "policy_profile": {
            "id": "balanced",
            "name": "Balanced Baseline",
            "full_time_max_units": 21.0,
            "part_time_max_units": 12.0,
            "allowable_overload": 3.0,
            "specialization_required": True,
            "consecutive_limit": 2,
            "balance_priority": 70.0,
            "utilization_target": 80.0,
        },
        "objective_weights": {
            "spec_match": 12.0,
            "utilization": 5.0,
            "conflict": 50.0,
            "policy_violation": 42.0,
            "unassigned": 30.0,
        },
    },
    {
        "id": "utilization",
        "name": "High Utilization",
        "description": "Pushes for higher load coverage while preserving feasibility.",
        "policy_profile": {
            "id": "utilization",
            "name": "High Utilization",
            "full_time_max_units": 24.0,
            "part_time_max_units": 15.0,
            "allowable_overload": 6.0,
            "specialization_required": False,
            "consecutive_limit": 3,
            "balance_priority": 90.0,
            "utilization_target": 95.0,
        },
        "objective_weights": {
            "spec_match": 9.0,
            "utilization": 7.0,
            "conflict": 45.0,
            "policy_violation": 38.0,
            "unassigned": 25.0,
        },
    },
    {
        "id": "specialization",
        "name": "Strict Specialization",
        "description": "Prioritizes exact specialization matches and tighter scheduling.",
        "policy_profile": {
            "id": "specialization",
            "name": "Strict Specialization",
            "full_time_max_units": 21.0,
            "part_time_max_units": 12.0,
            "allowable_overload": 2.0,
            "specialization_required": True,
            "consecutive_limit": 2,
            "balance_priority": 85.0,
            "utilization_target": 82.0,
        },
        "objective_weights": {
            "spec_match": 15.0,
            "utilization": 4.5,
            "conflict": 55.0,
            "policy_violation": 45.0,
            "unassigned": 30.0,
        },
    },
]


def _merge_weights(profile: PolicyProfileInput, weights: ObjectiveWeights) -> dict[str, float]:
    merged = weights.model_dump()
    specialization_multiplier = 1.15 if profile.specialization_required else 0.85
    balance_multiplier = 1.0 + max(min(profile.balance_priority, 100.0), 0.0) / 250.0
    utilization_multiplier = 1.0 + max(profile.utilization_target - 80.0, 0.0) / 200.0
    overload_multiplier = 1.0 + max(profile.allowable_overload, 0.0) / 20.0
    conflict_multiplier = 1.0 + max(4 - profile.consecutive_limit, 0) / 20.0

    merged["spec_match"] *= specialization_multiplier
    merged["utilization"] *= balance_multiplier * utilization_multiplier
    merged["policy_violation"] *= overload_multiplier
    merged["conflict"] *= conflict_multiplier
    return merged


def _normalize_faculty(profile: PolicyProfileInput, faculty_payload: list[dict[str, object]]) -> list[dict[str, object]]:
    normalized = []
    for faculty in faculty_payload:
        adjusted = dict(faculty)
        employment_type = str(adjusted.get("employment_type", "")).lower()
        if employment_type.startswith("full"):
            max_units = profile.full_time_max_units + profile.allowable_overload
        else:
            max_units = profile.part_time_max_units + min(profile.allowable_overload, 3.0)
        adjusted["max_units"] = min(float(adjusted.get("max_units", max_units)), float(max_units))
        adjusted["min_units"] = min(float(adjusted.get("min_units", 0.0)), float(adjusted["max_units"]))
        normalized.append(adjusted)
    return normalized


@router.post("/optimize")
async def optimize_workload(payload: OptimizeWorkloadRequest):
    sections = [section.model_dump() for section in payload.sections]
    faculty_list = [faculty.model_dump() for faculty in payload.faculty]

    if not sections:
        raise HTTPException(status_code=400, detail="sections payload is required")

    if not faculty_list:
        raise HTTPException(status_code=400, detail="faculty payload is required")

    policy_profile = payload.policy_profile
    weights = _merge_weights(policy_profile, payload.objective_weights)
    faculty_list = _normalize_faculty(policy_profile, faculty_list)

    elites = run_genetic_algorithm(sections, faculty_list, pop_size=30, generations=50, weights=weights)
    if not elites:
        raise HTTPException(status_code=422, detail="unable to generate feasible candidate solutions")

    optimized_result = run_tabu_search(elites, sections, faculty_list, max_iterations=20, weights=weights)

    record_workload_run(
        {
            "policy_profile": policy_profile.model_dump(),
            "objective_weights": weights,
            "score": optimized_result["metrics"]["score"],
            "fitness": round(float(optimized_result["metrics"]["score"]) / 100.0, 2),
            "conflicts": optimized_result["metrics"]["schedule_conflicts"],
            "utilization_rate": optimized_result["metrics"]["utilization_rate"],
            "assigned_sections": len([section for section, faculty_id in optimized_result["allocation"].items() if faculty_id]),
            "total_sections": len(sections),
            "faculty_count": len(faculty_list),
            "recommendation_count": len(optimized_result["explainable_recommendations"]),
        }
    )

    return {
        "status": "success",
        "policy_profile": policy_profile.model_dump(),
        "objective_weights": weights,
        "data": optimized_result,
    }


@router.get("/policy-profiles")
def list_policy_profiles() -> list[dict[str, object]]:
    return SAMPLE_POLICY_PROFILES
