import random
from typing import Any, Dict, List


def repair_chromosome(
    chromosome: Dict[str, str],
    sections: List[Dict[str, Any]],
    faculty_list: List[Dict[str, Any]],
) -> Dict[str, str]:
    repaired = chromosome.copy()
    section_map = {s["id"]: s for s in sections}
    faculty_map = {f["id"]: f for f in faculty_list}

    def is_assignment_valid(
        fac_id: str,
        sec: Dict[str, Any],
        current_units: float,
        schedules: List[Dict[str, Any]],
    ) -> bool:
        fac = faculty_map[fac_id]
        if current_units + float(sec.get("units", 3.0)) > float(fac.get("max_units", 18.0)):
            return False
        for existing in schedules:
            if (
                existing.get("day") == sec.get("day")
                and not (
                    sec.get("end_time") <= existing.get("start_time")
                    or sec.get("start_time") >= existing.get("end_time")
                )
            ):
                return False
        return True

    faculty_units = {f["id"]: 0.0 for f in faculty_list}
    faculty_schedules = {f["id"]: [] for f in faculty_list}

    for sec_id, fac_id in list(repaired.items()):
        if fac_id is None:
            continue

        sec = section_map.get(sec_id)
        if not sec:
            repaired[sec_id] = None
            continue

        if not is_assignment_valid(fac_id, sec, faculty_units[fac_id], faculty_schedules[fac_id]):
            reassigned = False
            candidates = [
                f for f in faculty_list if sec.get("required_specialization") in f.get("specializations", [])
            ]
            random.shuffle(candidates)

            for cand in candidates:
                cand_id = cand["id"]
                if is_assignment_valid(cand_id, sec, faculty_units[cand_id], faculty_schedules[cand_id]):
                    repaired[sec_id] = cand_id
                    faculty_units[cand_id] += float(sec.get("units", 3.0))
                    faculty_schedules[cand_id].append(sec)
                    reassigned = True
                    break

            if not reassigned:
                repaired[sec_id] = None
        else:
            faculty_units[fac_id] += float(sec.get("units", 3.0))
            faculty_schedules[fac_id].append(sec)

    return repaired


def repair_solution(solution: dict[str, object]) -> dict[str, object]:
    return solution
