from typing import Any, Dict, List

from backend_api.optimization_engine.constraint_repair import repair_chromosome
from backend_api.optimization_engine.fitness import evaluate_fitness


def run_tabu_search(
    elite_chromosomes: List[Dict[str, str]],
    sections: List[Dict[str, Any]],
    faculty_list: List[Dict[str, Any]],
    max_iterations: int = 30,
    tabu_tenure: int = 5,
    weights: Dict[str, float] | None = None,
) -> Dict[str, Any]:
    if not elite_chromosomes:
        return {
            "allocation": {},
            "metrics": {
                "score": 0.0,
                "spec_matches": 0,
                "schedule_conflicts": 0,
                "policy_violations": 0,
                "unassigned_subjects": len(sections),
                "utilization_rate": 0.0,
            },
            "explainable_recommendations": [],
        }

    best_chromosome = elite_chromosomes[0]
    best_metrics = evaluate_fitness(best_chromosome, sections, faculty_list, weights)

    tabu_list = []
    faculty_ids = [f["id"] for f in faculty_list]
    curr_chromosome = best_chromosome.copy()

    for _ in range(max_iterations):
        neighborhood = []
        for sec_id in curr_chromosome:
            for fac_id in faculty_ids:
                if curr_chromosome[sec_id] == fac_id:
                    continue
                neighbor = curr_chromosome.copy()
                neighbor[sec_id] = fac_id
                neighborhood.append((neighbor, (sec_id, fac_id)))

        best_neighbor = None
        best_neighbor_move = None
        best_neighbor_metrics = None

        for neighbor, move in neighborhood:
            metrics = evaluate_fitness(neighbor, sections, faculty_list, weights)
            is_tabu = move in tabu_list
            if not is_tabu or metrics["score"] > best_metrics["score"]:
                if best_neighbor_metrics is None or metrics["score"] > best_neighbor_metrics["score"]:
                    best_neighbor = neighbor
                    best_neighbor_move = move
                    best_neighbor_metrics = metrics

        if best_neighbor is None:
            break

        curr_chromosome = best_neighbor
        tabu_list.append(best_neighbor_move)
        if len(tabu_list) > tabu_tenure:
            tabu_list.pop(0)

        if best_neighbor_metrics["score"] > best_metrics["score"]:
            best_chromosome = best_neighbor
            best_metrics = best_neighbor_metrics

    # Final feasibility pass to reduce residual violations after local refinement.
    best_chromosome = repair_chromosome(best_chromosome, sections, faculty_list)
    best_metrics = evaluate_fitness(best_chromosome, sections, faculty_list, weights)

    rationales = []
    section_map = {s["id"]: s for s in sections}
    faculty_map = {f["id"]: f for f in faculty_list}

    for sec_id, fac_id in best_chromosome.items():
        sec = section_map.get(sec_id)
        if not sec:
            continue
        fac = faculty_map.get(fac_id) if fac_id else None
        if fac:
            is_spec = sec.get("required_specialization") in fac.get("specializations", [])
            rationales.append(
                {
                    "section_id": sec_id,
                    "course_code": sec.get("code"),
                    "assigned_faculty": fac.get("name"),
                    "specialization_matched": is_spec,
                    "explanation": f"Assigned to {fac.get('name')} based on {'100% specialization match' if is_spec else 'general academic domain match'} and schedule compatibility.",
                }
            )

    return {
        "allocation": best_chromosome,
        "metrics": best_metrics,
        "explainable_recommendations": rationales,
    }


def refine_solution(solution: dict[str, object]) -> dict[str, object]:
    return solution
