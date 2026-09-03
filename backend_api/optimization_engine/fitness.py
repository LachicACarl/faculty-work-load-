"""Fitness function and objective scoring for workload allocation."""
from typing import List, Tuple, Dict
import math


class FitnessEvaluator:
    """Evaluates fitness of allocation solutions."""
    
    def __init__(self, faculty_specs: Dict, sections_data: Dict, policies: Dict):
        """
        Initialize fitness evaluator.
        
        Args:
            faculty_specs: Faculty qualifications and constraints
            sections_data: Section requirements and schedules
            policies: Workload policies and weights
        """
        self.faculty_specs = faculty_specs
        self.sections_data = sections_data
        self.policies = policies
        self.balance_priority = policies.get('balance_priority', 0.7)
        self.specialization_priority = 1.0 - self.balance_priority
    
    def evaluate(self, allocations: List[Tuple[int, int]]) -> float:
        """
        Calculate overall fitness score (0.0-1.0).
        
        Composite fitness function:
        F(x) = w_1 * F_specialization(x) + w_2 * F_utilization(x)
        
        where:
        - F_specialization: Quality of specialization matching
        - F_utilization: Balance of workload distribution
        
        Args:
            allocations: List of (faculty_id, section_id) assignments
            
        Returns:
            Fitness score 0.0-1.0
        """
        if not allocations:
            return 0.0
        
        spec_score = self._calculate_specialization_fitness(allocations)
        util_score = self._calculate_utilization_fitness(allocations)
        
        # Weighted combination
        total_fitness = (self.specialization_priority * spec_score +
                        self.balance_priority * util_score)
        
        return max(0.0, min(1.0, total_fitness))  # Clamp to [0, 1]
    
    def _calculate_specialization_fitness(self, allocations: List[Tuple[int, int]]) -> float:
        """
        Calculate specialization matching component of fitness.
        
        Ranges 0.0-1.0:
        - 1.0: All faculty have exact specialization match for assigned sections
        - 0.5: Mix of matches and unmatched
        - 0.0: No specialization matches
        
        Args:
            allocations: Faculty-section assignments
            
        Returns:
            Specialization fitness component
        """
        if not allocations:
            return 0.0
        
        match_scores = []
        
        for faculty_id, section_id in allocations:
            section = self.sections_data.get(section_id, {})
            required_spec = section.get('required_specialization')
            
            if not required_spec:
                # No specialization requirement = perfect match
                match_scores.append(1.0)
                continue
            
            faculty = self.faculty_specs.get(faculty_id, {})
            qualifications = faculty.get('qualifications', [])
            
            # Find best matching specialization
            best_match = 0.0
            for qual in qualifications:
                spec = qual.get('specialization', '').lower()
                required = required_spec.lower()
                
                if spec == required:
                    best_match = qual.get('proficiency_level', 1.0)
                    break
                elif spec.startswith(required[:3]):  # Partial match on first 3 chars
                    best_match = max(best_match, 0.5)
            
            match_scores.append(best_match)
        
        return sum(match_scores) / len(match_scores) if match_scores else 0.0
    
    def _calculate_utilization_fitness(self, allocations: List[Tuple[int, int]]) -> float:
        """
        Calculate workload balance component of fitness.
        
        Encourages:
        - Spreading workload across faculty
        - Achieving target utilization rates
        - Avoiding underutilization and overload
        
        Args:
            allocations: Faculty-section assignments
            
        Returns:
            Utilization fitness component
        """
        if not allocations:
            return 0.0
        
        # Calculate workload per faculty
        faculty_workload = {}
        for faculty_id, section_id in allocations:
            units = self.sections_data[section_id]['units']
            if faculty_id not in faculty_workload:
                faculty_workload[faculty_id] = 0
            faculty_workload[faculty_id] += units
        
        # Calculate utilization ratios
        utilization_scores = []
        
        for faculty_id, workload in faculty_workload.items():
            faculty = self.faculty_specs[faculty_id]
            max_units = faculty['max_units']
            target_util = 0.85  # Ideal utilization
            
            actual_util = workload / max_units if max_units > 0 else 0.0
            
            # Fitness decreases with deviation from target
            if actual_util <= 1.0:
                # Under or at capacity
                deviation = abs(actual_util - target_util)
                score = 1.0 - (deviation * 1.2)  # Penalize underutilization slightly
            else:
                # Over capacity
                overload_ratio = (actual_util - 1.0) / 0.5  # Normalize to [-0.5, 0]
                score = 1.0 - (min(1.0, overload_ratio) * 0.8)  # Strong penalty
            
            utilization_scores.append(max(0.0, score))
        
        # Also factor in balance (variance) across faculty
        avg_util = sum(faculty_workload.values()) / len(faculty_workload) if faculty_workload else 0
        variance = sum((u - avg_util) ** 2 for u in faculty_workload.values()) / len(faculty_workload) if faculty_workload else 0
        
        # Higher variance = less balanced = lower score
        variance_penalty = math.sqrt(variance) / max(avg_util, 1.0) if avg_util > 0 else 0.0
        variance_score = 1.0 - min(1.0, variance_penalty)
        
        # Combine utilization and balance
        util_avg = sum(utilization_scores) / len(utilization_scores) if utilization_scores else 0.0
        
        return 0.6 * util_avg + 0.4 * variance_score
    
    def get_allocation_details(self, faculty_id: int, section_id: int) -> Dict:
        """
        Get detailed metrics for a single allocation.
        
        Args:
            faculty_id: Faculty member ID
            section_id: Section ID
            
        Returns:
            Dict with match quality, workload, explanation
        """
        section = self.sections_data.get(section_id, {})
        faculty = self.faculty_specs.get(faculty_id, {})
        
        # Calculate match quality
        required_spec = section.get('required_specialization')
        match_quality = 0.0
        match_level = "Unmatched"
        
        if not required_spec:
            match_quality = 1.0
            match_level = "Exact"
        else:
            qualifications = faculty.get('qualifications', [])
            for qual in qualifications:
                if qual.get('specialization', '').lower() == required_spec.lower():
                    match_quality = qual.get('proficiency_level', 1.0)
                    match_level = "Exact"
                    break
            
            if match_quality == 0.0:
                for qual in qualifications:
                    if qual.get('specialization', '').lower().startswith(required_spec.lower()[:3]):
                        match_quality = 0.5
                        match_level = "Partial"
                        break
        
        # Build explanation
        explanation = f"Assigned {faculty.get('full_name', 'Faculty')} to {section.get('name', 'Section')} "
        explanation += f"with {match_quality:.0%} specialization match"
        
        return {
            "match_quality": match_quality,
            "match_level": match_level,
            "explanation": explanation,
            "workload_units": section.get('units', 0)
        }
