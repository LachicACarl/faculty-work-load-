"""Isolated, reproducible execution for algorithm-comparison experiments."""
from dataclasses import dataclass
from dataclasses import replace
from datetime import datetime
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from sqlalchemy.engine import make_url

from backend_api.core.config import settings
from backend_api.optimization_engine.experiment_authorization import (
    ExperimentAuthorizationContext,
    ExperimentAuthorizationError,
    ExperimentAuthorizationGrant,
    ExperimentAuthorizationService,
    validate_authorization_grant,
)
from backend_api.optimization_engine.experiment_models import ExperimentRun, ExperimentTrial
from backend_api.optimization_engine.constraint_repair import (
    ConstraintRepair,
    FeasibilityCheck,
)
from backend_api.optimization_engine.fingerprint import (
    optimization_input_fingerprint,
)
from backend_api.optimization_engine.fitness import FitnessEvaluator
from backend_api.optimization_engine.genetic_algorithm import GeneticAlgorithm
from backend_api.optimization_engine.run_config import OptimizationConfig
from backend_api.optimization_engine.tabu_search import TabuSearch


METHODS = ("ga_only", "tabu_only", "hybrid")
IMPLEMENTATION_VERSION = "stage-5.4.2-v1"
EXECUTION_DISABLED_MESSAGE = (
    "Controlled experiment execution is disabled: this deployment has no "
    "protected institutional trust provider or durable approval ledger"
)


@dataclass
class ExperimentResult:
    """Non-persistent result returned by one isolated experiment trial."""

    trial_id: str
    experiment_id: str
    method: str
    seed: Optional[int]
    input_fingerprint: str
    objective_score: float
    objective_evaluations: int
    runtime_seconds: float
    feasible: bool
    violation_count: int
    assigned_sections: int
    unassigned_sections: int
    allocations: List[Tuple[int, int]]
    diagnostics: Dict
    status: str


