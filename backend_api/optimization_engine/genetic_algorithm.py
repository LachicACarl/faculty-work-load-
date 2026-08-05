import random
from typing import Any, Dict, List

from backend_api.optimization_engine.constraint_repair import repair_chromosome
from backend_api.optimization_engine.fitness import evaluate_fitness


def run_genetic_algorithm(
    sections: List[Dict[str, Any]],
    faculty_list: List[Dict[str, Any]],
    pop_size: int = 50,
    generations: int = 100,
    mutation_rate: float = 0.1,
    weights: Dict[str, float] | None = None,
) -> List[Dict[str, Any]]:
    if not sections or not faculty_list:
        return []

    faculty_ids = [f["id"] for f in faculty_list]
    if not faculty_ids:
        return []

    population = []
    for _ in range(pop_size):
        chrom = {s["id"]: random.choice(faculty_ids) for s in sections}
        population.append(chrom)

    for _ in range(generations):
        evaluations = [(chrom, evaluate_fitness(chrom, sections, faculty_list, weights)) for chrom in population]
        evaluations.sort(key=lambda x: x[1]["score"], reverse=True)

        cutoff = max(2, int(pop_size * 0.2))
        next_gen = [e[0] for e in evaluations[:cutoff]]

        while len(next_gen) < pop_size:
            p1, p2 = random.sample(next_gen[:cutoff], 2)
            child = {s_id: p1[s_id] if random.random() > 0.5 else p2[s_id] for s_id in p1}

            if random.random() < mutation_rate:
                mut_key = random.choice(list(child.keys()))
                child[mut_key] = random.choice(faculty_ids)

            child = repair_chromosome(child, sections, faculty_list)
            next_gen.append(child)

        population = next_gen

    final_evals = [(chrom, evaluate_fitness(chrom, sections, faculty_list, weights)) for chrom in population]
    final_evals.sort(key=lambda x: x[1]["score"], reverse=True)
    return [e[0] for e in final_evals[:5]]


def generate_initial_population(population_size: int) -> list[dict[str, object]]:
    return [{} for _ in range(population_size)]
