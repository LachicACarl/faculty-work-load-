"""Genetic Algorithm implementation for faculty workload allocation."""
import random
from typing import List, Tuple
from dataclasses import dataclass
from backend_api.core.config import settings


@dataclass
class Chromosome:
    """Represents a candidate solution (faculty-section allocation)."""
    allocations: List[Tuple[int, int]]  # List of (faculty_id, section_id) pairs
    fitness: float = 0.0
    violations: List[str] = None
    
    def __post_init__(self):
        if self.violations is None:
            self.violations = []


class GeneticAlgorithm:
    """Modified Hybrid Genetic Algorithm for workload allocation."""
    
    def __init__(self, population_size: int = None, generations: int = None,
                 mutation_rate: float = None, crossover_rate: float = None):
        """Initialize GA with configuration."""
        self.population_size = population_size or settings.GA_POPULATION_SIZE
        self.generations = generations or settings.GA_GENERATIONS
        self.mutation_rate = mutation_rate or settings.GA_MUTATION_RATE
        self.crossover_rate = crossover_rate or settings.GA_CROSSOVER_RATE
        self.population: List[Chromosome] = []
        self.best_chromosome: Chromosome = None
        self.fitness_history: List[float] = []
        
    def initialize_population(self, eligible_pairs: List[Tuple[int, int]],
                            sections_count: int) -> List[Chromosome]:
        """
        Generate initial population of random allocations.
        
        Args:
            eligible_pairs: List of (faculty_id, section_id) pairs that satisfy hard constraints
            sections_count: Total number of sections to assign
            
        Returns:
            List of initialized chromosomes
        """
        population = []
        
        for _ in range(self.population_size):
            # Sample eligible pairs to create partial solution
            available_pairs = eligible_pairs.copy()
            random.shuffle(available_pairs)
            
            # Create allocation taking at most one per section
            allocated_sections = set()
            allocations = []
            
            for faculty_id, section_id in available_pairs:
                if section_id not in allocated_sections:
                    allocations.append((faculty_id, section_id))
                    allocated_sections.add(section_id)
                    
                if len(allocations) >= sections_count:
                    break
            
            chromosome = Chromosome(allocations=allocations)
            population.append(chromosome)
        
        self.population = population
        return population
    
    def tournament_selection(self, tournament_size: int = 3) -> Chromosome:
        """
        Select a parent chromosome using tournament selection.
        
        Args:
            tournament_size: Number of candidates in tournament
            
        Returns:
            Best chromosome from tournament
        """
        tournament = random.sample(self.population, min(tournament_size, len(self.population)))
        return max(tournament, key=lambda c: c.fitness)
    
    def crossover(self, parent1: Chromosome, parent2: Chromosome) -> Chromosome:
        """
        Perform crossover between two parent chromosomes.
        Uses two-point crossover with conflict awareness.
        
        Args:
            parent1: First parent chromosome
            parent2: Second parent chromosome
            
        Returns:
            Child chromosome combining genetic material
        """
        if random.random() > self.crossover_rate or not parent1.allocations or not parent2.allocations:
            return Chromosome(allocations=parent1.allocations.copy())
        
        # Two-point crossover
        alloc1 = parent1.allocations.copy()
        alloc2 = parent2.allocations.copy()
        
        point1 = random.randint(0, len(alloc1))
        point2 = random.randint(point1, len(alloc1))
        
        # Create child by combining segments, avoiding duplicate section assignments
        child_allocations = alloc1[:point1]
        allocated_sections = {sec for _, sec in child_allocations}
        
        # Add segments from parent2 avoiding conflicts
        for faculty_id, section_id in alloc2[point1:point2]:
            if section_id not in allocated_sections:
                child_allocations.append((faculty_id, section_id))
                allocated_sections.add(section_id)
        
        # Add remaining from parent1
        for faculty_id, section_id in alloc1[point2:]:
            if section_id not in allocated_sections:
                child_allocations.append((faculty_id, section_id))
                allocated_sections.add(section_id)
        
        return Chromosome(allocations=child_allocations)
    
    def mutate(self, chromosome: Chromosome, eligible_pairs: List[Tuple[int, int]]) -> Chromosome:
        """
        Apply mutation operator to create variation.
        
        Mutations include:
        - Reassignment: Change faculty for a section
        - Insertion: Add new valid allocation
        - Deletion: Remove problematic allocation
        
        Args:
            chromosome: Chromosome to mutate
            eligible_pairs: Valid (faculty, section) pairs
            
        Returns:
            Mutated chromosome
        """
        if random.random() > self.mutation_rate:
            return chromosome
        
        mutated = Chromosome(allocations=chromosome.allocations.copy())
        
        mutation_type = random.choice(['reassign', 'insert', 'remove'])
        allocated_sections = {sec for _, sec in mutated.allocations}
        
        if mutation_type == 'reassign' and mutated.allocations:
            # Replace one allocation with alternative
            idx = random.randint(0, len(mutated.allocations) - 1)
            old_faculty, section = mutated.allocations[idx]
            
            # Find alternative faculty for same section
            alternatives = [f for f, s in eligible_pairs if s == section and f != old_faculty]
            if alternatives:
                mutated.allocations[idx] = (random.choice(alternatives), section)
        
        elif mutation_type == 'insert' and len(eligible_pairs) > len(mutated.allocations):
            # Add new allocation for unassigned section
            unassigned = [(f, s) for f, s in eligible_pairs if s not in allocated_sections]
            if unassigned:
                mutated.allocations.append(random.choice(unassigned))
        
        elif mutation_type == 'remove' and mutated.allocations:
            # Remove allocation with lowest fitness contribution
            mutated.allocations.pop(random.randint(0, len(mutated.allocations) - 1))
        
        return mutated
    
    def evolve(self, fitness_func, eligible_pairs: List[Tuple[int, int]],
              generation_callback=None) -> Chromosome:
        """
        Execute genetic algorithm evolution loop.
        
        Args:
            fitness_func: Callable that evaluates chromosome fitness
            eligible_pairs: Valid (faculty, section) pairs
            generation_callback: Optional callback(generation, best_fitness) for logging
            
        Returns:
            Best chromosome found
        """
        # Initialize and evaluate population
        self.initialize_population(eligible_pairs, len(set(s for _, s in eligible_pairs)))
        
        for chromosome in self.population:
            chromosome.fitness = fitness_func(chromosome)
        
        self.best_chromosome = max(self.population, key=lambda c: c.fitness)
        
        # Evolution loop
        for generation in range(self.generations):
            new_population = []
            
            # Elitism: keep best
            new_population.append(Chromosome(allocations=self.best_chromosome.allocations.copy()))
            
            # Generate rest of population
            while len(new_population) < self.population_size:
                parent1 = self.tournament_selection()
                parent2 = self.tournament_selection()
                
                child = self.crossover(parent1, parent2)
                child = self.mutate(child, eligible_pairs)
                child.fitness = fitness_func(child)
                
                new_population.append(child)
            
            self.population = new_population
            
            # Update best
            generation_best = max(self.population, key=lambda c: c.fitness)
            if generation_best.fitness > self.best_chromosome.fitness:
                self.best_chromosome = generation_best
            
            self.fitness_history.append(self.best_chromosome.fitness)
            
            if generation_callback:
                generation_callback(generation, self.best_chromosome.fitness)
        
        return self.best_chromosome
