"""Constraint repair and validation logic."""
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass, field


@dataclass
class ConstraintViolation:
    """Represents a single constraint violation."""
    type: str  # schedule_conflict, overload, specialization_mismatch, etc.
    faculty_id: int
    section_id: int
    severity: float  # 0.0-1.0
    details: str


class ConstraintRepair:
    """Repairs hard constraint violations in candidate solutions."""
    
    def __init__(self, faculty_specs: Dict, sections_data: Dict, policies: Dict):
        """
        Initialize constraint repair engine.
        
        Args:
            faculty_specs: Dict with faculty qualifications, availability, max_units
            sections_data: Dict with section schedules, required specialization
            policies: Policy constraints (max_units, specialization_required, etc.)
        """
        self.faculty_specs = faculty_specs
        self.sections_data = sections_data
        self.policies = policies
        self.violations: List[ConstraintViolation] = []
    
    def detect_violations(self, allocations: List[Tuple[int, int]]) -> List[ConstraintViolation]:
        """
        Detect hard constraint violations in allocation.
        
        Hard constraints:
        - V_h1: No schedule conflicts (faculty not available at section time)
        - V_h2: Workload limits (faculty units <= policy max + overload)
        - V_h3: Specialization requirements met if policy requires
        
        Args:
            allocations: List of (faculty_id, section_id) pairs
            
        Returns:
            List of detected violations
        """
        self.violations = []
        faculty_workload = {}
        allocated_sections = {}
        
        for faculty_id, section_id in allocations:
            # Track workload
            faculty_workload[faculty_id] = faculty_workload.get(faculty_id, 0) + \
                                          self.sections_data[section_id]['units']
            allocated_sections[faculty_id] = allocated_sections.get(faculty_id, []) + [section_id]
        
        # Check violations
        for faculty_id, section_id in allocations:
            faculty = self.faculty_specs[faculty_id]
            section = self.sections_data[section_id]
            
            # V_h1: Schedule conflict
            if not self._check_availability(faculty_id, section):
                self.violations.append(ConstraintViolation(
                    type="schedule_conflict",
                    faculty_id=faculty_id,
                    section_id=section_id,
                    severity=1.0,
                    details=f"Faculty not available at {section['schedule_day']} {section['schedule_time']}"
                ))
            
            # V_h2: Workload overload
            max_allowed = faculty['max_units'] + faculty.get('overload_allowed', 0)
            if faculty_workload[faculty_id] > max_allowed:
                excess = faculty_workload[faculty_id] - max_allowed
                self.violations.append(ConstraintViolation(
                    type="overload",
                    faculty_id=faculty_id,
                    section_id=section_id,
                    severity=min(1.0, excess / max_allowed),
                    details=f"Workload {faculty_workload[faculty_id]} exceeds max {max_allowed}"
                ))
            
            # V_h3: Specialization requirements
            if self.policies.get('specialization_required', True) and section.get('required_specialization'):
                if not self._has_specialization(faculty_id, section['required_specialization']):
                    self.violations.append(ConstraintViolation(
                        type="specialization_mismatch",
                        faculty_id=faculty_id,
                        section_id=section_id,
                        severity=1.0,
                        details=f"Faculty lacks required specialization: {section['required_specialization']}"
                    ))
        
        return self.violations
    
    def repair(self, allocations: List[Tuple[int, int]],
              eligible_pairs: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Repair constraint violations using reassignment and reordering.
        
        Repair operators:
        1. Reassign conflicting faculty to alternative eligible faculty
        2. Remove violating allocations and leave section unassigned
        3. Reorder allocations to respect consecutive limits
        
        Args:
            allocations: Potentially infeasible allocations
            eligible_pairs: All valid (faculty, section) pairs
            
        Returns:
            Repaired allocations with fewer/zero hard violations
        """
        violations = self.detect_violations(allocations)
        
        if not violations:
            return allocations
        
        repaired = allocations.copy()
        
        # Group violations by severity
        severe_violations = [v for v in violations if v.severity >= 0.8]
        
        # For each violation, attempt repair
        for violation in severe_violations:
            # Find allocation to repair
            alloc_idx = None
            for i, (fid, sid) in enumerate(repaired):
                if fid == violation.faculty_id and sid == violation.section_id:
                    alloc_idx = i
                    break
            
            if alloc_idx is None:
                continue
            
            section_id = violation.section_id
            
            # Find alternative faculty
            alternatives = [f for f, s in eligible_pairs if s == section_id]
            
            if alternatives:
                # Pick least loaded faculty
                chosen = min(alternatives,
                           key=lambda f: sum(self.sections_data[s]['units']
                                            for _, s in repaired if _ == f))
                repaired[alloc_idx] = (chosen, section_id)
            else:
                # No valid alternative, remove allocation
                repaired.pop(alloc_idx)
        
        return repaired
    
    def is_feasible(self, allocations: List[Tuple[int, int]]) -> bool:
        """
        Check if allocation satisfies all hard constraints.
        
        Args:
            allocations: Allocation to validate
            
        Returns:
            True if feasible (V_h(x) = 0)
        """
        violations = self.detect_violations(allocations)
        return len(violations) == 0
    
    def _check_availability(self, faculty_id: int, section: Dict) -> bool:
        """Check if faculty is available at section time."""
        faculty = self.faculty_specs[faculty_id]
        availability_slots = faculty.get('availability', [])
        
        section_day = section.get('schedule_day', 0)
        
        for slot in availability_slots:
            if slot['day_of_week'] == section_day:
                # Check time overlap
                if self._time_overlap(slot['start_time'], slot['end_time'],
                                     section.get('schedule_start_time', '08:00'),
                                     section.get('schedule_end_time', '10:00')):
                    return True
        
        return False
    
    def _has_specialization(self, faculty_id: int, required_spec: str) -> bool:
        """Check if faculty has required specialization."""
        faculty = self.faculty_specs[faculty_id]
        qualifications = faculty.get('qualifications', [])
        
        return any(q['specialization'].lower() == required_spec.lower()
                  for q in qualifications)
    
    def _time_overlap(self, start1: str, end1: str, start2: str, end2: str) -> bool:
        """Check if two time ranges overlap."""
        def time_to_minutes(t: str) -> int:
            h, m = map(int, t.split(':'))
            return h * 60 + m
        
        s1, e1 = time_to_minutes(start1), time_to_minutes(end1)
        s2, e2 = time_to_minutes(start2), time_to_minutes(end2)
        
        return not (e1 <= s2 or e2 <= s1)


class FeasibilityCheck:
    """Independent feasibility validation."""
    
    def __init__(self, constraint_repair: ConstraintRepair):
        """Initialize with constraint repair engine."""
        self.repair_engine = constraint_repair
    
    def is_feasible(self, allocations: List[Tuple[int, int]]) -> bool:
        """
        Strictly validate all hard constraints.
        Rejects solution if any V_h > 0.
        
        Args:
            allocations: Solution to validate
            
        Returns:
            True only if fully feasible
        """
        violations = self.repair_engine.detect_violations(allocations)
        hard_violations = [v for v in violations
                          if v.type in ['schedule_conflict', 'overload', 'specialization_mismatch']]
        return len(hard_violations) == 0
