import unittest

from fastapi.testclient import TestClient

from backend_api.main import app


class WorkloadOptimizeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_optimize_requires_sections(self) -> None:
        response = self.client.post("/api/workload/optimize", json={"faculty": []})
        self.assertEqual(response.status_code, 400)
        self.assertIn("sections payload is required", response.text)

    def test_optimize_requires_faculty(self) -> None:
        response = self.client.post(
            "/api/workload/optimize",
            json={
                "sections": [
                    {
                        "id": "SEC1",
                        "code": "IT501",
                        "required_specialization": "Algorithms",
                        "day": "Mon",
                        "start_time": 8.0,
                        "end_time": 11.0,
                        "units": 3.0,
                    }
                ]
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("faculty payload is required", response.text)

    def test_optimize_returns_solution_for_valid_payload(self) -> None:
        payload = {
            "sections": [
                {
                    "id": "SEC1",
                    "code": "IT501",
                    "required_specialization": "Algorithms",
                    "day": "Mon",
                    "start_time": 8.0,
                    "end_time": 11.0,
                    "units": 3.0,
                },
                {
                    "id": "SEC2",
                    "code": "CS510",
                    "required_specialization": "Machine Learning",
                    "day": "Tue",
                    "start_time": 8.0,
                    "end_time": 11.0,
                    "units": 3.0,
                },
            ],
            "faculty": [
                {
                    "id": "F1",
                    "name": "Dr. A",
                    "specializations": ["Algorithms"],
                    "min_units": 3.0,
                    "max_units": 9.0,
                },
                {
                    "id": "F2",
                    "name": "Dr. B",
                    "specializations": ["Machine Learning"],
                    "min_units": 3.0,
                    "max_units": 9.0,
                },
            ],
            "policy_profile": {
                "id": "balanced",
                "name": "Balanced Baseline",
                "full_time_max_units": 21.0,
                "part_time_max_units": 12.0,
                "allowable_overload": 3.0,
                "specialization_required": True,
                "consecutive_limit": 2,
                "balance_priority": 70.0,
                "utilization_target": 80.0,
            },
            "objective_weights": {
                "spec_match": 12.0,
                "utilization": 5.0,
                "conflict": 50.0,
                "policy_violation": 42.0,
                "unassigned": 30.0,
            },
        }

        response = self.client.post("/api/workload/optimize", json=payload)
        self.assertEqual(response.status_code, 200)
        body = response.json()

        self.assertEqual(body["status"], "success")
        self.assertIn("policy_profile", body)
        self.assertIn("objective_weights", body)
        self.assertIn("data", body)
        self.assertIn("allocation", body["data"])
        self.assertIn("metrics", body["data"])
        self.assertIn("explainable_recommendations", body["data"])

    def test_policy_profiles_are_listed(self) -> None:
        response = self.client.get("/api/workload/policy-profiles")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIsInstance(body, list)
        self.assertGreaterEqual(len(body), 1)

    def test_institutional_snapshot_is_available(self) -> None:
        response = self.client.get("/api/institutional/snapshot")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("faculty", body)
        self.assertIn("curriculum", body)
        self.assertIn("sources", body)

    def test_reports_and_analytics_endpoints_exist(self) -> None:
        report_response = self.client.get("/api/reports/workload-summary")
        analytics_response = self.client.get("/api/analytics/kpi-history")

        self.assertEqual(report_response.status_code, 200)
        self.assertEqual(analytics_response.status_code, 200)
        self.assertIn("summary", report_response.json())
        self.assertIn("trend", analytics_response.json())


if __name__ == "__main__":
    unittest.main()