class ExperimentRunner:
    """Run comparison methods without writing live allocation rows."""

    def __init__(
        self,
        db=None,
        authorization_context: Optional[ExperimentAuthorizationContext] = None,
        authorization_service: Optional[ExperimentAuthorizationService] = None,
    ):
        self.db = db
        self.authorization_context = authorization_context
        self.authorization_service = authorization_service

    def create_experiment(
        self,
        name: str,
        faculty_specs: dict,
        sections_data: dict,
        policies: dict,
        config: OptimizationConfig,
        seeds: List[int],
        evaluation_budget: int,
        stopping_condition: str = "objective_evaluations",
        input_provenance: str = "unspecified",
    ) -> str:
        self._require_authorization_service()
        if self.db is None:
            raise ExperimentAuthorizationError(
                "Controlled experiments require a persistent isolated results database"
            )
        seeds = _validate_manifest_inputs(
            seeds, evaluation_budget, stopping_condition, input_provenance
        )
        context = self.authorization_context
        if context is None:
            raise ExperimentAuthorizationError("Signed authorization evidence is required")
        result_database = _experiment_database_identity(self.db)
        if context.result_database != result_database:
            raise ExperimentAuthorizationError(
                "Authorization results database does not match the active database"
            )
        scope = dict(
            experiment_name=name,
            methods=list(METHODS),
            seeds=list(seeds),
            evaluation_budget=evaluation_budget,
            configuration=config.as_dict(),
            stopping_condition=stopping_condition,
            input_provenance=input_provenance,
            faculty_specs=faculty_specs,
            sections_data=sections_data,
            policies=policies,
        )
        experiment_id = str(uuid.uuid4())
        grant = self.authorization_service.authorize_manifest(
            context, experiment_id=experiment_id, **scope
        )
        if not isinstance(grant, ExperimentAuthorizationGrant):
            raise ExperimentAuthorizationError(
                "Trusted authorization service returned an invalid manifest grant"
            )
        return self._persist_authorized_manifest(
            grant, experiment_id, scope, name, config, seeds,
            evaluation_budget, stopping_condition,
        )

    def _persist_authorized_manifest(
        self, grant, experiment_id, scope, name, config, seeds,
        evaluation_budget, stopping_condition,
    ) -> str:
        """Persist a grant already issued by the trusted host in this call flow.

        This private handoff is used by the CLI after it has obtained and
        validated a grant before creating the output database. It is not a
        security boundary against arbitrary code in this trusted process.
        """
        self._require_authorization_service()
        if self.db is None:
            raise ExperimentAuthorizationError(
                "Controlled experiments require a persistent isolated results database"
            )
        context = self.authorization_context
        if context is None:
            raise ExperimentAuthorizationError("Signed authorization evidence is required")
        if context.result_database != _experiment_database_identity(self.db):
            raise ExperimentAuthorizationError(
                "Authorization results database does not match the active database"
            )
        payload = validate_authorization_grant(grant, context, experiment_id, scope)
        input_provenance, faculty_specs, sections_data, policies = (
            _decode_authorized_snapshot(context.snapshot_bytes)
        )
        if self.db.query(ExperimentRun).filter_by(
            authorization_id=payload["approval_id"]
        ).first() is not None:
            raise ExperimentAuthorizationError(
                "This approval has already been used for an experiment manifest"
            )
        self.db.add(
            ExperimentRun(
                experiment_id=experiment_id,
                name=name,
                input_provenance=input_provenance,
                input_fingerprint=self._fingerprint(
                    faculty_specs, sections_data, policies
                ),
                # Keep the exact signed bytes: trials consume this immutable
                # snapshot from the manifest instead of reopening its source.
                input_snapshot_json=context.snapshot_bytes.decode("utf-8"),
                authorization_id=payload["approval_id"],
                authorization_json=_json(context.envelope),
                configuration_json=_json(config.as_dict()),
                seed_list_json=_json(seeds),
                methods_json=_json(METHODS),
                planned_trial_count=len(seeds) * len(METHODS),
                evaluation_budget=evaluation_budget,
                stopping_condition=stopping_condition,
            )
        )
        self.db.commit()
        return experiment_id

    def run_trial(
        self,
        experiment_id: str,
        method: str,
        seed: Optional[int],
        faculty_specs: dict,
        sections_data: dict,
        policies: dict,
        config: OptimizationConfig,
        evaluation_budget: int,
        stopping_condition: str = "objective_evaluations",
        input_provenance: str = "unspecified",
    ) -> ExperimentResult:
        self._require_authorization_service()
        if self.db is None:
            raise ExperimentAuthorizationError(
                "Controlled trials require a persistent isolated results database"
            )
        if method not in METHODS:
            raise ValueError(f"Unsupported experiment method: {method}")
        if seed is not None and (
            isinstance(seed, bool) or not isinstance(seed, int) or seed < 0
        ):
            raise ValueError("seed must be a non-negative integer")
        _validate_budget(evaluation_budget)
        _validate_stopping_condition(stopping_condition)
        if not input_provenance.strip():
            raise ValueError("input_provenance must be a non-empty description")

        effective_config = replace(config, seed=seed)

        experiment = self.db.get(ExperimentRun, experiment_id)
        if experiment is None:
            raise ExperimentAuthorizationError(
                "A persisted, authorized experiment manifest is required"
            )
        try:
            envelope = json.loads(experiment.authorization_json)
            payload = envelope["payload"]
            snapshot_bytes = experiment.input_snapshot_json.encode("utf-8")
        except (AttributeError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ExperimentAuthorizationError(
                "Persisted experiment authorization evidence is malformed"
            ) from exc
        if experiment.authorization_id != payload.get("approval_id"):
            raise ExperimentAuthorizationError(
                "Persisted authorization ID does not match its signed evidence"
            )
        context = ExperimentAuthorizationContext(
            envelope=envelope,
            snapshot_bytes=snapshot_bytes,
            snapshot_path=payload.get("snapshot_path", ""),
            result_database=_experiment_database_identity(self.db),
            purpose=payload.get("purpose", ""),
        )
        planned_methods = json.loads(experiment.methods_json)
        planned_seeds = json.loads(experiment.seed_list_json)
        self.authorization_service.authorize_trial(
            context,
            experiment_id=experiment_id,
            experiment_name=experiment.name,
            methods=planned_methods,
            seeds=planned_seeds,
            evaluation_budget=experiment.evaluation_budget,
            configuration=json.loads(experiment.configuration_json),
            stopping_condition=experiment.stopping_condition,
            input_provenance=experiment.input_provenance,
            faculty_specs=faculty_specs,
            sections_data=sections_data,
            policies=policies,
            required_method=method,
            required_seed=seed,
        )
        input_provenance, faculty_specs, sections_data, policies = (
            _decode_authorized_snapshot(context.snapshot_bytes)
        )
        self._validate_experiment_manifest(
            experiment_id, method, seed, self._fingerprint(
                faculty_specs, sections_data, policies
            ), effective_config, evaluation_budget, stopping_condition,
            input_provenance,
        )
        if method not in planned_methods or seed not in planned_seeds:
            raise ExperimentAuthorizationError(
                "Requested method or seed is outside the authorized plan"
            )
        if self.db.query(ExperimentTrial).filter_by(
            experiment_id=experiment_id, method=method, seed=seed
        ).first() is not None:
            raise ExperimentAuthorizationError(
                "This approved method/seed trial has already been recorded"
            )

        trial_id = str(uuid.uuid4())
        started_at = datetime.utcnow()
        fingerprint = self._fingerprint(
            faculty_specs, sections_data, policies
        )
        environment = _runtime_environment()
        objective_counter = {"count": 0}
        self._create_pending_trial(
            trial_id, experiment_id, method, seed, fingerprint, effective_config,
            evaluation_budget, stopping_condition, started_at, input_provenance,
            context.snapshot_bytes.decode("utf-8"), environment,
        )
        started_clock = time.perf_counter()
        try:
            result = self._execute(
                trial_id,
                experiment_id,
                method,
                seed,
                faculty_specs,
                sections_data,
                policies,
                effective_config,
                evaluation_budget,
                stopping_condition,
                fingerprint,
                started_clock,
                objective_counter,
            )
        except Exception as exc:
            result = ExperimentResult(
                trial_id=trial_id,
                experiment_id=experiment_id,
                method=method,
                seed=seed,
                input_fingerprint=fingerprint,
                objective_score=0.0,
                objective_evaluations=objective_counter["count"],
                runtime_seconds=time.perf_counter() - started_clock,
                feasible=False,
                violation_count=1,
                assigned_sections=0,
                unassigned_sections=len(sections_data),
                allocations=[],
                diagnostics={
                    "failure_code": type(exc).__name__,
                    "failure_message": str(exc),
                    "objective_evaluations": objective_counter["count"],
                    "stopping_condition": stopping_condition,
                    "termination_reason": "unexpected_failure",
                },
                status="failed",
            )
        self._persist_trial(result)
        return result

    def _execute(
        self,
        trial_id,
        experiment_id,
        method,
        seed,
        faculty_specs,
        sections_data,
        policies,
        config,
        evaluation_budget,
        stopping_condition,
        fingerprint,
        started_clock,
        objective_counter,
    ):
        eligible_pairs = sorted(
            ConstraintRepair(faculty_specs, sections_data, policies)
            ._eligible_pairs()
        )
        required_ids = set(sections_data)
        feasibility = FeasibilityCheck(
            faculty_specs, sections_data, policies, required_ids
        )
        repair_engine = ConstraintRepair(faculty_specs, sections_data, policies)
        fitness = FitnessEvaluator(faculty_specs, sections_data, policies)

        def objective(allocations):
            if objective_counter["count"] >= evaluation_budget:
                raise RuntimeError("Objective evaluation budget exceeded")
            objective_counter["count"] += 1
            return fitness.evaluate(allocations)

        repair_events = []

        def repair_candidate(candidate):
            repaired = repair_engine.repair(
                candidate, eligible_pairs, feasibility.is_feasible
            )
            repair_events.append({
                "attempts": repaired.attempts,
                "completed": repaired.completed,
                "feasible": repaired.feasible,
                "termination_reason": repaired.termination_reason,
                "unresolved_violations": repaired.unresolved_violations,
            })
            return repaired

        if method == "tabu_only":
            current = []
            for section_id in sorted(sections_data):
                pair = next(
                    (pair for pair in eligible_pairs if pair[1] == section_id),
                    None,
                )
                if pair is not None:
                    current.append(pair)
            search = TabuSearch(
                tabu_tenure=config.tabu_tenure,
                max_iterations=config.tabu_max_iterations,
                max_evaluations=evaluation_budget,
            )
            allocations = search.refine(
                current,
                objective,
                eligible_pairs,
                feasibility_func=feasibility.is_feasible,
            )
            evaluations = search.evaluation_count
            final_objective = search.best_fitness if search.best_solution is not None else 0.0
            diagnostics = {
                "stopping_condition": stopping_condition,
                "stopped_by_budget": search.stopped_by_budget,
                "termination_reason": search.termination_reason,
            }
        else:
            ga_budget = evaluation_budget if method == "ga_only" else min(
                evaluation_budget, max(1, evaluation_budget // 2)
            )
            ga = GeneticAlgorithm(
                population_size=config.ga_population_size,
                generations=config.ga_generations,
                mutation_rate=config.ga_mutation_rate,
                crossover_rate=config.ga_crossover_rate,
                rng=__import__("random").Random(seed),
                max_evaluations=ga_budget,
            )
            best = ga.evolve(
                fitness_func=lambda candidate: objective(
                    candidate.allocations
                ),
                eligible_pairs=eligible_pairs,
                repair_func=repair_candidate if method == "hybrid" else None,
                feasibility_func=feasibility.is_feasible,
            )
            allocations = best.allocations if best.fitness != float("-inf") else []
            evaluations = ga.evaluation_count
            final_objective = best.fitness if best.fitness != float("-inf") else 0.0
            diagnostics = {
                "stopping_condition": stopping_condition,
                "stopped_by_budget": ga.stopped_by_budget,
                "termination_reason": ga.termination_reason,
            }
            if method == "hybrid" and evaluation_budget > evaluations:
                remaining = max(0, evaluation_budget - evaluations)
                search = TabuSearch(
                    tabu_tenure=config.tabu_tenure,
                    max_iterations=config.tabu_max_iterations,
                    max_evaluations=remaining,
                )
                allocations = search.refine(
                    allocations,
                    objective,
                    eligible_pairs,
                    feasibility_func=feasibility.is_feasible,
                    repair_func=repair_candidate,
                )
                evaluations += search.evaluation_count
                if search.best_solution is not None:
                    final_objective = search.best_fitness
                diagnostics["stopped_by_budget"] = (
                    ga.stopped_by_budget or search.stopped_by_budget
                )
                diagnostics["ga_termination_reason"] = ga.termination_reason
                diagnostics["tabu_termination_reason"] = search.termination_reason
                diagnostics["termination_reason"] = (
                    "budget_exhausted" if search.stopped_by_budget
                    else f"tabu_{search.termination_reason}"
                )

        feasible = feasibility.is_feasible(allocations)
        violations = repair_engine._diagnose(allocations)[0]
        # Reuse the search's measured score. An extra fitness call here would
        # exceed the declared objective-evaluation budget without being counted.
        objective = final_objective if allocations else 0.0
        if objective_counter["count"] != evaluations:
            raise RuntimeError(
                "Reported evaluation count does not match objective calls "
                f"({evaluations} reported, {objective_counter['count']} observed)"
            )
        if evaluations > evaluation_budget:
            raise RuntimeError("Objective evaluation budget exceeded")
        budget_exhausted = diagnostics["stopped_by_budget"]
        diagnostics["objective_evaluations"] = objective_counter["count"]
        diagnostics["evaluation_budget"] = evaluation_budget
        diagnostics["budget_exhausted"] = budget_exhausted
        diagnostics["repair_attempts"] = sum(
            event["attempts"] for event in repair_events
        )
        diagnostics["repair_events"] = repair_events
        diagnostics["violation_codes"] = violations
        diagnostics["objective_direction"] = "maximize"
        return ExperimentResult(
            trial_id=trial_id,
            experiment_id=experiment_id,
            method=method,
            seed=seed,
            input_fingerprint=fingerprint,
            objective_score=objective,
            objective_evaluations=evaluations,
            runtime_seconds=time.perf_counter() - started_clock,
            feasible=feasible,
            violation_count=len(violations),
            assigned_sections=len(allocations),
            unassigned_sections=max(0, len(sections_data) - len(allocations)),
            allocations=list(allocations),
            diagnostics=diagnostics,
            status=(
                "completed_infeasible" if not feasible
                else "budget_exhausted" if budget_exhausted
                else "succeeded"
            ),
        )

    def _require_authorization_service(self):
        if self.authorization_service is None:
            raise ExperimentAuthorizationError(EXECUTION_DISABLED_MESSAGE)

    def _persist_trial(self, result):
        if self.db is None:
            return
        completed_at = datetime.utcnow()
        trial = self.db.get(ExperimentTrial, result.trial_id)
        if trial is None:
            raise RuntimeError("Pending experiment trial record is missing")
        trial.completed_at = completed_at
        trial.runtime_seconds = result.runtime_seconds
        trial.objective_score = result.objective_score
        trial.objective_evaluations = result.objective_evaluations
        trial.feasible = result.feasible
        trial.violation_count = result.violation_count
        trial.assigned_sections = result.assigned_sections
        trial.unassigned_sections = result.unassigned_sections
        trial.diagnostics_json = _json(result.diagnostics)
        trial.allocations_json = _json(result.allocations)
        trial.termination_reason = result.diagnostics.get(
            "termination_reason", "unknown"
        )
        trial.status = result.status
        trial.failure_code = result.diagnostics.get("failure_code")
        self.db.commit()

    def _create_pending_trial(
        self, trial_id, experiment_id, method, seed, fingerprint, config,
        evaluation_budget, stopping_condition, started_at, input_provenance,
        input_snapshot_json, environment,
    ):
        if self.db is None:
            return
        self.db.add(
            ExperimentTrial(
                trial_id=trial_id,
                experiment_id=experiment_id,
                method=method,
                implementation_version=IMPLEMENTATION_VERSION,
                input_fingerprint=fingerprint,
                input_provenance=input_provenance,
                input_snapshot_json=input_snapshot_json,
                seed=seed,
                configuration_json=_json(config.as_dict()),
                evaluation_budget=evaluation_budget,
                stopping_condition=stopping_condition,
                termination_reason="in_progress",
                started_at=started_at,
                objective_evaluations=0,
                violation_count=0,
                assigned_sections=0,
                unassigned_sections=0,
                diagnostics_json=_json({"termination_reason": "in_progress"}),
                allocations_json="[]",
                environment_json=_json(environment),
                status="running",
            )
        )
        self.db.commit()

    def _validate_experiment_manifest(
        self, experiment_id, method, seed, fingerprint, config,
        evaluation_budget, stopping_condition, input_provenance,
    ):
        if self.db is None:
            return
        experiment = self.db.get(ExperimentRun, experiment_id)
        if experiment is None:
            raise ValueError("Persisted trial requires an existing experiment manifest")
        if fingerprint != experiment.input_fingerprint:
            raise ValueError("Trial inputs do not match the experiment fingerprint")
        if method not in json.loads(experiment.methods_json):
            raise ValueError("Trial method is not included in the experiment plan")
        if seed not in json.loads(experiment.seed_list_json):
            raise ValueError("Trial seed is not included in the experiment plan")
        if evaluation_budget != experiment.evaluation_budget:
            raise ValueError("Trial budget does not match the experiment plan")
        if stopping_condition != experiment.stopping_condition:
            raise ValueError("Trial stopping condition does not match the plan")
        if input_provenance != experiment.input_provenance:
            raise ValueError("Trial provenance does not match the experiment plan")
        planned_config = json.loads(experiment.configuration_json)
        effective_config = config.as_dict()
        planned_config.pop("seed", None)
        effective_config.pop("seed", None)
        if effective_config != planned_config:
            raise ValueError("Trial configuration does not match the experiment plan")

    @staticmethod
    def _fingerprint(faculty_specs, sections_data, policies):
        return optimization_input_fingerprint(
            faculty_specs, sections_data, policies
        )


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _decode_authorized_snapshot(snapshot_bytes):
    """Return fresh execution inputs parsed from the signed bytes."""
    try:
        snapshot = json.loads(snapshot_bytes.decode("utf-8"))
        provenance = snapshot["provenance"]
        faculty_specs = {
            int(key): value for key, value in snapshot["faculty_specs"].items()
        }
        sections_data = {
            int(key): value for key, value in snapshot["sections_data"].items()
        }
        policies = snapshot["policies"]
    except (UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise ExperimentAuthorizationError(
            "Authorized snapshot cannot be consumed by the experiment runner"
        ) from exc
    return provenance, faculty_specs, sections_data, policies


def _validate_stopping_condition(value):
    if value != "objective_evaluations":
        raise ValueError("Only objective_evaluations stopping is currently supported")


def _validate_budget(value):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("evaluation_budget must be a non-negative integer")


def _validate_manifest_inputs(seeds, evaluation_budget, stopping_condition,
                              input_provenance):
    seeds = list(seeds)
    if not seeds:
        raise ValueError("At least one experiment seed is required")
    if any(
        isinstance(seed, bool) or not isinstance(seed, int) or seed < 0
        for seed in seeds
    ):
        raise ValueError("Experiment seeds must be non-negative integers")
    if len(set(seeds)) != len(seeds):
        raise ValueError("Experiment seeds must be unique")
    _validate_budget(evaluation_budget)
    _validate_stopping_condition(stopping_condition)
    if not input_provenance.strip():
        raise ValueError("input_provenance must be a non-empty description")
    return seeds


def _experiment_database_identity(db):
    """Return a safe SQLite result target and reject application databases."""
    try:
        database_url = make_url(str(db.get_bind().url))
    except Exception as exc:
        raise ExperimentAuthorizationError(
            "Cannot identify the experiment results database"
        ) from exc
    if database_url.get_backend_name() != "sqlite":
        raise ExperimentAuthorizationError(
            "Experiment results must use an isolated SQLite database"
        )
    database = database_url.database
    if database in (None, "", ":memory:"):
        return "sqlite::memory:"
    if (database_url.query and "uri" in database_url.query) or database.lower().startswith("file:"):
        raise ExperimentAuthorizationError(
            "SQLite URI result databases are not supported"
        )
    path = Path(database)
    if not path.is_absolute():
        path = Path.cwd() / path
    resolved_path = path.resolve()
    repository_database = (Path(__file__).resolve().parents[2] / "faculty_workload.db").resolve()
    if resolved_path == repository_database:
        raise ExperimentAuthorizationError(
            "Experiment results cannot use the application database"
        )
    try:
        configured_url = make_url(settings.DATABASE_URL)
        configured_database = configured_url.database
        if configured_url.get_backend_name() == "sqlite" and configured_database not in (
            None, "", ":memory:"
        ):
            configured_path = Path(configured_database)
            if not configured_path.is_absolute():
                configured_path = Path.cwd() / configured_path
            if configured_path.resolve() == resolved_path:
                raise ExperimentAuthorizationError(
                    "Experiment results cannot use the configured application database"
                )
    except ExperimentAuthorizationError:
        raise
    except Exception as exc:
        raise ExperimentAuthorizationError(
            "Cannot verify separation from the application database"
        ) from exc
    return str(resolved_path)


def _runtime_environment():
    packages = {}
    for distribution in ("fastapi", "pydantic", "sqlalchemy"):
        try:
            packages[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            packages[distribution] = None
    repository = Path(__file__).resolve().parents[2]
    try:
        revision = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repository,
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain"], cwd=repository,
            check=True, capture_output=True, text=True,
        ).stdout
        source_control = {
            "revision": revision,
            "working_tree_dirty": bool(status.strip()),
            "status_sha256": hashlib.sha256(status.encode("utf-8")).hexdigest(),
        }
    except (OSError, subprocess.CalledProcessError):
        source_control = {"revision": None, "working_tree_dirty": None}
    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "packages": packages,
        "source_control": source_control,
    }
