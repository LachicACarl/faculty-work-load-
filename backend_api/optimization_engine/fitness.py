from typing import Any, Dict, List


def evaluate_fitness(
    chromosome: Dict[str, str],
    sections: List[Dict[str, Any]],
    faculty_list: List[Dict[str, Any]],
    weights: Dict[str, float] | None = None,
) -> Dict[str, Any]:
    if weights is None:
        weights = {
            "spec_match": 10.0,
            "utilization": 5.0,
            "conflict": 50.0,
            "policy_violation": 40.0,
            "unassigned": 30.0,
        }

    faculty_map = {f["id"]: f for f in faculty_list}
    section_map = {s["id"]: s for s in sections}

    spec_matches = 0
    conflicts = 0
    policy_violations = 0
    unassigned = 0

    faculty_assigned_units: Dict[str, float] = {f["id"]: 0.0 for f in faculty_list}
    faculty_schedules: Dict[str, List[Dict[str, Any]]] = {f["id"]: [] for f in faculty_list}

    for sec_id, fac_id in chromosome.items():
        sec = section_map.get(sec_id)
        if not sec:
            unassigned += 1
            continue

        if fac_id is None:
            unassigned += 1
            continue

        fac = faculty_map.get(fac_id)
        if not fac:
            unassigned += 1
            continue

        if sec.get("required_specialization") in fac.get("specializations", []):
            spec_matches += 1

        for existing_sec in faculty_schedules[fac_id]:
            if (
                existing_sec.get("day") == sec.get("day")
                and not (
                    sec.get("end_time") <= existing_sec.get("start_time")
                    or sec.get("start_time") >= existing_sec.get("end_time")
                )
            ):
                conflicts += 1

        faculty_schedules[fac_id].append(sec)
        faculty_assigned_units[fac_id] += float(sec.get("units", 3.0))

    total_capacity = 0.0
    total_assigned = 0.0

    for fac_id, assigned_units in faculty_assigned_units.items():
        fac = faculty_map[fac_id]
        max_units = float(fac.get("max_units", 18.0))
        min_units = float(fac.get("min_units", 12.0))
        total_capacity += max_units
        total_assigned += min_units if assigned_units >= min_units else assigned_units

        if assigned_units > max_units:
            policy_violations += int(assigned_units - max_units)
        elif assigned_units < min_units and assigned_units > 0:
            policy_violations += 1

    utilization_score = (total_assigned / total_capacity) * 100 if total_capacity > 0 else 0

    score = (
        (spec_matches * weights["spec_match"])
        + (utilization_score * weights["utilization"])
        - (conflicts * weights["conflict"])
        - (policy_violations * weights["policy_violation"])
        - (unassigned * weights["unassigned"])
    )

    return {
        "score": max(score, 0.0),
        "spec_matches": spec_matches,
        "schedule_conflicts": conflicts,
        "policy_violations": policy_violations,
        "unassigned_subjects": unassigned,
        "utilization_rate": round(utilization_score, 2),
    }


def score_solution(solution: dict[str, object]) -> float:
    return float(solution.get("score", 0.0))
