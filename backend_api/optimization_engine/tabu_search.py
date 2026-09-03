"""Tabu Search local refinement for workload allocation."""
from typing import List, Tuple, Set, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import random


@dataclass
class Move:
    """Represents a move in neighborhood search."""
    faculty_from: int
    faculty_to: int
    section_id: int
    delta_fitness: float = 0.0  # Change in fitness if applied


@dataclass
class TabuAttribute:
    """Tabu tenure tracking for moves."""
    move: Move
    tabu_until: int  # Iteration when move becomes non-tabu


class TabuSearch:
    """Tabu Search for local refinement of elite solutions."""
    
    def __init__(self, tabu_tenure: int = None, max_iterations: int = None):
        """
        Initialize Tabu Search.
        
        Args:
            tabu_tenure: How long moves remain tabu (default from settings)
            max_iterations: Maximum local search iterations
        """
        from backend_api.core.config import settings
        self.tabu_tenure = tabu_tenure or settings.TABU_TENURE
        self.max_iterations = max_iterations or settings.TABU_MAX_ITERATIONS
        self.tabu_list: List[TabuAttribute] = []
        self.best_solution: Optional[List[Tuple[int, int]]] = None
        self.best_fitness: float = 0.0
        self.iteration_history: List[float] = []
    
    def generate_neighborhood(self,
                            allocations: List[Tuple[int, int]],
                            eligible_pairs: List[Tuple[int, int]]) -> List[Move]:
        """
        Generate neighborhood moves from current solution.
        
        Neighborhood operators:
        1. Reassignment: Assign section to different faculty
        2. Exchange: Swap assignments between two faculty
        3. Insertion: Add unassigned section
        4. Deletion: Remove allocation (last resort)
        
        Args:
            allocations: Current allocation solution
            eligible_pairs: Valid (faculty, section) pairs
            
        Returns:
            List of feasible moves
        """
        moves = []
        allocated = {sec: fac for fac, sec in allocations}
        
        # Reassignment moves: change faculty for existing section
        for faculty_id, section_id in allocations:
            alternatives = [f for f, s in eligible_pairs if s == section_id and f != faculty_id]
            for alt_faculty in alternatives:
                moves.append(Move(
                    faculty_from=faculty_id,
                    faculty_to=alt_faculty,
                    section_id=section_id
                ))
        
        # Exchange moves: swap assignments
        for i, (fac1, sec1) in enumerate(allocations):
            for j, (fac2, sec2) in enumerate(allocations):
                if i < j:  # Avoid duplicates
                    # Check if both exchanges are valid
                    if (fac2, sec1) in eligible_pairs and (fac1, sec2) in eligible_pairs:
                        moves.append(Move(
                            faculty_from=fac1,
                            faculty_to=fac2,
                            section_id=sec1  # Indicates exchange of sec1 and sec2
                        ))
        
        # Insertion moves: add unassigned sections
        unassigned_sections = set(s for _, s in eligible_pairs) - set(sec for _, sec in allocations)
        for section_id in list(unassigned_sections)[:min(10, len(unassigned_sections))]:
            for faculty_id, sec in eligible_pairs:
                if sec == section_id:
                    moves.append(Move(
                        faculty_from=-1,  # Indicates insertion
                        faculty_to=faculty_id,
                        section_id=section_id
                    ))
                    break
        
        return moves[:min(len(moves), 50)]  # Limit neighborhood size
    
    def apply_move(self, allocations: List[Tuple[int, int]], move: Move) -> List[Tuple[int, int]]:
        """
        Apply a move to current solution.
        
        Args:
            allocations: Current solution
            move: Move to apply
            
        Returns:
            New solution after applying move
        """
        new_alloc = allocations.copy()
        
        if move.faculty_from == -1:
            # Insertion
            new_alloc.append((move.faculty_to, move.section_id))
        else:
            # Find and update allocation
            for i, (fac, sec) in enumerate(new_alloc):
                if fac == move.faculty_from and sec == move.section_id:
                    new_alloc[i] = (move.faculty_to, sec)
                    break
        
        return new_alloc
    
    def is_tabu(self, move: Move, current_iteration: int) -> bool:
        """
        Check if move is tabu.
        
        Args:
            move: Move to check
            current_iteration: Current iteration number
            
        Returns:
            True if move is currently tabu
        """
        for tabu_attr in self.tabu_list:
            if (tabu_attr.move.faculty_from == move.faculty_from and
                tabu_attr.move.faculty_to == move.faculty_to and
                tabu_attr.move.section_id == move.section_id):
                if current_iteration < tabu_attr.tabu_until:
                    return True
        
        return False
    
    def add_to_tabu(self, move: Move, current_iteration: int):
        """Add move to tabu list."""
        self.tabu_list.append(TabuAttribute(
            move=move,
            tabu_until=current_iteration + self.tabu_tenure
        ))
        
        # Remove old tabu entries
        self.tabu_list = [t for t in self.tabu_list
                         if t.tabu_until > current_iteration]
    
    def refine(self, initial_solution: List[Tuple[int, int]],
              fitness_func,
              eligible_pairs: List[Tuple[int, int]],
              iteration_callback=None) -> List[Tuple[int, int]]:
        """
        Execute Tabu Search local refinement.
        
        Args:
            initial_solution: Elite solution from GA
            fitness_func: Fitness evaluation function
            eligible_pairs: Valid (faculty, section) pairs
            iteration_callback: Optional callback(iteration, best_fitness)
            
        Returns:
            Best solution found during search
        """
        current = initial_solution.copy()
        current_fitness = fitness_func(current)
        
        self.best_solution = current.copy()
        self.best_fitness = current_fitness
        self.tabu_list = []
        
        for iteration in range(self.max_iterations):
            # Generate neighborhood
            neighborhood = self.generate_neighborhood(current, eligible_pairs)
            
            if not neighborhood:
                break
            
            # Find best non-tabu move
            best_move = None
            best_move_fitness = float('-inf')
            
            for move in neighborhood:
                if not self.is_tabu(move, iteration):
                    candidate = self.apply_move(current, move)
                    candidate_fitness = fitness_func(candidate)
                    
                    if candidate_fitness > best_move_fitness:
                        best_move = move
                        best_move_fitness = candidate_fitness
            
            # Aspiration criteria: override tabu if better than best known
            if best_move is None or best_move_fitness <= self.best_fitness:
                for move in neighborhood:
                    candidate = self.apply_move(current, move)
                    candidate_fitness = fitness_func(candidate)
                    
                    if candidate_fitness > self.best_fitness:
                        best_move = move
                        best_move_fitness = candidate_fitness
                        # Override tabu
                        break
            
            if best_move is None:
                break
            
            # Apply move
            current = self.apply_move(current, best_move)
            current_fitness = best_move_fitness
            
            self.add_to_tabu(best_move, iteration)
            
            # Update best
            if current_fitness > self.best_fitness:
                self.best_solution = current.copy()
                self.best_fitness = current_fitness
            
            self.iteration_history.append(self.best_fitness)
            
            if iteration_callback:
                iteration_callback(iteration, self.best_fitness)
        
        return self.best_solution
