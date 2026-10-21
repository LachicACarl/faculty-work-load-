# Experiment Authorization Security Status

## Current decision: execution disabled

Controlled experiment execution is disabled in this repository. No
institution-controlled trust provider, protected key provisioning mechanism,
or durable approval-consumption ledger is available here. The CLI entry point
and direct `ExperimentRunner` entry points fail closed unless a trusted host
injects an authorization service. The shipped CLI has no such service and
therefore cannot launch experiments.

The `ExperimentAuthorizationService` is an integration contract, not a
production service. Tests use an explicitly synthetic verifier and an
in-memory ledger. That harness demonstrates call ordering and denial behavior;
it is not durable, institutionally trusted, or deployable as approval evidence.
The signed JSON format below describes fields that a future provider may
verify. It does not grant permission.

## Threat model

| Actor or boundary | Capability and current treatment |
| --- | --- |
| CLI operator choosing environment variables | Environment variables no longer select the signing key. The shipped CLI has no trust provider and denies execution. |
| Local user able to alter repository files | Can alter local code and test fixtures. A dirty checkout is not a trusted execution host; use a reviewed immutable deployment before any future run. |
| Arbitrary Python code in the same interpreter | Treated as trusted code. Python private methods and module objects are not security boundaries. Such code can call internal helpers or raw optimizer classes. If this actor must be resisted, move execution into a separate restricted process or service. |
| Institutionally authorized operator | Must use a future protected host that independently verifies the institutional trust anchor and atomically consumes approvals through a durable ledger. That host is not implemented here. |

Protected assets include institutional workload snapshots, approval
authenticity and scope, single-use approval state, and experiment output
integrity. Relevant entry points are the CLI `main`, `run_comparison`,
`ExperimentRunner.create_experiment`, `ExperimentRunner.run_trial`, and the
private computation helper. Only the private helper performs optimization
without its own authorization check; it is not a security boundary against
arbitrary code in the interpreter. Public runner and CLI entry points require
an injected host service, and the shipped CLI supplies none.

## Enforced behavior in this checkout

- `verify_experiment_authorization` verifies the signed payload only when
  given an explicit Ed25519 public key. It no longer reads a key path from an
  environment variable.
- The CLI `main` rejects execution before parsing paths or opening input files.
- `run_comparison`, `create_experiment`, and `run_trial` reject execution when
  no authorization service is provided.
- The public `ExperimentRunner` constructor does not accept a caller-supplied
  grant. Each public `create_experiment` call asks the injected host service to
  authorize the manifest; the service must consume the approval ID atomically.
- A host service must validate the signature, purpose, human-review evidence,
  snapshot path and bytes, result database path, and complete run plan.
- The CLI obtains and validates a manifest grant through the host service before
  creating the output path. It then passes the grant through a private
  same-process persistence handoff. That helper is not a security boundary
  against arbitrary code in the trusted process.
- The host service must verify each trial against the consumed approval and
  manifest binding.
- Service authorization errors propagate before manifest or trial persistence.
  Database/schema errors after successful authorization remain operational
  failures and may leave an output artifact.

These are interface and fail-closed guarantees, not an implemented institutional
deployment. A custom service passed by arbitrary Python code is not trusted
merely because it implements the protocol. The host that injects it must be
under trusted control.

`ExperimentAuthorizationGrant` is a data object, not a cryptographic or
independently one-use token. It is not accepted through the public runner API.
The private CLI handoff assumes trusted code in the same process and must not be
exposed as an external integration surface. A future host service must keep
grant issuance and handoff under host control and atomically consume approval
IDs in durable storage. Arbitrary same-process code remains outside this
repository's threat model.

## Trust provider required before enabling runs

A production provider must obtain the Ed25519 public key from an independent
trust anchor whose identity and permissions are controlled outside the caller's
request. A path or environment variable alone is insufficient when the caller
can replace either the path or file. The deployment must document protected
ownership and permissions, operator identity, key rotation and revocation,
backup/recovery, and how the provider authenticates the approval signer.

The provider must reject absent, malformed, wrong-type, untrusted, expired, or
out-of-scope approvals. The human reviewer and data owner must be verified by
the institution's governance process; strings in a signed payload do not prove
their authority.

## Durable single-use and revocation service required

The unique `authorization_id` constraint in `experiment_runs` prevents
duplicates only while that results database remains intact. It does not
prevent replay after deletion or recreation of the results database. This
repository has no institution-controlled approval ledger, revocation service,
or atomic consumption implementation, so durable replay protection is **not
implemented**.

Before enabling execution, the provider must atomically consume an approval ID
in durable storage bound to the exact authorization and manifest, reject
concurrent or later reuse, expose revocation, and define recovery behavior
after a crash between consumption and result persistence. Ledger unavailability
must deny execution. A consumed approval may be lost if output persistence
fails; recovery must require a new approved authorization unless the ledger has
a reviewed recovery protocol. The results database must not be the only replay
record.

The CLI creates its output file only after successful authorization. A later
database creation, schema, or persistence failure can therefore leave an empty
or partial output artifact and consume the approval. Such a failure is not an
authorization denial; recovery must follow the host's documented policy and
must not silently reuse the consumed approval.

## Same-process execution boundary

Python cannot prevent arbitrary code in the same interpreter from importing
private helpers, monkey-patching objects, or invoking optimizer classes. The
current supported-entry-point checks assume the application host's code is
trusted. They do not protect against a hostile plugin, shell user with arbitrary
Python access to the process, or a modified checkout. If that threat is in
scope, use a separate privileged process/service with a narrow authenticated
interface; it must independently verify authorization and consume the approval.
No such process or service is available in this repository, so execution stays
disabled.

## Synthetic tests

Tests generate ephemeral keys and use an in-memory ledger with synthetic
fixtures in temporary or in-memory databases. The ledger tests demonstrate the
expected service contract, including denial on duplicate use across recreated
temporary result databases and concurrent consumption attempts. Public runner
calls cannot accept a previously issued grant; the private CLI handoff is
trusted same-process code. These tests do not prove durable replay protection,
trust-key provisioning, institutional signer identity, or permission to use
any dataset.

## Separate approval requirements

Even after the technical provider exists, execution requires actual written
data-owner approval for the specific purpose and snapshot, completed human
dataset review, a frozen and validated de-identified snapshot, and an approved
source revision. Software tests and test signatures satisfy none of these
requirements.
