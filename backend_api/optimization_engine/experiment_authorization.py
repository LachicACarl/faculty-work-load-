"""Verify signed experiment evidence using a trust anchor supplied by a host.

This module does not provision a trust anchor or implement a durable ledger.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import base64
import hashlib
import json
from pathlib import Path
from typing import Protocol

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


CONTROLLED_EXPERIMENT_PURPOSE = "controlled_optimization_benchmark"


class ExperimentAuthorizationError(ValueError):
    """Raised when a signed authorization is missing or does not match a run."""


@dataclass(frozen=True)
class ExperimentAuthorizationGrant:
    """Single manifest grant issued by a trusted host after ledger consumption."""

    experiment_id: str
    approval_id: str
    scope_sha256: str
    payload: dict


class ExperimentAuthorizationService(Protocol):
    """Trusted host interface for verification and durable approval consumption.

    Production implementations must obtain their key from an independently
    provisioned trust anchor and atomically consume approval IDs in a durable,
    institution-controlled ledger. No such production implementation ships in
    this repository.
    """

    def authorize_manifest(
        self, context, *, experiment_id, **scope
    ) -> ExperimentAuthorizationGrant: ...

    def authorize_trial(self, context, *, experiment_id, **scope): ...


@dataclass(frozen=True)
class ExperimentAuthorizationContext:
    """Signed approval plus the exact input bytes and paths to be consumed."""

    envelope: dict
    snapshot_bytes: bytes
    snapshot_path: str
    result_database: str
    purpose: str


def canonical_json_bytes(value):
    """Serialize JSON deterministically for signatures and snapshot checks."""
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ExperimentAuthorizationError("Authorization data is not valid JSON") from exc


def authorization_scope_sha256(scope):
    """Bind a host-issued grant to the exact manifest arguments."""
    return hashlib.sha256(canonical_json_bytes(scope)).hexdigest()


def validate_authorization_grant(grant, context, experiment_id, scope):
    """Reject a host grant that does not match this exact signed run request."""
    signed_payload = context.envelope.get("payload", {})
    if (
        not isinstance(grant, ExperimentAuthorizationGrant)
        or grant.experiment_id != experiment_id
        or grant.approval_id != signed_payload.get("approval_id")
        or grant.payload != signed_payload
        or grant.scope_sha256 != authorization_scope_sha256(scope)
    ):
        raise ExperimentAuthorizationError(
            "Host authorization grant does not match this manifest"
        )
    return grant.payload


def load_authorization_context(authorization_file, snapshot_bytes, snapshot_path,
                              result_database, purpose):
    """Load evidence without granting it; callers must still verify its scope."""
    try:
        envelope = json.loads(Path(authorization_file).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ExperimentAuthorizationError(
            "Authorization evidence is missing or unreadable"
        ) from exc
    if not isinstance(envelope, dict):
        raise ExperimentAuthorizationError("Authorization evidence must be a JSON object")
    return ExperimentAuthorizationContext(
        envelope=envelope,
        snapshot_bytes=snapshot_bytes,
        snapshot_path=str(Path(snapshot_path).resolve()),
        result_database=normalize_result_database(result_database),
        purpose=purpose,
    )


def normalize_result_database(value):
    if value == "sqlite::memory:":
        return value
    return str(Path(value).resolve())


def verify_experiment_authorization(
    context,
    *,
    trusted_public_key,
    experiment_name,
    methods,
    seeds,
    evaluation_budget,
    configuration,
    stopping_condition,
    input_provenance,
    faculty_specs,
    sections_data,
    policies,
    required_method=None,
    required_seed=None,
):
    """Verify signature and exact scope using an explicitly supplied trust key.

    This verifies cryptographic evidence; it does not establish how the caller
    obtained the key or whether the key belongs to an institution.
    """
    if not isinstance(context, ExperimentAuthorizationContext):
        raise ExperimentAuthorizationError("Signed authorization evidence is required")

    envelope = context.envelope
    payload = envelope.get("payload") if isinstance(envelope, dict) else None
    signature_text = envelope.get("signature_ed25519") if isinstance(envelope, dict) else None
    if not isinstance(payload, dict) or not isinstance(signature_text, str):
        raise ExperimentAuthorizationError("Signed authorization evidence is malformed")

    if not isinstance(trusted_public_key, Ed25519PublicKey):
        raise ExperimentAuthorizationError("Trusted approval key must be Ed25519")

    try:
        signature = base64.b64decode(signature_text, validate=True)
        trusted_public_key.verify(signature, canonical_json_bytes(payload))
    except (ValueError, InvalidSignature, ExperimentAuthorizationError) as exc:
        raise ExperimentAuthorizationError("Authorization signature is invalid") from exc

    _validate_payload(payload)
    now = datetime.now(timezone.utc)
    approved_at = _parse_timestamp(payload["approved_at"], "approved_at")
    expires_at = _parse_timestamp(payload["expires_at"], "expires_at")
    if approved_at > now or expires_at <= now or expires_at <= approved_at:
        raise ExperimentAuthorizationError("Authorization is stale or not yet valid")

    review = payload["human_review"]
    reviewed_at = _parse_timestamp(review["reviewed_at"], "human_review.reviewed_at")
    if reviewed_at > now or reviewed_at < approved_at:
        raise ExperimentAuthorizationError("Human review timestamp is invalid")

    if context.purpose != CONTROLLED_EXPERIMENT_PURPOSE:
        raise ExperimentAuthorizationError("Requested experiment purpose is not permitted")
    if payload["purpose"] != context.purpose:
        raise ExperimentAuthorizationError("Authorization purpose does not match the request")

    snapshot_path = str(Path(context.snapshot_path).resolve())
    result_database = normalize_result_database(context.result_database)
    if payload["snapshot_path"] != snapshot_path:
        raise ExperimentAuthorizationError("Snapshot path does not match the approval")
    if payload["result_database"] != result_database:
        raise ExperimentAuthorizationError("Results database does not match the approval")

    if not isinstance(context.snapshot_bytes, bytes):
        raise ExperimentAuthorizationError("Exact snapshot bytes are required")
    try:
        decoded_snapshot = json.loads(context.snapshot_bytes.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ExperimentAuthorizationError("Snapshot bytes are not valid UTF-8 JSON") from exc
    expected_snapshot = {
        "provenance": input_provenance,
        "faculty_specs": faculty_specs,
        "sections_data": sections_data,
        "policies": policies,
    }
    if decoded_snapshot != json.loads(canonical_json_bytes(expected_snapshot)):
        raise ExperimentAuthorizationError(
            "Runner inputs do not match the exact approved snapshot bytes"
        )
    snapshot_hash = hashlib.sha256(context.snapshot_bytes).hexdigest()
    if payload["snapshot_sha256"] != snapshot_hash:
        raise ExperimentAuthorizationError("Snapshot hash does not match the approval")

    requested_methods = list(methods)
    requested_seeds = list(seeds)
    if payload["experiment_name"] != experiment_name:
        raise ExperimentAuthorizationError("Experiment name does not match the approval")
    if payload["methods"] != requested_methods:
        raise ExperimentAuthorizationError("Experiment methods do not match the approval")
    if payload["seeds"] != requested_seeds:
        raise ExperimentAuthorizationError("Experiment seeds do not match the approval")
    if payload["evaluation_budget"] != evaluation_budget:
        raise ExperimentAuthorizationError("Evaluation budget does not match the approval")
    if payload["configuration"] != configuration:
        raise ExperimentAuthorizationError("Optimizer configuration does not match the approval")
    if payload["stopping_condition"] != stopping_condition:
        raise ExperimentAuthorizationError("Stopping condition does not match the approval")
    if payload["input_provenance"] != input_provenance:
        raise ExperimentAuthorizationError("Input provenance does not match the approval")
    if required_method is not None and required_method not in payload["methods"]:
        raise ExperimentAuthorizationError("Trial method is outside the approved plan")
    if required_seed is not None and required_seed not in payload["seeds"]:
        raise ExperimentAuthorizationError("Trial seed is outside the approved plan")

    return payload


def _validate_payload(payload):
    required = {
        "schema_version", "approval_id", "decision", "approved_by",
        "approval_reference", "approved_at", "expires_at", "purpose",
        "snapshot_path", "snapshot_sha256", "result_database",
        "experiment_name", "methods", "seeds", "evaluation_budget",
        "configuration", "stopping_condition", "input_provenance",
        "human_review",
    }
    if required - set(payload):
        raise ExperimentAuthorizationError("Authorization payload is incomplete")
    if (isinstance(payload["schema_version"], bool)
            or payload["schema_version"] != 1
            or payload["decision"] != "approved"):
        raise ExperimentAuthorizationError("Authorization is not an approved version-1 record")
    for field in ("approval_id", "approved_by", "approval_reference", "experiment_name",
                  "snapshot_path", "snapshot_sha256", "result_database", "input_provenance"):
        if not isinstance(payload[field], str) or not payload[field].strip():
            raise ExperimentAuthorizationError(f"Authorization field {field} is required")
    if len(payload["snapshot_sha256"]) != 64 or any(
        char not in "0123456789abcdef" for char in payload["snapshot_sha256"]
    ):
        raise ExperimentAuthorizationError("Approved snapshot SHA-256 is malformed")
    if not isinstance(payload["methods"], list) or not payload["methods"]:
        raise ExperimentAuthorizationError("Authorization methods must be a nonempty list")
    if any(not isinstance(method, str) or not method.strip()
           for method in payload["methods"]):
        raise ExperimentAuthorizationError("Authorization methods must be strings")
    if len(set(payload["methods"])) != len(payload["methods"]):
        raise ExperimentAuthorizationError("Authorization methods must be unique")
    if not isinstance(payload["seeds"], list) or not payload["seeds"]:
        raise ExperimentAuthorizationError("Authorization seeds must be a nonempty list")
    if any(isinstance(seed, bool) or not isinstance(seed, int) or seed < 0
           for seed in payload["seeds"]):
        raise ExperimentAuthorizationError("Authorization seeds must be non-negative integers")
    if len(set(payload["seeds"])) != len(payload["seeds"]):
        raise ExperimentAuthorizationError("Authorization seeds must be unique")
    if isinstance(payload["evaluation_budget"], bool) or not isinstance(
        payload["evaluation_budget"], int
    ) or payload["evaluation_budget"] < 0:
        raise ExperimentAuthorizationError("Authorization evaluation budget is invalid")
    if not isinstance(payload["configuration"], dict):
        raise ExperimentAuthorizationError("Authorization configuration must be an object")
    if payload["stopping_condition"] != "objective_evaluations":
        raise ExperimentAuthorizationError("Authorization stopping condition is unsupported")
    if payload["purpose"] != CONTROLLED_EXPERIMENT_PURPOSE:
        raise ExperimentAuthorizationError("Authorization purpose is unsupported")
    review = payload["human_review"]
    if not isinstance(review, dict) or review.get("status") != "complete":
        raise ExperimentAuthorizationError("Completed human dataset review is required")
    for field in ("reviewer", "review_reference", "reviewed_at"):
        if not isinstance(review.get(field), str) or not review[field].strip():
            raise ExperimentAuthorizationError(f"Human review field {field} is required")


def _parse_timestamp(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ExperimentAuthorizationError(f"Authorization timestamp {label} is required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ExperimentAuthorizationError(f"Authorization timestamp {label} is invalid") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ExperimentAuthorizationError(f"Authorization timestamp {label} must include a timezone")
    return parsed.astimezone(timezone.utc)
