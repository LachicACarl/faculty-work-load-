"""Constraint repair and strict feasibility validation for workload allocation."""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Tuple


@dataclass
class ConstraintViolation:
    type: str
    faculty_id: int
    section_id: int
    severity: float
    details: str


class ConstraintRepair:
    """Detects and repairs hard-constraint violations in candidate allocations."""

    def __init__(self, faculty_specs: Dict, sections_data: Dict, policies: Dict):
        self.faculty_specs = faculty_specs
        self.sections_data = sections_data
        self.policies = policies
        self.violations: List[ConstraintViolation] = []

    @staticmethod
    def _to_minutes(value: str) -> int:
        parsed = datetime.strptime(value, "%H:%M")
        return parsed.hour * 60 + parsed.minute

    @classmethod
    def _time_overlap(cls, start1: str, end1: str, start2: str, end2: str) -> bool:
        s1, e1 = cls._to_minutes(start1), cls._to_minutes(end1)
        s2, e2 = cls._to_minutes(start2), cls._to_minutes(end2)
        if e1 <= s1 or e2 <= s2:
            raise ValueError("Schedule end time must be later than start time")
        return not (e1 <= s2 or e2 <= s1)

    def _has_specialization(self, faculty_id: int, required_spec: str) -> bool:
        if not required_spec:
            return True
        faculty = self.faculty_specs.get(faculty_id, {})
        required = required_spec.strip().casefold()
        return any(
            str(q.get("specialization", "")).strip().casefold() == required
            for q in faculty.get("qualifications", [])
        )

    def _check_availability(self, faculty_id: int, section: Dict) -> bool:
        faculty = self.faculty_specs[faculty_id]
        slots = faculty.get("availability", [])
        day = section.get("schedule_day")
        start = section.get("schedule_start_time")
        end = section.get("schedule_end_time")
        try:
            self._to_minutes(start)
            self._to_minutes(end)
            if self._to_minutes(end) <= self._to_minutes(start):
                return False
        except (TypeError, ValueError):
            return False
        return any(
            slot.get("day_of_week") == day
            and self._slot_covers(slot, start, end)
            for slot in slots
        )

    @classmethod
    def _slot_covers(cls, slot: Dict, start: str, end: str) -> bool:
        try:
            slot_start = cls._to_minutes(slot.get("start_time"))
            slot_end = cls._to_minutes(slot.get("end_time"))
            section_start = cls._to_minutes(start)
            section_end = cls._to_minutes(end)
            return slot_start < slot_end and slot_start <= section_start and section_end <= slot_end
        except (TypeError, ValueError):
            return False

    def detect_violations(self, allocations: List[Tuple[int, int]]) -> List[ConstraintViolation]:
        violations: List[ConstraintViolation] = []
        seen_sections = set()
        faculty_workload: Dict[int, int] = {}

        for faculty_id, section_id in allocations:
            if faculty_id not in self.faculty_specs or section_id not in self.sections_data:
                violations.append(ConstraintViolation(
                    "unknown_reference", faculty_id, section_id, 1.0,
                    "Allocation references an unknown faculty member or section."
                ))
                continue
            if section_id in seen_sections:
                violations.append(ConstraintViolation(
                    "duplicate_section", faculty_id, section_id, 1.0,
                    "A section is assigned more than once."
                ))
            seen_sections.add(section_id)
            faculty_workload[faculty_id] = faculty_workload.get(faculty_id, 0) + int(
                self.sections_data[section_id].get("units", 0)
            )

        # Every section in the optimization instance must be assigned exactly once.
        for section_id in set(self.sections_data) - seen_sections:
            violations.append(ConstraintViolation(
                "unassigned_section", 0, section_id, 1.0,
                "Required section has no faculty assignment."
            ))

        for faculty_id, section_id in allocations:
            faculty = self.faculty_specs.get(faculty_id)
            section = self.sections_data.get(section_id)
            if faculty is None or section is None:
                continue

            try:
                maximum = int(faculty.get("max_units", 0)) + int(faculty.get("overload_allowed", 0))
            except (TypeError, ValueError):
                maximum = -1
            if maximum < 0 or faculty_workload.get(faculty_id, 0) > maximum:
                violations.append(ConstraintViolation(
                    "overload", faculty_id, section_id, 1.0,
                    f"Workload {faculty_workload.get(faculty_id, 0)} exceeds allowed maximum {maximum}."
                ))

            if not self._check_availability(faculty_id, section):
                violations.append(ConstraintViolation(
                    "availability", faculty_id, section_id, 1.0,
                    "Faculty availability does not cover the section schedule."
                ))

            required = section.get("required_specialization")
            if self.policies.get("specialization_required", True) and required:
                if not self._has_specialization(faculty_id, required):
                    violations.append(ConstraintViolation(
                        "specialization_mismatch", faculty_id, section_id, 1.0,
                        f"Faculty lacks required specialization: {required}."
                    ))

            enrollment = section.get("enrollment")
            if enrollment is not None:
                minimum = section.get("min_class_size", 0)
                maximum_size = section.get("max_class_size")
                if enrollment < minimum or (maximum_size is not None and enrollment > maximum_size):
                    violations.append(ConstraintViolation(
                        "enrollment_bounds", faculty_id, section_id, 1.0,
                        "Section enrollment is outside the subject's approved bounds."
                    ))

        # A faculty member cannot be booked for overlapping sections.
        for faculty_id in self.faculty_specs:
            assigned = [
                self.sections_data[section_id]
                for assigned_faculty, section_id in allocations
                if assigned_faculty == faculty_id and section_id in self.sections_data
            ]
            for index, first in enumerate(assigned):
                for second in assigned[index + 1:]:
                    if first.get("schedule_day") == second.get("schedule_day"):
                        try:
                            if self._time_overlap(
                                first.get("schedule_start_time"), first.get("schedule_end_time"),
                                second.get("schedule_start_time"), second.get("schedule_end_time")
                            ):
                                violations.append(ConstraintViolation(
                                    "faculty_schedule_overlap", faculty_id,
                                    second.get("id", 0), 1.0,
                                    "Faculty member has overlapping section schedules."
                                ))
                        except (TypeError, ValueError):
                            violations.append(ConstraintViolation(
                                "invalid_schedule", faculty_id, second.get("id", 0), 1.0,
                                "Section schedule contains an invalid time interval."
                            ))

        # Room/time conflicts are independent of faculty assignment.
        for index, (faculty_a, section_a_id) in enumerate(allocations):
            section_a = self.sections_data.get(section_a_id)
            if section_a is None or not section_a.get("room"):
                continue
            for faculty_b, section_b_id in allocations[index + 1:]:
                section_b = self.sections_data.get(section_b_id)
                if (
                    section_b is not None
                    and section_a.get("room") == section_b.get("room")
                    and section_a.get("schedule_day") == section_b.get("schedule_day")
                ):
                    try:
                        if self._time_overlap(
                            section_a.get("schedule_start_time"), section_a.get("schedule_end_time"),
                            section_b.get("schedule_start_time"), section_b.get("schedule_end_time")
                        ):
                            violations.append(ConstraintViolation(
                                "room_time_conflict", faculty_b, section_b_id, 1.0,
                                f"Room {section_a.get('room')} is booked for overlapping sections."
                            ))
                    except (TypeError, ValueError):
                        violations.append(ConstraintViolation(
                            "invalid_schedule", faculty_b, section_b_id, 1.0,
                            "Section schedule contains an invalid time interval."
                        ))

        self.violations = violations
        return violations

    def repair(self, allocations: List[Tuple[int, int]], eligible_pairs: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Greedily retain feasible eligible assignments; never weaken policy."""
        repaired: List[Tuple[int, int]] = []
        assigned_sections = set()
        workload: Dict[int, int] = {}
        # Stable order makes repair reproducible.
        for faculty_id, section_id in allocations:
            if section_id in assigned_sections or (faculty_id, section_id) not in eligible_pairs:
                continue
            faculty = self.faculty_specs.get(faculty_id)
            section = self.sections_data.get(section_id)
            if faculty is None or section is None:
                continue
            candidate = repaired + [(faculty_id, section_id)]
            if self.detect_violations(candidate):
                # Current candidate may also show unassigned-section violations,
                # so test the constraints local to this candidate directly.
                if not self._candidate_pair_is_valid(faculty_id, section_id, repaired, workload):
                    continue
            if not self._candidate_pair_is_valid(faculty_id, section_id, repaired, workload):
                continue
            repaired.append((faculty_id, section_id))
            assigned_sections.add(section_id)
            workload[faculty_id] = workload.get(faculty_id, 0) + int(section["units"])
        self.violations = self.detect_violations(repaired)
        return repaired

    def _candidate_pair_is_valid(self, faculty_id: int, section_id: int, repaired: List[Tuple[int, int]], workload: Dict[int, int]) -> bool:
        faculty = self.faculty_specs[faculty_id]
        section = self.sections_data[section_id]
        if (faculty_id, section_id) not in [
            (fid, sid)
            for fid in self.faculty_specs
            for sid in self.sections_data
            if not self.policies.get("specialization_required", True)
            or not self.sections_data[sid].get("required_specialization")
            or self._has_specialization(fid, self.sections_data[sid].get("required_specialization"))
        ]:
            return False
        maximum = int(faculty.get("max_units", 0)) + int(faculty.get("overload_allowed", 0))
        if workload.get(faculty_id, 0) + int(section["units"]) > maximum:
            return False
        if not self._check_availability(faculty_id, section):
            return False
        for existing_faculty_id, existing_id in repaired:
            existing = self.sections_data[existing_id]
            if existing.get("schedule_day") == section.get("schedule_day"):
                try:
                    if self._time_overlap(
                        existing.get("schedule_start_time"), existing.get("schedule_end_time"),
                        section.get("schedule_start_time"), section.get("schedule_end_time")
                    ):
                        if existing_faculty_id == faculty_id:
                            return False
                        if section.get("room") and section.get("room") == existing.get("room"):
                            return False
                except (TypeError, ValueError):
                    return False
        return True

    def is_feasible(self, allocations: List[Tuple[int, int]]) -> bool:
        return len(self.detect_violations(allocations)) == 0


class FeasibilityCheck:
    """Strictly validate all hard constraints before allocations can be committed."""

    def __init__(self, constraint_repair: ConstraintRepair):
        self.repair_engine = constraint_repair

    def is_feasible(self, allocations: List[Tuple[int, int]]) -> bool:
        return not self.repair_engine.detect_violations(allocations)
