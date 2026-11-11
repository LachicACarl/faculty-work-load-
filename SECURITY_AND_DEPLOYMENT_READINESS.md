# Institutional Deployment Readiness

## Current decision: NOT APPROVED FOR INSTITUTIONAL OR PRODUCTION DATA

This repository is a development prototype. The following controls are absent or incomplete:
- The login page is a non-authenticating preview.
- API routes expose faculty, curriculum, allocation, reporting and institutional data without an authentication/authorization dependency.
- Role definitions exist in the data model, but there is no enforced role-based access control.
- The database is configured for SQLite by default and database initialization uses create_all rather than a reviewed migration chain.
- There is no tested institutional backup/restore process, audit log, retention policy, incident procedure, or security monitoring.
- The optimization engine currently has correctness defects recorded below.
- The committed database file has unknown provenance and may contain non-synthetic data. Do not use it as a production seed or copy it into another environment.

## Required release gates

1. **Identity and access**
   - Institution selects and provisions an identity provider (prefer OIDC/SAML SSO).
   - Validate issuer, audience, signature, expiry, nonce/state and key rotation.
   - Enforce server-side roles and institution/department scope on every protected route.
   - Require MFA according to institutional policy; define account disablement and session revocation.
   - Keep secrets in an approved secret manager. Never commit credentials or use a frontend-only gate.
2. **Data governance**
   - Data owner approves the purpose, fields, retention, permitted users and lawful institutional basis.
   - Inventory, classify and de-identify the existing SQLite file before any reuse.
   - Define retention, deletion, export, disclosure and incident response procedures.
3. **Database**
   - Select an institution-managed PostgreSQL service, configure TLS and least-privilege DB credentials.
   - Adopt Alembic migrations; do not rely on create_all for production schema changes.
   - Enforce foreign keys, uniqueness, required fields and transaction boundaries.
   - Test encrypted backups and restore to a clean environment; document RPO/RTO.
4. **Application security**
   - Restrict CORS to exact institutional origins; do not use wildcard origins with credentials.
   - Return generic errors; keep stack traces and internal exceptions in protected logs.
   - Validate inputs, paginate list endpoints, rate-limit authentication and costly optimization jobs.
   - Record immutable audit events for sensitive reads, exports, policy changes, allocation runs and approvals.
5. **Workload governance**
   - Have the institution formally approve workload limits, overload, teaching hours/units, availability, class sizes, rooms, and consecutive-hour rules.
   - Require human review before an allocation is published or applied.
   - Store each optimization run as a reproducible, versioned scenario; do not silently overwrite prior allocations.
   - Independently validate complete coverage, duplicate assignments, schedules, qualifications and workload.
6. **Operations**
   - Add CI for backend tests, frontend build/lint, dependency audit and migration checks.
   - Deploy to a controlled staging environment first, then conduct UAT, security testing and recovery exercises.
   - Establish monitoring, alerting, patch cadence, vulnerability response and an accountable system owner.

## Confirmed code defects to remediate

- The workload route calls `TabuSearch.refine` using incompatible keyword arguments and a lambda signature.
- It does not strictly reject an infeasible final allocation before persisting it as a successful run.
- Empty eligibility silently falls back to all faculty-section combinations, undermining specialization policy.
- Section assignment coverage, duplicate section IDs, schedule overlap, room conflict and enrollment bounds are not comprehensively checked by the production validator.
- Workload KPI values and dashboard history are hard-coded demonstration values.
- CSV endpoint constructs `FileResponse` without a real file path; an in-memory CSV must use `StreamingResponse`.
- Frontend fallback fabricates optimization results when API requests fail; this must be removed.
- Main dashboard presents hard-coded faculty counts, section counts, utilization, history, logs and match rows.
- The committed database and generated dependency/cache artifacts must not be shipped as application source.

A production sign-off requires all release gates above, independent security review, institutional data-owner approval and documented user acceptance. This checklist is not itself an authorization to process institutional data.


## Remediation branch notes

- CI workflow: `.github/workflows/ci.yml` runs backend unit tests and the frontend production build on pull requests to `main`.
- Generated frontend `node_modules` and tracked Python bytecode/cache directories were removed from the remediation branch tree; `.gitignore` now prevents re-adding them.
- The optimization validator now checks complete coverage, duplicate and unknown references, qualification policy, maximum workload, availability, valid time intervals, faculty and room overlap, enrollment bounds, and consecutive teaching-time caps.
- The optimization API creates pending proposals only after independent feasibility validation; pending or approved proposals prevent the same section from being selected again. Approval marks the section assigned; flagging releases it for a future run.
- CSV, dashboard, KPI, and institutional summaries now use approved assignment records rather than mock values or pending proposals.
- Production startup now fails closed when `APP_ENV=production`; this is a deliberate safety stop, not an implemented authentication solution.

## Still blocking institutional deployment

The production identity provider, server-side role and institution scoping, migration framework, database TLS/least-privilege policy, audit trail, data-owner review of `faculty_workload.db`, tested backups/restores, and deployment/UAT are still not implemented. Do not set `APP_ENV=production` until those controls have been delivered and independently verified. The existing SQLite file is retained unchanged pending documented data-owner disposition.
