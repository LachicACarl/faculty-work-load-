import unittest
import json
import os
import subprocess
import sys
import tempfile
import copy
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend_api.core.database import Base
from backend_api.models import Allocation
from backend_api.optimization_engine import (
    ExperimentRunner,
    OptimizationConfig,
    paired_method_comparison,
    summarize_trials,
)
from backend_api.optimization_engine.fitness import FitnessEvaluator
from backend_api.optimization_engine.experiment_authorization import (
    CONTROLLED_EXPERIMENT_PURPOSE,
    ExperimentAuthorizationError,
    ExperimentAuthorizationGrant,
    authorization_scope_sha256,
    validate_authorization_grant,
)
from backend_api.optimization_engine.experiment_cli import (
    PROJECT_ROOT,
    _assert_isolated_new_database,
    main as experiment_cli_main,
    run_comparison,
)
from backend_api.optimization_engine.analysis import experiment_completeness
from backend_api.optimization_engine.experiment_models import (
    ExperimentBase,
    ExperimentRun,
    ExperimentTrial,
)
from backend_api.tests.test_optimization_engine import build_fixture
from backend_api.tests.experiment_authorization_helpers import (
    SyntheticAuthorizationSigner,
    synthetic_snapshot_bytes,
)


def analysis_row(method, seed, score, feasible=True, status="succeeded", **updates):
    row = {
        "trial_id": f"trial-{method}-{seed}",
        "experiment_id": "analysis-manifest",
        "method": method,
        "implementation_version": "stage-5.4.2-v1",
        "input_fingerprint": "same-synthetic-input",
        "input_provenance": "synthetic analysis fixture",
        "input_snapshot_json": json.dumps({"provenance": "synthetic", "id": 1}),
        "seed": seed,
        "configuration_json": json.dumps({
            "seed": seed, "ga_population_size": 4, "ga_generations": 3,
        }),
        "evaluation_budget": 20,
        "stopping_condition": "objective_evaluations",
        "environment_json": json.dumps({
            "python_version": "synthetic", "source_control": {
                "revision": "test-revision", "working_tree_dirty": False,
                "status_sha256": "test-status",
            },
        }),
        "diagnostics_json": json.dumps({"objective_direction": "maximize"}),
        "objective_score": score,
        "feasible": feasible,
        "status": status,
        "objective_evaluations": 10,
        "runtime_seconds": 0.01,
    }
    row.update(updates)
    return row


class ExperimentCliPathGuardTests(unittest.TestCase):
    def test_relative_application_path_uses_process_cwd_not_project_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            application_db = root / "relative-app.sqlite"
            output_path = application_db.resolve()
            original_cwd = Path.cwd()
            try:
                os.chdir(root)
                engine = create_engine("sqlite:///relative-app.sqlite")
                try:
                    connect_args, _ = engine.dialect.create_connect_args(engine.url)
                    self.assertEqual(Path(connect_args[0]).resolve(), output_path)
                finally:
                    engine.dispose()
                with patch(
                    "backend_api.optimization_engine.experiment_cli.settings.DATABASE_URL",
                    "sqlite:///relative-app.sqlite",
                ):
                    with self.assertRaisesRegex(
                        ValueError, "configured application database"
                    ):
                        _assert_isolated_new_database(output_path)
            finally:
                os.chdir(original_cwd)

    def test_absolute_application_path_remains_protected(self):
        with tempfile.TemporaryDirectory() as directory:
            application_db = Path(directory) / "absolute-app.sqlite"
            url = URL.create("sqlite", database=str(application_db)).render_as_string(
                hide_password=False
            )
            with patch(
                "backend_api.optimization_engine.experiment_cli.settings.DATABASE_URL",
                url,
            ):
                with self.assertRaisesRegex(
                    ValueError, "configured application database"
                ):
                    _assert_isolated_new_database(application_db.resolve())

    def test_percent_encoded_url_path_matches_sqlalchemy_literal_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            application_db = root / "relative%20name.sqlite"
            output_path = application_db.resolve()
            original_cwd = Path.cwd()
            try:
                os.chdir(root)
                engine = create_engine("sqlite:///relative%20name.sqlite")
                try:
                    connect_args, _ = engine.dialect.create_connect_args(engine.url)
                    self.assertEqual(Path(connect_args[0]).resolve(), output_path)
                finally:
                    engine.dispose()
                with patch(
                    "backend_api.optimization_engine.experiment_cli.settings.DATABASE_URL",
                    "sqlite:///relative%20name.sqlite",
                ):
                    with self.assertRaisesRegex(
                        ValueError, "configured application database"
                    ):
                        _assert_isolated_new_database(output_path)
            finally:
                os.chdir(original_cwd)

    def test_existing_output_file_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "existing-results.sqlite"
            output.write_bytes(b"leave this file untouched")
            before = output.read_bytes()
            with patch(
                "backend_api.optimization_engine.experiment_cli.settings.DATABASE_URL",
                "sqlite:///:memory:",
            ):
                with self.assertRaisesRegex(FileExistsError, "already exists"):
                    _assert_isolated_new_database(output.resolve())
            self.assertEqual(output.read_bytes(), before)

    def test_known_production_path_remains_protected(self):
        with patch(
            "backend_api.optimization_engine.experiment_cli.settings.DATABASE_URL",
            "sqlite:///:memory:",
        ):
            with self.assertRaisesRegex(ValueError, "production workload database"):
                _assert_isolated_new_database(PROJECT_ROOT / "faculty_workload.db")

    def test_file_uri_and_uri_parameters_are_rejected(self):
        uri_urls = (
            "sqlite:///file:relative-app.sqlite?uri=true&mode=ro",
            "sqlite:///file:relative%20app.sqlite?uri=true&mode=rw",
            "sqlite:///file:relative-app.sqlite?uri=true&mode=rwc",
            "sqlite:///file:relative-app.sqlite?uri=true&mode=memory",
            "sqlite:///file%3Arelative-app.sqlite?uri=true&mode=ro",
            "sqlite:///relative-app.sqlite?mode=ro",
            "sqlite:///relative-app.sqlite?uri=false",
        )
        with tempfile.TemporaryDirectory() as directory:
            output = (Path(directory) / "results.sqlite").resolve()
            for url in uri_urls:
                with self.subTest(url=url), patch(
                    "backend_api.optimization_engine.experiment_cli.settings.DATABASE_URL",
                    url,
                ):
                    with self.assertRaisesRegex(ValueError, "URI database URLs"):
                        _assert_isolated_new_database(output)

    def test_uri_configuration_is_rejected_before_engine_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "synthetic-input.json"
            source.write_text("{}", encoding="utf-8")
            output = root / "results.sqlite"
            uri_url = "sqlite:///file:app.sqlite?uri=true&mode=rw"
            with patch(
                "backend_api.optimization_engine.experiment_cli.settings.DATABASE_URL",
                uri_url,
            ), patch(
                "backend_api.optimization_engine.experiment_cli.create_engine"
            ) as create_engine_mock:
                with self.assertRaisesRegex(ValueError, "URI database URLs"):
                    run_comparison(
                        source, output, "must reject", [1], 1, None,
                        root / "approval.json", CONTROLLED_EXPERIMENT_PURPOSE,
                        authorization_service=object(),
                    )
                create_engine_mock.assert_not_called()

    def test_plain_in_memory_application_url_is_allowed(self):
        with tempfile.TemporaryDirectory() as directory:
            output = (Path(directory) / "new-results.sqlite").resolve()
            with patch(
                "backend_api.optimization_engine.experiment_cli.settings.DATABASE_URL",
                "sqlite:///:memory:",
            ):
                _assert_isolated_new_database(output)


