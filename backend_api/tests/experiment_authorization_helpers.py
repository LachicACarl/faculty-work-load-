"""Ephemeral signing helpers for synthetic authorization regression tests only."""
from datetime import datetime, timedelta, timezone
import base64
import hashlib
import json
import tempfile
import threading
import uuid
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from backend_api.optimization_engine.experiment import METHODS
from backend_api.optimization_engine.experiment_authorization import (
    CONTROLLED_EXPERIMENT_PURPOSE,
    ExperimentAuthorizationContext,
    ExperimentAuthorizationError,
    ExperimentAuthorizationGrant,
    authorization_scope_sha256,
    canonical_json_bytes,
    verify_experiment_authorization,
)


class SyntheticAuthorizationSigner:
    """Create short-lived signatures for synthetic fixtures inside unit tests."""

    def __init__(self, test_case):
        self.directory = tempfile.TemporaryDirectory()
        test_case.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        private_key = Ed25519PrivateKey.generate()
        self.private_key = private_key
        self.public_key = private_key.public_key()
        public_key_pem = self.public_key.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        self.public_key_path = self.root / "ephemeral-test-public-key.pem"
        self.public_key_path.write_bytes(public_key_pem)
        self._consumed_approvals = {}
        self._ledger_lock = threading.Lock()

    def authorize_manifest(self, context, *, experiment_id, **scope):
        payload = verify_experiment_authorization(
            context, trusted_public_key=self.public_key, **scope
        )
        approval_id = payload["approval_id"]
        with self._ledger_lock:
            if approval_id in self._consumed_approvals:
                raise ExperimentAuthorizationError("Approval has already been consumed")
            self._consumed_approvals[approval_id] = experiment_id
        return ExperimentAuthorizationGrant(
            experiment_id=experiment_id,
            approval_id=approval_id,
            scope_sha256=authorization_scope_sha256(scope),
            payload=payload,
        )

    def authorize_trial(self, context, *, experiment_id, **scope):
        payload = verify_experiment_authorization(
            context, trusted_public_key=self.public_key, **scope
        )
        with self._ledger_lock:
            if self._consumed_approvals.get(payload["approval_id"]) != experiment_id:
                raise ExperimentAuthorizationError(
                    "Approval is not consumed for this experiment manifest"
                )
        return payload

    def snapshot_path(self, label, snapshot_bytes):
        path = self.root / f"{label}-{uuid.uuid4()}.json"
        path.write_bytes(snapshot_bytes)
        return path

    def sign(self, *, snapshot_path, result_database, name, seeds, budget,
             config, provenance, faculty, sections, policies, methods=None,
             payload_updates=None):
        snapshot_bytes = Path(snapshot_path).read_bytes()
        now = datetime.now(timezone.utc)
        payload = {
            "schema_version": 1,
            "approval_id": str(uuid.uuid4()),
            "decision": "approved",
            "approved_by": "Synthetic test harness",
            "approval_reference": "TEST_ONLY: synthetic fixture authorization",
            "approved_at": now.isoformat(),
            "expires_at": (now + timedelta(minutes=10)).isoformat(),
            "purpose": CONTROLLED_EXPERIMENT_PURPOSE,
            "snapshot_path": str(Path(snapshot_path).resolve()),
            "snapshot_sha256": hashlib.sha256(snapshot_bytes).hexdigest(),
            "result_database": _database_identity(result_database),
            "experiment_name": name,
            "methods": list(methods or METHODS),
            "seeds": list(seeds),
            "evaluation_budget": budget,
            "configuration": config.as_dict(),
            "stopping_condition": "objective_evaluations",
            "input_provenance": provenance,
            "human_review": {
                "status": "complete",
                "reviewer": "Synthetic test harness",
                "review_reference": "TEST_ONLY: no institutional data reviewed",
                "reviewed_at": now.isoformat(),
            },
        }
        if payload_updates:
            payload.update(payload_updates)
        envelope = {
            "payload": payload,
            "signature_ed25519": base64.b64encode(
                self.private_key.sign(canonical_json_bytes(payload))
            ).decode("ascii"),
        }
        return ExperimentAuthorizationContext(
            envelope=envelope,
            snapshot_bytes=snapshot_bytes,
            snapshot_path=str(Path(snapshot_path).resolve()),
            result_database=_database_identity(result_database),
            purpose=CONTROLLED_EXPERIMENT_PURPOSE,
        )

    def write(self, context, filename="approval.json"):
        path = self.root / filename
        path.write_bytes(canonical_json_bytes(context.envelope))
        return path


def synthetic_snapshot_bytes(faculty, sections, policies, provenance):
    value = {
        "provenance": provenance,
        "faculty_specs": faculty,
        "sections_data": sections,
        "policies": policies,
    }
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _database_identity(value):
    if value == "sqlite::memory:":
        return value
    return str(Path(value).resolve())
