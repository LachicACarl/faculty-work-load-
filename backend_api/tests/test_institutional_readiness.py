"""Synthetic regression coverage for institutional-readiness defects."""
import unittest

from backend_api.optimization_engine.constraint_repair import ConstraintRepair, FeasibilityCheck
from backend_api.optimization_engine.tabu_search import TabuSearch


def fixture():
    faculty = {
        1: {
            "max_units": 6, "overload_allowed": 0,
            "qualifications": [{"specialization": "Computer Science", "proficiency_level": 1.0}],
            "availability": [{"day_of_week": 0, "start_time": "08:00", "end_time": "12:00"}],
        },
        2: {
            "max_units": 6, "overload_allowed": 0,
            "qualifications": [{"specialization": "Mathematics", "proficiency_level": 1.0}],
            "availability": [{"day_of_week": 0, "start_time": "08:00", "end_time": "12:00"}],
        },
    }
    sections = {
        101: {
            "units": 3, "required_specialization": "Computer Science",
            "schedule_day": 0, "schedule_start_time": "08:00", "schedule_end_time": "10:00",
            "enrollment": 20, "min_class_size": 1, "max_class_size": 30, "room": "A101",
        },
        102: {
            "units": 3, "required_specialization": "Mathematics",
            "schedule_day": 0, "schedule_start_time": "10:00", "schedule_end_time": "12:00",
            "enrollment": 20, "min_class_size": 1, "max_class_size": 30, "room": "A102",
        },
    }
    return faculty, sections, {"specialization_required": True, "consecutive_limit": 4}


class FeasibilityRegressionTests(unittest.TestCase):
    def setUp(self):
        faculty, sections, policy = fixture()
        self.engine = ConstraintRepair(faculty, sections, policy)
        self.validator = FeasibilityCheck(self.engine)

    def test_accepts_feasible_complete_assignment(self):
        self.assertTrue(self.validator.is_feasible([(1, 101), (2, 102)]))

    def test_rejects_missing_required_section(self):
        self.assertFalse(self.validator.is_feasible([(1, 101)]))

    def test_rejects_duplicate_section_assignment(self):
        self.assertFalse(self.validator.is_feasible([(1, 101), (2, 101), (2, 102)]))

    def test_rejects_unknown_ids(self):
        self.assertFalse(self.validator.is_feasible([(99, 101)]))
        self.assertFalse(self.validator.is_feasible([(1, 999)]))

    def test_rejects_specialization_mismatch(self):
        self.assertFalse(self.validator.is_feasible([(2, 101), (2, 102)]))

    def test_rejects_faculty_schedule_overlap(self):
        self.engine.sections_data[102]["required_specialization"] = "Computer Science"
        self.engine.sections_data[102]["schedule_start_time"] = "09:30"
        self.assertFalse(self.validator.is_feasible([(1, 101), (1, 102)]))

    def test_rejects_room_time_collision(self):
        self.engine.sections_data[102]["schedule_start_time"] = "09:30"
        self.engine.sections_data[102]["room"] = "A101"
        self.assertFalse(self.validator.is_feasible([(1, 101), (2, 102)]))

    def test_rejects_invalid_schedule_time(self):
        self.engine.sections_data[101]["schedule_start_time"] = "25:00"
        self.assertFalse(self.validator.is_feasible([(1, 101), (2, 102)]))

    def test_rejects_consecutive_teaching_time_over_policy_limit(self):
        self.engine.policies["consecutive_limit"] = 1
        self.engine.sections_data[102]["required_specialization"] = "Computer Science"
        self.assertFalse(self.validator.is_feasible([(1, 101), (1, 102)]))


class TabuSearchRegressionTests(unittest.TestCase):
    def test_refine_accepts_list_and_callable(self):
        search = TabuSearch(tabu_tenure=2, max_iterations=2)
        result = search.refine(
            initial_solution=[(1, 101), (2, 102)],
            fitness_func=lambda allocations: 1.0 if len(allocations) == 2 else 0.0,
            eligible_pairs=[(1, 101), (2, 102)],
        )
        self.assertEqual(set(result), {(1, 101), (2, 102)})



class SchemaRegressionTests(unittest.TestCase):
    def test_rejects_invalid_clock_time(self):
        from pydantic import ValidationError
        from backend_api.schemas import AvailabilityBase, SectionBase
        with self.assertRaises(ValidationError):
            AvailabilityBase(day_of_week=0, start_time="25:00", end_time="26:00")
        with self.assertRaises(ValidationError):
            SectionBase(
                subject_id=1,
                section_code="X-1",
                semester="2026-1",
                schedule_day=0,
                schedule_start_time="08:00",
                schedule_end_time="25:00",
            )

    def test_rejects_invalid_class_size_bounds(self):
        from pydantic import ValidationError
        from backend_api.schemas import SubjectBase
        with self.assertRaises(ValidationError):
            SubjectBase(
                code="BAD-1",
                name="Invalid bounds",
                units=3,
                min_class_size=30,
                max_class_size=10,
            )

if __name__ == "__main__":
    unittest.main()