class ExperimentFrameworkTests(unittest.TestCase):
    def setUp(self):
        self.faculty, self.sections, self.policies = build_fixture()
        self.authorizer = SyntheticAuthorizationSigner(self)
        self.config = OptimizationConfig(
            seed=11,
            ga_population_size=4,
            ga_generations=3,
            tabu_tenure=2,
            tabu_max_iterations=4,
        )
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        ExperimentBase.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.runner = ExperimentRunner(
            self.db, authorization_service=self.authorizer
        )

    def _manifest(self, name, seeds, budget, faculty=None, sections=None):
        faculty = faculty if faculty is not None else self.faculty
        sections = sections if sections is not None else self.sections
        provenance = "synthetic test fixture"
        snapshot_bytes = synthetic_snapshot_bytes(
            faculty, sections, self.policies, provenance
        )
        snapshot_path = self.authorizer.snapshot_path(name, snapshot_bytes)
        self.runner.authorization_context = self.authorizer.sign(
            snapshot_path=snapshot_path,
            result_database="sqlite::memory:",
            name=name,
            seeds=seeds,
            budget=budget,
            config=self.config,
            provenance=provenance,
            faculty=faculty,
            sections=sections,
            policies=self.policies,
        )
        return self.runner.create_experiment(
            name,
            faculty,
            sections,
            self.policies,
            self.config,
            seeds,
            budget,
            input_provenance=provenance,
        )

    def test_missing_authorization_blocks_manifest_before_any_persistence(self):
        runner = ExperimentRunner(self.db)
        with self.assertRaisesRegex(ExperimentAuthorizationError, "disabled"):
            runner.create_experiment(
                "unsigned", self.faculty, self.sections, self.policies,
                self.config, [11], 5,
                input_provenance="synthetic test fixture",
            )
        self.assertEqual(self.db.query(ExperimentRun).count(), 0)
        self.assertEqual(self.db.query(ExperimentTrial).count(), 0)

    def test_direct_runner_trial_without_service_is_denied_before_persistence(self):
        runner = ExperimentRunner(self.db)
        with self.assertRaisesRegex(ExperimentAuthorizationError, "disabled"):
            runner.run_trial(
                "missing-manifest", "ga_only", 11,
                self.faculty, self.sections, self.policies,
                self.config, 5, input_provenance="synthetic test fixture",
            )
        self.assertEqual(self.db.query(ExperimentRun).count(), 0)
        self.assertEqual(self.db.query(ExperimentTrial).count(), 0)

    def test_authorization_ledger_failure_blocks_manifest_and_trials(self):
        class UnavailableLedger:
            def authorize_manifest(self, *args, **kwargs):
                raise ExperimentAuthorizationError("authorization ledger unavailable")

            def authorize_trial(self, *args, **kwargs):
                raise ExperimentAuthorizationError("authorization ledger unavailable")

        provenance = "synthetic test fixture"
        name = "ledger-outage"
        snapshot_bytes = synthetic_snapshot_bytes(
            self.faculty, self.sections, self.policies, provenance
        )
        snapshot_path = self.authorizer.snapshot_path(name, snapshot_bytes)
        context = self.authorizer.sign(
            snapshot_path=snapshot_path, result_database="sqlite::memory:",
            name=name, seeds=[11], budget=5, config=self.config,
            provenance=provenance, faculty=self.faculty,
            sections=self.sections, policies=self.policies,
        )
        runner = ExperimentRunner(
            self.db, authorization_context=context,
            authorization_service=UnavailableLedger(),
        )
        with self.assertRaisesRegex(ExperimentAuthorizationError, "ledger unavailable"):
            runner.create_experiment(
                name, self.faculty, self.sections, self.policies,
                self.config, [11], 5, input_provenance=provenance,
            )
        self.assertEqual(self.db.query(ExperimentRun).count(), 0)
        self.assertEqual(self.db.query(ExperimentTrial).count(), 0)

    def test_invalid_signature_and_incomplete_human_review_block_before_persistence(self):
        name = "invalid-evidence"
        provenance = "synthetic test fixture"
        snapshot_bytes = synthetic_snapshot_bytes(
            self.faculty, self.sections, self.policies, provenance
        )
        snapshot_path = self.authorizer.snapshot_path(name, snapshot_bytes)
        context = self.authorizer.sign(
            snapshot_path=snapshot_path, result_database="sqlite::memory:",
            name=name, seeds=[11], budget=5, config=self.config,
            provenance=provenance, faculty=self.faculty,
            sections=self.sections, policies=self.policies,
        )
        invalid_envelope = copy.deepcopy(context.envelope)
        invalid_envelope["signature_ed25519"] = "AA=="
        self.runner.authorization_context = type(context)(
            invalid_envelope, context.snapshot_bytes, context.snapshot_path,
            context.result_database, context.purpose,
        )
        with self.assertRaisesRegex(ExperimentAuthorizationError, "signature"):
            self.runner.create_experiment(
                name, self.faculty, self.sections, self.policies,
                self.config, [11], 5, input_provenance=provenance,
            )

        incomplete = self.authorizer.sign(
            snapshot_path=snapshot_path, result_database="sqlite::memory:",
            name=name, seeds=[11], budget=5, config=self.config,
            provenance=provenance, faculty=self.faculty,
            sections=self.sections, policies=self.policies,
            payload_updates={"human_review": {"status": "pending"}},
        )
        self.runner.authorization_context = incomplete
        with self.assertRaisesRegex(ExperimentAuthorizationError, "human"):
            self.runner.create_experiment(
                name, self.faculty, self.sections, self.policies,
                self.config, [11], 5, input_provenance=provenance,
            )
        self.assertEqual(self.db.query(ExperimentRun).count(), 0)
        self.assertEqual(self.db.query(ExperimentTrial).count(), 0)

    def test_caller_environment_key_cannot_enable_execution(self):
        provenance = "synthetic test fixture"
        name = "missing-trust-key"
        snapshot_bytes = synthetic_snapshot_bytes(
            self.faculty, self.sections, self.policies, provenance
        )
        snapshot_path = self.authorizer.snapshot_path(name, snapshot_bytes)
        context = self.authorizer.sign(
            snapshot_path=snapshot_path, result_database="sqlite::memory:",
            name=name, seeds=[11], budget=5, config=self.config,
            provenance=provenance, faculty=self.faculty,
            sections=self.sections, policies=self.policies,
        )
        runner = ExperimentRunner(self.db, authorization_context=context)
        with patch.dict(os.environ, {
            "OFWAS_EXPERIMENT_TRUSTED_PUBLIC_KEY_FILE": str(self.authorizer.public_key_path),
        }):
            with self.assertRaisesRegex(ExperimentAuthorizationError, "disabled"):
                runner.create_experiment(
                    name, self.faculty, self.sections, self.policies,
                    self.config, [11], 5, input_provenance=provenance,
                )
        self.assertEqual(self.db.query(ExperimentRun).count(), 0)
        self.assertEqual(self.db.query(ExperimentTrial).count(), 0)

    def test_snapshot_substitution_is_rejected_before_manifest_persistence(self):
        experiment_id = self._manifest("snapshot-substitution-source", [11], 5)
        source = self.db.get(ExperimentRun, experiment_id)
        envelope = json.loads(source.authorization_json)
        context = self.authorizer.sign(
            snapshot_path=envelope["payload"]["snapshot_path"],
            result_database="sqlite::memory:",
            name="snapshot-substitution-target", seeds=[11], budget=5,
            config=self.config, provenance="synthetic test fixture",
            faculty=self.faculty, sections=self.sections, policies=self.policies,
        )
        self.db.delete(source)
        self.db.commit()
        tampered = type(context)(
            context.envelope,
            context.snapshot_bytes + b" ",
            context.snapshot_path,
            context.result_database,
            context.purpose,
        )
        self.runner.authorization_context = tampered
        with self.assertRaises(ExperimentAuthorizationError):
            self.runner.create_experiment(
                "snapshot-substitution-target", self.faculty, self.sections,
                self.policies, self.config, [11], 5,
                input_provenance="synthetic test fixture",
            )
        self.assertEqual(self.db.query(ExperimentRun).count(), 0)
        self.assertEqual(self.db.query(ExperimentTrial).count(), 0)

    def test_result_database_binding_mismatch_is_rejected_before_manifest(self):
        provenance = "synthetic test fixture"
        name = "wrong-result-database"
        snapshot_bytes = synthetic_snapshot_bytes(
            self.faculty, self.sections, self.policies, provenance
        )
        snapshot_path = self.authorizer.snapshot_path(name, snapshot_bytes)
        self.runner.authorization_context = self.authorizer.sign(
            snapshot_path=snapshot_path,
            result_database=self.authorizer.root / "different-results.sqlite",
            name=name, seeds=[11], budget=5, config=self.config,
            provenance=provenance, faculty=self.faculty,
            sections=self.sections, policies=self.policies,
        )
        with self.assertRaisesRegex(ExperimentAuthorizationError, "does not match"):
            self.runner.create_experiment(
                name, self.faculty, self.sections, self.policies,
                self.config, [11], 5, input_provenance=provenance,
            )
        self.assertEqual(self.db.query(ExperimentRun).count(), 0)
        self.assertEqual(self.db.query(ExperimentTrial).count(), 0)

    def test_host_grant_with_modified_plan_binding_is_rejected(self):
        provenance = "synthetic test fixture"
        name = "modified-grant-plan"
        snapshot_bytes = synthetic_snapshot_bytes(
            self.faculty, self.sections, self.policies, provenance
        )
        snapshot_path = self.authorizer.snapshot_path(name, snapshot_bytes)
        context = self.authorizer.sign(
            snapshot_path=snapshot_path, result_database="sqlite::memory:",
            name=name, seeds=[11], budget=5, config=self.config,
            provenance=provenance, faculty=self.faculty,
            sections=self.sections, policies=self.policies,
        )
        payload = context.envelope["payload"]
        scope = {
            "experiment_name": name,
            "methods": ["ga_only", "tabu_only", "hybrid"],
            "seeds": [11],
            "evaluation_budget": 5,
            "configuration": self.config.as_dict(),
            "stopping_condition": "objective_evaluations",
            "input_provenance": provenance,
            "faculty_specs": self.faculty,
            "sections_data": self.sections,
            "policies": self.policies,
        }
        grant = ExperimentAuthorizationGrant(
            experiment_id="host-issued-id",
            approval_id=payload["approval_id"],
            scope_sha256=authorization_scope_sha256(scope),
            payload=payload,
        )
        with self.assertRaisesRegex(ExperimentAuthorizationError, "does not match"):
            validate_authorization_grant(
                grant, context, "different-experiment-id", scope
            )
        with self.assertRaisesRegex(ExperimentAuthorizationError, "does not match"):
            validate_authorization_grant(
                ExperimentAuthorizationGrant(
                    experiment_id="host-issued-id",
                    approval_id=payload["approval_id"],
                    scope_sha256=authorization_scope_sha256(scope),
                    payload=payload,
                ),
                context,
                "host-issued-id",
                {**scope, "seeds": [12]},
            )
        self.assertEqual(self.db.query(ExperimentRun).count(), 0)
        self.assertEqual(self.db.query(ExperimentTrial).count(), 0)

    def test_already_issued_grant_cannot_enter_public_runner_with_fresh_database(self):
        provenance = "synthetic test fixture"
        name = "grant-replay-attempt"
        snapshot_bytes = synthetic_snapshot_bytes(
            self.faculty, self.sections, self.policies, provenance
        )
        snapshot_path = self.authorizer.snapshot_path(name, snapshot_bytes)
        context = self.authorizer.sign(
            snapshot_path=snapshot_path, result_database="sqlite::memory:",
            name=name, seeds=[11], budget=5, config=self.config,
            provenance=provenance, faculty=self.faculty,
            sections=self.sections, policies=self.policies,
        )
        scope = {
            "experiment_name": name,
            "methods": ["ga_only", "tabu_only", "hybrid"],
            "seeds": [11],
            "evaluation_budget": 5,
            "configuration": self.config.as_dict(),
            "stopping_condition": "objective_evaluations",
            "input_provenance": provenance,
            "faculty_specs": self.faculty,
            "sections_data": self.sections,
            "policies": self.policies,
        }
        grant = self.authorizer.authorize_manifest(
            context, experiment_id="issued-before-database-recreation", **scope
        )
        recreated_engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        ExperimentBase.metadata.create_all(recreated_engine)
        recreated_db = sessionmaker(bind=recreated_engine)()
        self.addCleanup(recreated_engine.dispose)
        self.addCleanup(recreated_db.close)

        with self.assertRaises(TypeError):
            ExperimentRunner(
                recreated_db,
                authorization_context=context,
                authorization_service=self.authorizer,
                authorization_grant=grant,
            )
        self.assertEqual(recreated_db.query(ExperimentRun).count(), 0)
        self.assertEqual(recreated_db.query(ExperimentTrial).count(), 0)

        replay_runner = ExperimentRunner(
            recreated_db,
            authorization_context=context,
            authorization_service=self.authorizer,
        )
        with self.assertRaisesRegex(ExperimentAuthorizationError, "consumed"):
            replay_runner.create_experiment(
                name, self.faculty, self.sections, self.policies,
                self.config, [11], 5, input_provenance=provenance,
            )
        self.assertEqual(recreated_db.query(ExperimentRun).count(), 0)
        self.assertEqual(recreated_db.query(ExperimentTrial).count(), 0)

    def test_synthetic_ledger_atomically_allows_only_one_concurrent_consumption(self):
        provenance = "synthetic test fixture"
        name = "concurrent-consumption"
        snapshot_bytes = synthetic_snapshot_bytes(
            self.faculty, self.sections, self.policies, provenance
        )
        snapshot_path = self.authorizer.snapshot_path(name, snapshot_bytes)
        context = self.authorizer.sign(
            snapshot_path=snapshot_path, result_database="sqlite::memory:",
            name=name, seeds=[11], budget=5, config=self.config,
            provenance=provenance, faculty=self.faculty,
            sections=self.sections, policies=self.policies,
        )
        scope = {
            "experiment_name": name,
            "methods": ["ga_only", "tabu_only", "hybrid"],
            "seeds": [11],
            "evaluation_budget": 5,
            "configuration": self.config.as_dict(),
            "stopping_condition": "objective_evaluations",
            "input_provenance": provenance,
            "faculty_specs": self.faculty,
            "sections_data": self.sections,
            "policies": self.policies,
        }

        def consume(index):
            try:
                return self.authorizer.authorize_manifest(
                    context, experiment_id=f"concurrent-{index}", **scope
                )
            except ExperimentAuthorizationError:
                return None

        with ThreadPoolExecutor(max_workers=8) as executor:
            grants = list(executor.map(consume, range(8)))
        self.assertEqual(sum(grant is not None for grant in grants), 1)

    def test_expired_and_wrong_purpose_authorizations_are_rejected(self):
        provenance = "synthetic test fixture"
        name = "stale-or-wrong-purpose"
        snapshot_bytes = synthetic_snapshot_bytes(
            self.faculty, self.sections, self.policies, provenance
        )
        snapshot_path = self.authorizer.snapshot_path(name, snapshot_bytes)
        expired = self.authorizer.sign(
            snapshot_path=snapshot_path, result_database="sqlite::memory:",
            name=name, seeds=[11], budget=5, config=self.config,
            provenance=provenance, faculty=self.faculty,
            sections=self.sections, policies=self.policies,
            payload_updates={
                "approved_at": "2020-01-01T00:00:00+00:00",
                "expires_at": "2020-01-02T00:00:00+00:00",
            },
        )
        self.runner.authorization_context = expired
        with self.assertRaisesRegex(ExperimentAuthorizationError, "stale"):
            self.runner.create_experiment(
                name, self.faculty, self.sections, self.policies,
                self.config, [11], 5, input_provenance=provenance,
            )

        valid = self.authorizer.sign(
            snapshot_path=snapshot_path, result_database="sqlite::memory:",
            name=name, seeds=[11], budget=5, config=self.config,
            provenance=provenance, faculty=self.faculty,
            sections=self.sections, policies=self.policies,
        )
        wrong_purpose = type(valid)(
            valid.envelope, valid.snapshot_bytes, valid.snapshot_path,
            valid.result_database, "other-purpose",
        )
        self.runner.authorization_context = wrong_purpose
        with self.assertRaisesRegex(ExperimentAuthorizationError, "purpose"):
            self.runner.create_experiment(
                name, self.faculty, self.sections, self.policies,
                self.config, [11], 5, input_provenance=provenance,
            )
        self.assertEqual(self.db.query(ExperimentRun).count(), 0)

    def test_approval_cannot_be_reused_for_another_manifest(self):
        experiment_id = self._manifest("single-use-approval", [11], 5)
        experiment = self.db.get(ExperimentRun, experiment_id)
        context = self.runner.authorization_context
        with self.assertRaisesRegex(ExperimentAuthorizationError, "consumed"):
            self.runner.create_experiment(
                experiment.name, self.faculty, self.sections, self.policies,
                self.config, [11], 5,
                input_provenance="synthetic test fixture",
            )
        self.assertEqual(self.db.query(ExperimentRun).count(), 1)

    def test_test_ledger_rejects_reuse_after_results_database_recreation(self):
        with tempfile.TemporaryDirectory() as directory:
            result_path = (Path(directory) / "results.sqlite").resolve()
            provenance = "synthetic test fixture"
            name = "single-use-across-temporary-databases"
            snapshot_bytes = synthetic_snapshot_bytes(
                self.faculty, self.sections, self.policies, provenance
            )
            snapshot_path = self.authorizer.snapshot_path(name, snapshot_bytes)
            context = self.authorizer.sign(
                snapshot_path=snapshot_path, result_database=result_path,
                name=name, seeds=[11], budget=5, config=self.config,
                provenance=provenance, faculty=self.faculty,
                sections=self.sections, policies=self.policies,
            )

            first_engine = create_engine(URL.create(
                "sqlite", database=str(result_path)
            ))
            ExperimentBase.metadata.create_all(first_engine)
            first_db = sessionmaker(bind=first_engine)()
            first_runner = ExperimentRunner(
                first_db,
                authorization_context=context,
                authorization_service=self.authorizer,
            )
            first_runner.create_experiment(
                name, self.faculty, self.sections, self.policies,
                self.config, [11], 5, input_provenance=provenance,
            )
            self.assertEqual(first_db.query(ExperimentRun).count(), 1)
            first_db.close()
            first_engine.dispose()

            result_path.unlink()
            recreated_engine = create_engine(URL.create(
                "sqlite", database=str(result_path)
            ))
            ExperimentBase.metadata.create_all(recreated_engine)
            recreated_db = sessionmaker(bind=recreated_engine)()
            try:
                recreated_runner = ExperimentRunner(
                    recreated_db,
                    authorization_context=context,
                    authorization_service=self.authorizer,
                )
                with self.assertRaisesRegex(
                    ExperimentAuthorizationError, "consumed"
                ):
                    recreated_runner.create_experiment(
                        name, self.faculty, self.sections, self.policies,
                        self.config, [11], 5, input_provenance=provenance,
                    )
                self.assertEqual(recreated_db.query(ExperimentRun).count(), 0)
                self.assertEqual(recreated_db.query(ExperimentTrial).count(), 0)
            finally:
                recreated_db.close()
                recreated_engine.dispose()

    def test_direct_runner_rechecks_signed_evidence_before_trial_persistence(self):
        experiment_id = self._manifest("direct-runner", [11], 5)
        experiment = self.db.get(ExperimentRun, experiment_id)
        envelope = json.loads(experiment.authorization_json)
        envelope["signature_ed25519"] = "AA=="
        experiment.authorization_json = json.dumps(envelope)
        self.db.commit()

        with self.assertRaisesRegex(ExperimentAuthorizationError, "signature"):
            self.runner.run_trial(
                experiment_id, "ga_only", 11, self.faculty, self.sections,
                self.policies, self.config, 5,
                input_provenance="synthetic test fixture",
            )
        self.assertEqual(self.db.query(ExperimentTrial).count(), 0)

    def test_signed_synthetic_test_authorization_allows_scoped_execution(self):
        experiment_id = self._manifest("synthetic-test-only", [11], 5)
        result = self.runner.run_trial(
            experiment_id, "ga_only", 11, self.faculty, self.sections,
            self.policies, self.config, 5,
            input_provenance="synthetic test fixture",
        )
        self.assertNotEqual(result.status, "failed")
        self.assertEqual(self.db.query(ExperimentTrial).count(), 1)
        saved = self.db.query(ExperimentRun).one()
        self.assertTrue(saved.authorization_id)
        self.assertIn("TEST_ONLY", saved.authorization_json)

    def tearDown(self):
        self.db.close()
        ExperimentBase.metadata.drop_all(self.engine)
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_experiment_models_use_separate_metadata_with_constraints(self):
        app_tables = set(Base.metadata.tables)
        self.assertNotIn("experiment_runs", app_tables)
        self.assertNotIn("experiment_trials", app_tables)
        self.assertEqual(
            set(ExperimentBase.metadata.tables),
            {"experiment_runs", "experiment_trials"},
        )
        trial_table = ExperimentBase.metadata.tables["experiment_trials"]
        self.assertEqual(
            [fk.target_fullname for fk in trial_table.foreign_keys],
            ["experiment_runs.experiment_id"],
        )
        constraints = inspect(self.engine).get_unique_constraints("experiment_trials")
        self.assertIn(
            {"name": "uq_experiment_trial_method_seed",
             "column_names": ["experiment_id", "method", "seed"]},
            constraints,
        )

    def test_import_order_never_registers_experiments_on_application_base(self):
        checks = (
            "from backend_api.core.database import Base; import backend_api.models; "
            "import backend_api.optimization_engine.experiment_models; "
            "assert not {'experiment_runs', 'experiment_trials'} & set(Base.metadata.tables)",
            "from backend_api.optimization_engine.experiment_models import ExperimentBase; "
            "import backend_api.models; from backend_api.core.database import Base; "
            "assert not {'experiment_runs', 'experiment_trials'} & set(Base.metadata.tables); "
            "assert {'experiment_runs', 'experiment_trials'} == set(ExperimentBase.metadata.tables)",
        )
        environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", DEBUG="false")
        for code in checks:
            with self.subTest(import_order=code[:35]):
                completed = subprocess.run(
                    [sys.executable, "-B", "-c", code],
                    cwd=PROJECT_ROOT,
                    env=environment,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_methods_share_fingerprint_and_do_not_write_live_allocations(self):
        experiment_id = self._manifest("comparison", [11], 20)
        results = [
            self.runner.run_trial(
                experiment_id, method, 11, self.faculty, self.sections,
                self.policies, self.config, 20,
                input_provenance="synthetic test fixture",
            )
            for method in ("ga_only", "tabu_only", "hybrid")
        ]
        self.assertEqual({result.input_fingerprint for result in results}, {
            results[0].input_fingerprint
        })
        self.assertTrue(all(result.status != "failed" for result in results))
        self.assertTrue(all(result.objective_evaluations <= 20 for result in results))
        self.assertTrue(all(
            result.diagnostics["objective_evaluations"] == result.objective_evaluations
            for result in results
        ))
        self.assertEqual(self.db.query(Allocation).count(), 0)
        self.assertEqual(self.db.query(ExperimentRun).count(), 1)
        self.assertEqual(self.db.query(ExperimentTrial).count(), 3)
        saved_experiment = self.db.query(ExperimentRun).one()
        self.assertEqual(saved_experiment.planned_trial_count, 3)
        self.assertEqual(
            json.loads(saved_experiment.input_snapshot_json)["provenance"],
            "synthetic test fixture",
        )
        completeness = experiment_completeness(
            {"planned_trial_count": saved_experiment.planned_trial_count},
            [{"status": trial.status}
             for trial in self.db.query(ExperimentTrial).all()],
        )
        self.assertTrue(completeness["complete"])
        for trial in self.db.query(ExperimentTrial).all():
            self.assertEqual(trial.input_provenance, "synthetic test fixture")
            self.assertEqual(trial.implementation_version, "stage-5.4.2-v1")
            self.assertTrue(trial.termination_reason)
            self.assertEqual(trial.objective_evaluations,
                             json.loads(trial.diagnostics_json)["objective_evaluations"])
            self.assertEqual(json.loads(trial.input_snapshot_json)["provenance"],
                             "synthetic test fixture")
            self.assertIsInstance(json.loads(trial.allocations_json), list)
            self.assertIn("python_version", json.loads(trial.environment_json))
            self.assertEqual(json.loads(trial.configuration_json)["seed"], trial.seed)

    def test_ga_only_and_tabu_only_have_distinct_execution_paths(self):
        ga_experiment = self._manifest("ga", [11], 12)
        tabu_experiment = self._manifest("tabu", [11], 12)
        with patch("backend_api.optimization_engine.experiment.TabuSearch.refine",
                   side_effect=AssertionError("Tabu invoked by GA-only")) as tabu_refine, \
             patch("backend_api.optimization_engine.experiment.ConstraintRepair.repair",
                   side_effect=AssertionError("repair invoked by baseline")) as repair:
            ga = self.runner.run_trial(
                ga_experiment, "ga_only", 11, self.faculty, self.sections,
                self.policies, self.config, 12,
                input_provenance="synthetic test fixture",
            )
        tabu_refine.assert_not_called()
        repair.assert_not_called()

        with patch("backend_api.optimization_engine.experiment.GeneticAlgorithm.evolve",
                   side_effect=AssertionError("GA invoked by Tabu-only")) as ga_evolve, \
             patch("backend_api.optimization_engine.experiment.ConstraintRepair.repair",
                   side_effect=AssertionError("repair invoked by baseline")) as repair:
            tabu = self.runner.run_trial(
                tabu_experiment, "tabu_only", 11, self.faculty, self.sections,
                self.policies, self.config, 12,
                input_provenance="synthetic test fixture",
            )
        ga_evolve.assert_not_called()
        repair.assert_not_called()
        self.assertEqual(ga.diagnostics["repair_events"], [])
        self.assertNotEqual(ga.status, "failed")
        self.assertNotEqual(tabu.status, "failed")
        self.assertIn("stopped_by_budget", tabu.diagnostics)

    def test_zero_and_minimal_budgets_are_enforced_and_reported(self):
        for method in ("ga_only", "tabu_only", "hybrid"):
            with self.subTest(method=method):
                zero_experiment = self._manifest(f"zero-{method}", [11], 0)
                minimal_experiment = self._manifest(f"minimal-{method}", [11], 1)
                result = self.runner.run_trial(
                    zero_experiment, method, 11, self.faculty, self.sections,
                    self.policies, self.config, 0,
                    input_provenance="synthetic test fixture",
                )
                self.assertEqual(result.status, "completed_infeasible")
                self.assertEqual(result.objective_evaluations, 0)
                self.assertEqual(result.diagnostics["termination_reason"], "budget_exhausted")
                self.assertTrue(result.diagnostics["budget_exhausted"])

                minimal = self.runner.run_trial(
                    minimal_experiment, method, 11, self.faculty, self.sections,
                    self.policies, self.config, 1,
                    input_provenance="synthetic test fixture",
                )
                self.assertEqual(minimal.objective_evaluations, 1)
                self.assertLessEqual(minimal.objective_evaluations, 1)
                self.assertEqual(
                    minimal.diagnostics["objective_evaluations"],
                    minimal.objective_evaluations,
                )
                self.assertEqual(minimal.status, "budget_exhausted")

    def test_actual_objective_calls_match_reported_count(self):
        original = FitnessEvaluator.evaluate
        for method in ("ga_only", "tabu_only", "hybrid"):
            with self.subTest(method=method):
                experiment_id = self._manifest(f"count-{method}", [11], 7)
                calls = []

                def counted(evaluator, allocations):
                    calls.append(list(allocations))
                    return original(evaluator, allocations)

                with patch.object(FitnessEvaluator, "evaluate", counted):
                    result = self.runner.run_trial(
                        experiment_id, method, 11, self.faculty, self.sections,
                        self.policies, self.config, 7,
                        input_provenance="synthetic test fixture",
                    )

                self.assertEqual(len(calls), result.objective_evaluations)
                self.assertLessEqual(len(calls), 7)

    def test_unexpected_objective_failure_preserves_call_diagnostics(self):
        experiment_id = self._manifest("failure", [11], 5)
        def fail(_evaluator, _allocations):
            raise RuntimeError("simulated objective failure")

        with patch.object(FitnessEvaluator, "evaluate", fail):
            result = self.runner.run_trial(
                experiment_id, "ga_only", 11, self.faculty, self.sections,
                self.policies, self.config, 5,
                input_provenance="synthetic test fixture",
            )

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.objective_evaluations, 1)
        self.assertEqual(result.diagnostics["objective_evaluations"], 1)
        self.assertEqual(result.diagnostics["termination_reason"], "unexpected_failure")
        self.assertEqual(result.diagnostics["failure_message"], "simulated objective failure")
        saved = self.db.query(ExperimentTrial).filter_by(trial_id=result.trial_id).one()
        self.assertEqual(saved.status, "failed")
        self.assertEqual(saved.termination_reason, "unexpected_failure")
        self.assertIn("simulated objective failure", saved.diagnostics_json)
        self.assertEqual(json.loads(saved.input_snapshot_json)["sections_data"],
                         {str(key): value for key, value in self.sections.items()})

    def test_interrupted_trial_remains_visible_as_running(self):
        experiment_id = self._manifest("interrupted", [11], 5)
        with patch.object(ExperimentRunner, "_execute", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.runner.run_trial(
                    experiment_id, "ga_only", 11, self.faculty, self.sections,
                    self.policies, self.config, 5,
                    input_provenance="synthetic test fixture",
                )

        saved = self.db.query(ExperimentTrial).filter_by(
            experiment_id=experiment_id
        ).one()
        self.assertEqual(saved.status, "running")
        self.assertEqual(saved.termination_reason, "in_progress")
        self.assertIsNone(saved.completed_at)
        completeness = experiment_completeness(
            {"planned_trial_count": 2}, [{"status": saved.status}],
        )
        self.assertFalse(completeness["complete"])
        self.assertEqual(completeness["missing_trials"], 1)

    def test_infeasible_completed_trial_is_not_reported_as_success(self):
        faculty = {key: dict(value) for key, value in self.faculty.items()}
        for spec in faculty.values():
            spec["qualifications"] = []
        experiment_id = self._manifest("infeasible", [11], 10, faculty=faculty)

        result = self.runner.run_trial(
            experiment_id, "ga_only", 11, faculty, self.sections,
            self.policies, self.config, 10,
            input_provenance="synthetic test fixture",
        )

        self.assertEqual(result.status, "completed_infeasible")
        self.assertFalse(result.feasible)
        self.assertGreater(result.violation_count, 0)
        self.assertEqual(result.allocations, [])

    def test_trial_input_fingerprint_does_not_change_with_seed(self):
        experiment_id = self._manifest("seeded", [11, 12], 12)
        results = [
            self.runner.run_trial(
                experiment_id, "ga_only", seed, self.faculty, self.sections,
                self.policies, self.config, 12,
                input_provenance="synthetic test fixture",
            )
            for seed in (11, 12)
        ]
        self.assertEqual(results[0].input_fingerprint, results[1].input_fingerprint)
        self.assertEqual([result.seed for result in results], [11, 12])

    def test_persisted_experiment_rejects_mismatched_trial_inputs(self):
        experiment_id = self._manifest("manifest", [11], 20)
        changed_sections = {key: dict(value) for key, value in self.sections.items()}
        changed_sections[1]["enrollment"] = 15

        with self.assertRaisesRegex(ExperimentAuthorizationError, "snapshot"):
            self.runner.run_trial(
                experiment_id, "ga_only", 11, self.faculty, changed_sections,
                self.policies, self.config, 20,
                input_provenance="synthetic test fixture",
            )

        self.assertEqual(self.db.query(ExperimentTrial).count(), 0)

    def test_rejects_unsupported_stopping_conditions(self):
        with self.assertRaisesRegex(ValueError, "Only objective_evaluations"):
            self.runner.create_experiment(
                "unsupported", self.faculty, self.sections, self.policies,
                self.config, [11], 20, stopping_condition="wall_clock",
            )
        with self.assertRaisesRegex(ValueError, "Only objective_evaluations"):
            self.runner.run_trial(
                "invalid", "ga_only", 11, self.faculty, self.sections,
                self.policies, self.config, 20,
                stopping_condition="wall_clock",
            )
        with self.assertRaisesRegex(ValueError, "non-negative integer"):
            self.runner.run_trial(
                "invalid", "ga_only", 11, self.faculty, self.sections,
                self.policies, self.config, -1,
            )

    def test_analysis_reports_descriptive_and_paired_results(self):
        trials = [
            analysis_row("ga_only", 1, 0.4),
            analysis_row("hybrid", 1, 0.6),
        ]
        summary = summarize_trials(trials)
        comparison = paired_method_comparison(trials, "hybrid", "ga_only")
        self.assertEqual(summary["hybrid"]["sample_size"], 1)
        self.assertFalse(summary["hybrid"]["missing_count_known"])
        self.assertFalse(comparison["missing_seed_count_known"])
        self.assertEqual(comparison["sample_size"], 1)
        self.assertAlmostEqual(comparison["mean_difference"], 0.2)

    def test_analysis_excludes_failures_and_infeasible_scores_but_counts_them(self):
        trials = [
            analysis_row("ga_only", 1, 0.5),
            analysis_row("ga_only", 2, 0.0, feasible=False,
                         status="completed_infeasible"),
            analysis_row("ga_only", 3, 0.0, feasible=False, status="failed"),
            analysis_row("hybrid", 1, 0.7, status="budget_exhausted"),
        ]

        summary = summarize_trials(
            trials, planned_counts={"ga_only": 4, "hybrid": 1}
        )
        comparison = paired_method_comparison(trials, "hybrid", "ga_only")

        self.assertEqual(summary["ga_only"]["sample_size"], 3)
        self.assertEqual(summary["ga_only"]["objective_sample_size"], 1)
        self.assertEqual(summary["ga_only"]["failed_trials"], 1)
        self.assertEqual(summary["ga_only"]["completed_infeasible_trials"], 1)
        self.assertEqual(summary["ga_only"]["missing_trials"], 1)
        self.assertAlmostEqual(summary["ga_only"]["feasible_run_rate"], 0.25)
        self.assertAlmostEqual(summary["ga_only"]["objective"]["mean"], 0.5)
        self.assertEqual(comparison["sample_size"], 1)
        self.assertEqual(comparison["left_excluded_trials"], 0)
        self.assertEqual(comparison["right_excluded_trials"], 2)

    def test_documented_cli_writes_only_to_new_isolated_database(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "synthetic-instance.json"
            output = root / "results.sqlite"
            source.write_text(json.dumps({
                "provenance": "Synthetic unit-test fixture; not institutional data",
                "faculty_specs": {str(key): value for key, value in self.faculty.items()},
                "sections_data": {str(key): value for key, value in self.sections.items()},
                "policies": self.policies,
            }), encoding="utf-8")

            provenance = "Synthetic unit-test fixture; not institutional data"
            context = self.authorizer.sign(
                snapshot_path=source,
                result_database=output,
                name="cli smoke test",
                seeds=[11],
                budget=20,
                config=self.config,
                provenance=provenance,
                faculty=self.faculty,
                sections=self.sections,
                policies=self.policies,
            )
            authorization_file = self.authorizer.write(context)
            experiment_id, results = run_comparison(
                source, output, "cli smoke test", [11], 20, self.config,
                authorization_file, CONTROLLED_EXPERIMENT_PURPOSE,
                authorization_service=self.authorizer,
            )

            self.assertTrue(output.exists())
            self.assertEqual(len(results), 3)
            self.assertTrue(all(result.experiment_id == experiment_id for result in results))
            self.assertEqual(self.db.query(Allocation).count(), 0)
            import sqlite3
            connection = sqlite3.connect(output)
            try:
                self.assertEqual(
                    sorted(connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()),
                    [("experiment_runs",), ("experiment_trials",)],
                )
                self.assertEqual(
                    connection.execute("SELECT COUNT(*) FROM experiment_trials").fetchone()[0],
                    3,
                )
            finally:
                connection.close()

    def test_cli_missing_approval_creates_no_output_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "synthetic-instance.json"
            source.write_bytes(synthetic_snapshot_bytes(
                self.faculty, self.sections, self.policies,
                "Synthetic unit-test fixture; not institutional data",
            ))
            output = root / "not-created" / "results.sqlite"
            with patch.dict(os.environ, {
                "OFWAS_EXPERIMENT_TRUSTED_PUBLIC_KEY_FILE": str(self.authorizer.public_key_path),
            }):
                with self.assertRaisesRegex(ExperimentAuthorizationError, "disabled"):
                    run_comparison(
                        source, output, "missing approval", [11], 5, self.config,
                        root / "missing-approval.json", CONTROLLED_EXPERIMENT_PURPOSE,
                    )
            self.assertFalse(output.exists())
            self.assertFalse(output.parent.exists())

    def test_cli_ledger_failure_creates_no_output_path(self):
        class UnavailableLedger:
            def authorize_manifest(self, *args, **kwargs):
                raise ExperimentAuthorizationError("authorization ledger unavailable")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "synthetic-instance.json"
            output = root / "not-created" / "results.sqlite"
            provenance = "Synthetic unit-test fixture; not institutional data"
            source.write_text(json.dumps({
                "provenance": provenance,
                "faculty_specs": {str(key): value for key, value in self.faculty.items()},
                "sections_data": {str(key): value for key, value in self.sections.items()},
                "policies": self.policies,
            }), encoding="utf-8")
            context = self.authorizer.sign(
                snapshot_path=source,
                result_database=output,
                name="ledger failure",
                seeds=[11], budget=5, config=self.config,
                provenance=provenance, faculty=self.faculty,
                sections=self.sections, policies=self.policies,
            )
            authorization_file = self.authorizer.write(context)
            with self.assertRaisesRegex(ExperimentAuthorizationError, "ledger unavailable"):
                run_comparison(
                    source, output, "ledger failure", [11], 5, self.config,
                    authorization_file, CONTROLLED_EXPERIMENT_PURPOSE,
                    authorization_service=UnavailableLedger(),
                )
            self.assertFalse(output.exists())
            self.assertFalse(output.parent.exists())

    def test_post_authorization_database_creation_failure_is_not_denial(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "synthetic-instance.json"
            output = root / "results" / "results.sqlite"
            provenance = "Synthetic unit-test fixture; not institutional data"
            source.write_text(json.dumps({
                "provenance": provenance,
                "faculty_specs": {str(key): value for key, value in self.faculty.items()},
                "sections_data": {str(key): value for key, value in self.sections.items()},
                "policies": self.policies,
            }), encoding="utf-8")
            context = self.authorizer.sign(
                snapshot_path=source,
                result_database=output,
                name="post-authorization-schema-failure",
                seeds=[11], budget=5, config=self.config,
                provenance=provenance, faculty=self.faculty,
                sections=self.sections, policies=self.policies,
            )
            authorization_file = self.authorizer.write(context)

            with patch(
                "backend_api.optimization_engine.experiment_cli.create_engine",
                side_effect=RuntimeError("synthetic database creation failure"),
            ):
                with self.assertRaisesRegex(
                    RuntimeError, "synthetic database creation failure"
                ):
                    run_comparison(
                        source, output, "post-authorization-schema-failure",
                        [11], 5, self.config, authorization_file,
                        CONTROLLED_EXPERIMENT_PURPOSE,
                        authorization_service=self.authorizer,
                    )

            self.assertTrue(output.exists())
            self.assertEqual(output.stat().st_size, 0)

    def test_post_authorization_schema_failure_is_not_denial(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "synthetic-instance.json"
            output = root / "results" / "results.sqlite"
            provenance = "Synthetic unit-test fixture; not institutional data"
            source.write_text(json.dumps({
                "provenance": provenance,
                "faculty_specs": {str(key): value for key, value in self.faculty.items()},
                "sections_data": {str(key): value for key, value in self.sections.items()},
                "policies": self.policies,
            }), encoding="utf-8")
            context = self.authorizer.sign(
                snapshot_path=source, result_database=output,
                name="post-authorization-schema-failure",
                seeds=[11], budget=5, config=self.config,
                provenance=provenance, faculty=self.faculty,
                sections=self.sections, policies=self.policies,
            )
            authorization_file = self.authorizer.write(context)

            with patch.object(
                ExperimentBase.metadata,
                "create_all",
                side_effect=RuntimeError("synthetic schema creation failure"),
            ):
                with self.assertRaisesRegex(
                    RuntimeError, "synthetic schema creation failure"
                ):
                    run_comparison(
                        source, output, "post-authorization-schema-failure",
                        [11], 5, self.config, authorization_file,
                        CONTROLLED_EXPERIMENT_PURPOSE,
                        authorization_service=self.authorizer,
                    )

            self.assertTrue(output.exists())

    def test_post_authorization_manifest_persistence_failure_is_not_denial(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "synthetic-instance.json"
            output = root / "results" / "results.sqlite"
            provenance = "Synthetic unit-test fixture; not institutional data"
            source.write_text(json.dumps({
                "provenance": provenance,
                "faculty_specs": {str(key): value for key, value in self.faculty.items()},
                "sections_data": {str(key): value for key, value in self.sections.items()},
                "policies": self.policies,
            }), encoding="utf-8")
            context = self.authorizer.sign(
                snapshot_path=source, result_database=output,
                name="post-authorization-persistence-failure",
                seeds=[11], budget=5, config=self.config,
                provenance=provenance, faculty=self.faculty,
                sections=self.sections, policies=self.policies,
            )
            authorization_file = self.authorizer.write(context)

            with patch.object(
                Session, "commit",
                side_effect=RuntimeError("synthetic manifest persistence failure"),
            ):
                with self.assertRaisesRegex(
                    RuntimeError, "synthetic manifest persistence failure"
                ):
                    run_comparison(
                        source, output, "post-authorization-persistence-failure",
                        [11], 5, self.config, authorization_file,
                        CONTROLLED_EXPERIMENT_PURPOSE,
                        authorization_service=self.authorizer,
                    )

            self.assertTrue(output.exists())
            import sqlite3
            connection = sqlite3.connect(output)
            try:
                self.assertEqual(
                    connection.execute(
                        "SELECT COUNT(*) FROM experiment_runs"
                    ).fetchone()[0],
                    0,
                )
                self.assertEqual(
                    connection.execute(
                        "SELECT COUNT(*) FROM experiment_trials"
                    ).fetchone()[0],
                    0,
                )
            finally:
                connection.close()

    def test_command_line_entrypoint_is_disabled_without_host_services(self):
        with self.assertRaisesRegex(ExperimentAuthorizationError, "disabled"):
            experiment_cli_main(["--input-json", "must-not-be-read.json"])

    def test_cli_refuses_production_database_path_without_opening_it(self):
        with self.assertRaisesRegex(ValueError, "production workload database"):
            _assert_isolated_new_database(PROJECT_ROOT / "faculty_workload.db")
