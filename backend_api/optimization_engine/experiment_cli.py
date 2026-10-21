"""Run a matched experiment into a new, isolated SQLite results database."""
import json
import os
from pathlib import Path
from urllib.parse import unquote
import uuid
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import URL, make_url
from sqlalchemy.orm import sessionmaker

from backend_api.core.config import settings
from backend_api.optimization_engine.experiment import (
    EXECUTION_DISABLED_MESSAGE,
    ExperimentRunner,
    METHODS,
    _validate_manifest_inputs,
)
from backend_api.optimization_engine.experiment_authorization import (
    ExperimentAuthorizationError,
    ExperimentAuthorizationService,
    load_authorization_context,
    validate_authorization_grant,
)
from backend_api.optimization_engine.experiment_models import ExperimentBase


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_comparison(input_json, output_db, name, seeds, evaluation_budget, config,
                   authorization_file, purpose, *,
                   authorization_service: Optional[ExperimentAuthorizationService] = None):
    """Run only when called by a host with a trusted authorization service.

    The command-line entry point deliberately supplies no service and is
    disabled until a protected institutional trust provider and durable
    approval ledger are deployed.
    """
    if authorization_service is None:
        raise ExperimentAuthorizationError(EXECUTION_DISABLED_MESSAGE)

    snapshot_path = Path(input_json).resolve(strict=True)
    database_path = Path(output_db).resolve()
    _assert_isolated_new_database(database_path)

    snapshot_bytes = snapshot_path.read_bytes()
    try:
        source = json.loads(snapshot_bytes.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Input JSON must be valid UTF-8") from exc
    provenance = source.get("provenance")
    if not isinstance(provenance, str) or not provenance.strip():
        raise ValueError("Input JSON must include non-empty provenance")
    faculty_specs = _integer_keyed(source.get("faculty_specs"), "faculty_specs")
    sections_data = _integer_keyed(source.get("sections_data"), "sections_data")
    policies = source.get("policies")
    if not isinstance(policies, dict):
        raise ValueError("Input JSON policies must be an object")
    seeds = _validate_manifest_inputs(
        seeds, evaluation_budget, "objective_evaluations", provenance
    )

    authorization = load_authorization_context(
        authorization_file,
        snapshot_bytes,
        snapshot_path,
        database_path,
        purpose,
    )
    experiment_id = str(uuid.uuid4())
    scope = {
        "experiment_name": name,
        "methods": list(METHODS),
        "seeds": list(seeds),
        "evaluation_budget": evaluation_budget,
        "configuration": config.as_dict(),
        "stopping_condition": "objective_evaluations",
        "input_provenance": provenance,
        "faculty_specs": faculty_specs,
        "sections_data": sections_data,
        "policies": policies,
    }
    grant = authorization_service.authorize_manifest(
        authorization, experiment_id=experiment_id, **scope
    )
    validate_authorization_grant(grant, authorization, experiment_id, scope)

    database_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        output_fd = os.open(
            str(database_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600
        )
    except FileExistsError as exc:
        raise FileExistsError(
            "Output database already exists; choose a new isolated results path"
        ) from exc
    os.close(output_fd)
    url = URL.create("sqlite", database=str(database_path))
    engine = create_engine(url)
    try:
        ExperimentBase.metadata.create_all(engine)
        session = sessionmaker(bind=engine)()
        try:
            runner = ExperimentRunner(
                session,
                authorization_context=authorization,
                authorization_service=authorization_service,
            )
            experiment_id = runner._persist_authorized_manifest(
                grant,
                experiment_id,
                scope,
                name,
                config,
                list(seeds),
                evaluation_budget,
                "objective_evaluations",
            )
            results = []
            for seed in seeds:
                for method in METHODS:
                    results.append(
                        runner.run_trial(
                            experiment_id,
                            method,
                            seed,
                            faculty_specs,
                            sections_data,
                            policies,
                            config,
                            evaluation_budget,
                            input_provenance=provenance,
                        )
                    )
            return experiment_id, results
        finally:
            session.close()
    finally:
        engine.dispose()


def _assert_isolated_new_database(database_path):
    production_path = (PROJECT_ROOT / "faculty_workload.db").resolve()
    if database_path == production_path:
        raise ValueError("Refusing to use the production workload database")

    configured_url = make_url(settings.DATABASE_URL)
    if configured_url.get_backend_name() == "sqlite":
        if _uses_unsupported_sqlite_uri(configured_url):
            raise ValueError(
                "SQLite URI database URLs are not supported by the experiment CLI; "
                "use a filesystem path or :memory:"
            )
        configured_database = configured_url.database
        if configured_database not in (None, ":memory:"):
            if _configured_sqlite_file_path(configured_url) == database_path:
                raise ValueError("Refusing to use the configured application database")

    if database_path.exists():
        raise FileExistsError(
            "Output database already exists; choose a new isolated results path"
        )


def _configured_sqlite_file_path(configured_url):
    """Resolve an ordinary configured SQLite file from this process's CWD."""
    database = configured_url.database
    if database in (None, "", ":memory:"):
        return None

    configured_path = Path(database)
    if not configured_path.is_absolute():
        configured_path = Path.cwd() / configured_path
    return configured_path.resolve()


def _uses_unsupported_sqlite_uri(configured_url):
    """Reject SQLite URI filenames and URI-specific parameters conservatively."""
    database = configured_url.database or ""
    if unquote(database).lower().startswith("file:"):
        return True

    query = {key.lower(): value for key, value in configured_url.query.items()}
    uri_parameters = {
        "mode", "cache", "immutable", "nolock", "psow", "vfs", "mutex",
    }
    return "uri" in query or bool(uri_parameters.intersection(query))


def _integer_keyed(value, label):
    if not isinstance(value, dict) or not value:
        raise ValueError(f"Input JSON {label} must be a non-empty object")
    try:
        return {int(key): item for key, item in value.items()}
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Input JSON {label} keys must be integer IDs") from exc


def main(argv=None):
    """Deny CLI execution until a protected authorization host is deployed."""
    raise ExperimentAuthorizationError(EXECUTION_DISABLED_MESSAGE)


if __name__ == "__main__":
    main()
