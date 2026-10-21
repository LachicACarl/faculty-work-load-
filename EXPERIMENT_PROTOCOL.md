# Stage 5.4.2 Experiment Protocol

## Status and research question

This is a preregistered protocol, not a report of measured performance. No full
comparison has been run and no method is claimed to be better.

The question is whether the implemented hybrid allocation pipeline produces a
higher feasible-run rate and, among feasible outputs, a higher workload fitness
score than the GA-only and Tabu-only pipelines under the same objective-call
budget. Comparisons are two-sided; the protocol does not assume the hybrid wins.

## Problem instances and provenance

There are currently no verified, representative, deidentified institutional
problem-instance files in `backend_api`. The only identified instance is the
small hand-authored fixture in
`backend_api/tests/test_optimization_engine.py::build_fixture` (two faculty,
two sections). It is synthetic test data, not institutional data, and is useful
only for execution and persistence smoke tests. The provenance of
`faculty_workload.db` has not been established in this audit, so it is excluded
from experiment inputs and was not read or changed.

A performance study must wait for one or more approved, deidentified snapshots
with documented source, extraction date, semester, inclusion rules, and any
transformations. Before use, retain written data-owner approval that identifies
the permitted purpose and dataset scope; document the source, extraction date,
semester, de-identification method, inclusion/exclusion rules, transformations,
and schema version. Validate the frozen JSON against the experiment input
schema, run the shared hard-feasibility validator, and have an authorized
reviewer confirm that the snapshot is representative for its stated claim.
Keep unresolved EARIST extracts out of the application database. Record a
stable identity as the SHA-256 of the exact approved JSON bytes in the approval
record alongside the existing canonical `input_fingerprint`; the fingerprint
alone does not include provenance. The manifest/trials already retain the
snapshot and provenance, so this gate adds no database columns or migration.

Supply each snapshot as UTF-8 JSON with integer-ID object keys:

```json
{
  "provenance": "Deidentified source, semester, extraction date, and transformations",
  "faculty_specs": {"101": {"max_units": 6, "overload_allowed": 0,
    "qualifications": [], "availability": []}},
  "sections_data": {"201": {"units": 3, "schedule_day": 0,
    "schedule_start_time": "08:00", "schedule_end_time": "10:00",
    "required_specialization": "Example", "semester": "Example",
    "room": null, "enrollment": 20, "is_planning": false,
    "min_class_size": 1, "max_class_size": 50}},
  "policies": {"specialization_required": true, "consecutive_limit": 2,
    "balance_priority": 0.7}
}
```

The example is a format illustration only, not a study dataset. The saved trial
contains the complete supplied snapshot and its provenance, so the fingerprint
can be checked and the input reconstructed. The fingerprint by itself is only
a checksum and is not a reconstruction source. Snapshot storage may contain
sensitive schedule or qualification data; only approved deidentified inputs
belong in the isolated results database.

## Compared methods

- **GA-only:** random eligible-pair population initialization and Genetic
  Algorithm generations. It does not call repair or Tabu Search.
- **Tabu-only:** deterministic first-eligible-pair-per-section initialization
  and Tabu Search. It does not call GA or hybrid repair. If that initial
  allocation fails the shared validator, the trial completes infeasible without
  searching from another start.
- **Hybrid:** GA with constraint repair followed by Tabu Search. The GA receives
  half the total objective-call budget (rounded down, with a minimum of one when
  the total budget is positive); Tabu receives the remaining calls.

These are comparisons of the current **pipelines**, not a controlled
ablation of the search algorithms alone. Their initialization differs, only
the hybrid invokes repair, and Tabu's current implementation is deterministic
so the seed does not change its path. Initialization, feasibility checks,
repair attempts, and neighborhood construction are not objective evaluations.
Their computational cost is reflected in separately recorded wall runtime.
The implementation does not claim equal total CPU work from equal objective
call counts.

## Objective, constraints, and budget

All methods maximize the same `FitnessEvaluator` score in `[0, 1]`:

`(1 - balance_priority) * specialization_fitness + balance_priority * utilization_fitness`.

The objective is scored only for candidates accepted by the shared
`FeasibilityCheck` during search. The evaluation budget is the maximum number
of actual calls to `FitnessEvaluator.evaluate` per trial, not the only
condition that can stop a search. The shared counter covers GA
initialization and generations, Tabu initial and neighborhood candidates, and
any failed objective call. Feasibility checks and repair calculations do not
consume objective calls. The completed score reuses the last measured candidate
score; it does not make a hidden final call.

### Effective stopping conditions and recorded termination

Each method has its own configured search limit in addition to the shared
maximum objective-call budget. A method can stop before using the full budget
when its generation/iteration cap is reached or its search has no useful move.
These are parts of the compared pipeline configuration and must be reported;
they are not equivalent amounts of compute across methods.

- **GA-only:** stops at `ga_generations` or the objective-call budget. Its
  internal termination reasons include `generation_limit`, `budget_exhausted`,
  and `no_feasible_candidate`.
- **Tabu-only:** stops at `tabu_max_iterations`, `local_optimum`,
  `no_available_moves`, `infeasible_initial_candidate`, or the objective-call
  budget. These are the internal termination reasons recorded by the current
  implementation.
- **Hybrid:** gives GA at most half of the total evaluation budget (rounded
  down, with a minimum of one for a positive budget), then gives unused calls
  to Tabu when calls remain. Either phase can also stop at its configured
  generation/iteration or search limit. Diagnostics preserve
  `ga_termination_reason` and `tabu_termination_reason` when both phases run;
  the top-level `termination_reason` records the runner's terminal reason.
- **Trial status:** `succeeded` means a feasible result completed before the
  maximum evaluation budget was exhausted, including completion at a search
  limit. `budget_exhausted` means the call cap stopped search with a feasible
  retained candidate. `completed_infeasible` means no feasible complete
  candidate was returned. `failed` records an unexpected exception, and
  `running` is a persisted trial interrupted before terminal update.

`ExperimentTrial` stores the top-level termination reason, status, effective
configuration (including generation/iteration caps), objective-call count, and
diagnostics JSON. The `stopping_condition` manifest value
`objective_evaluations` describes the maximum call budget; it does not mean
that generation and iteration caps are disabled. A new stopping rule or
terminal reason requires a protocol revision and tests before benchmarking.

The final candidate is independently rechecked with the same
`FeasibilityCheck` used by the production allocation route. Hard constraints
include complete assignment of required sections, no duplicate section
assignments, valid faculty and section IDs, faculty availability,
specialization policy, workload limits including allowed overload, faculty
schedule non-overlap, enrollment bounds, room-time conflicts, and the
consecutive-section policy.

## Fixed plan

- Seeds: `101` through `120`, matched across all methods for each instance.
- Repetitions: 20 trials per instance and method (60 rows per instance).
- Maximum objective-call budget: 2,000 per trial.
- Manifest stopping-condition label: `objective_evaluations`, meaning the
  maximum evaluator-call count. The configured GA generation limit and Tabu
  iteration limit, plus natural search stops, can terminate a trial earlier;
  save and report the actual termination reason for every trial.
- Effective configuration: GA population 30, 50 generations, mutation rate
  0.15, crossover rate 0.85, Tabu tenure 10, and 100 Tabu iterations. These
  values must be recorded in each trial; a change requires a protocol revision
  before execution.
- Runtime: `time.perf_counter()` elapsed seconds around optimization and final
  validation, excluding database persistence. Record Python, platform,
  dependency versions, source revision, and dirty-tree state with each trial.

An experiment is complete only when its persisted trial count equals
`3 * number_of_seeds` for each input instance. Running rows indicate interruption;
missing rows indicate work that never started. Both invalidate a complete
comparison until the missing work is rerun and retained.

## Outcome handling and metrics

Status meanings:

- `succeeded`: completed with a feasible candidate before using the entire
  budget.
- `budget_exhausted`: the budget stopped search and the retained candidate is
  feasible.
- `completed_infeasible`: execution returned no feasible complete candidate;
  `termination_reason` still records whether budget exhaustion caused the stop.
- `failed`: an unexpected exception occurred; its code, message, objective-call
  count, and partial run record remain saved.
- `running`: a persisted trial was interrupted before it could be finalized.

The primary metric is feasible-run rate, with all scheduled rows in the
denominator; failed and incomplete rows are not silently dropped. Secondary
metrics are objective score among feasible completed candidates only,
objective-call count, runtime, violation count, and assigned/unassigned section
counts. Failed and infeasible objective sentinel values are excluded from
objective summaries and shown separately by status. Budget-exhausted feasible
solutions remain eligible for objective summaries.

## Planned analysis

Pair methods by `(input_fingerprint, seed)`. Report counts and feasibility rate
for every status, and report feasible-only objective means, medians, standard
deviations, ranges, and per-trial values. Report runtime and evaluation counts
separately. The current analysis helper is descriptive and makes no significance
claim.

For a single fixed instance with the planned 20 matched seeds, use exact
McNemar tests on paired feasibility outcomes and two-sided Wilcoxon signed-rank
tests on objective differences for pairs where both methods are feasible.
Report paired median differences and a paired bootstrap interval when the
number of valid pairs supports it. Apply Holm correction to the two prespecified
hybrid-vs-baseline comparisons. If fewer than 10 valid pairs remain, or
assumptions for the planned test fail, report descriptive results only. Tabu is
deterministic under the current implementation; its repeated rows are the same
baseline, not 20 independent Tabu realizations. Do not use them to claim a
stochastic Tabu performance distribution.

Analyze rows from one `ExperimentRun` manifest at a time. The analysis helpers
validate agreement on manifest ID, input fingerprint and snapshot, provenance,
configuration (excluding the intentionally varied per-trial seed), evaluation
budget, stopping-condition label, implementation version, and runtime/source
environment. Pass the manifest to `summarize_trials` and
`paired_method_comparison` so absent planned seeds are listed explicitly.
Without the manifest (or planned counts for summaries), analysis marks exact
missing counts unknown; it still reports status counts and unmatched feasible
trials. The manifest's
seed and method lists define the planned matrix; `experiment_completeness`
checks recorded, missing, and running rows. Do not merge trials from separate
manifests into one summary or paired comparison.

`implementation_version` and the recorded source environment are the existing
compatibility markers; the schema has no separate objective-formula version.
The current implementation shares one `FitnessEvaluator` and records objective
direction in diagnostics. If the objective changes, increment the implementation
version and revise this protocol before comparing trials. This does not add a
database field or imply a migration.

No trial may be removed based on its score. Exclusions are limited to
predeclared input corruption or infrastructure failure and must be reported by
method and reason; failed and interrupted trials remain in the result database.

## Isolated execution workflow

### Authorization gate

**Controlled experiment execution is disabled in this checkout.** The CLI
entry point rejects requests before reading input paths. Direct runner methods
also reject calls unless a trusted host injects an authorization service. No
production service, institution-controlled trust anchor, or durable approval
ledger is implemented here. An environment variable or a locally generated
key cannot enable institutional execution.

The `run_comparison` service-injection seam exists for trusted host integration
and synthetic tests only. Test keys and in-memory ledgers are not production
authorization. Do not invoke it with institutional data. See
`EXPERIMENT_AUTHORIZATION.md` for the threat model, enforced behavior, and
required infrastructure. Do not treat the old command-line workflow as
executable; a new reviewed deployment procedure is required after the missing
provider and ledger exist.

## Known gaps before performance claims

- Representative approved institutional input snapshots and their provenance
  are missing.
- No institution-verified trusted signing key or signed approval envelope has
  been provisioned; human authorization and review remain pending.
- No protected trust-provider or durable approval-consumption/revocation
  service exists. Approval reuse after results-database recreation is not
  prevented by this repository; experiment execution is disabled.
- The Python implementation assumes same-process code is trusted. If hostile
  code in the application interpreter must be resisted, a separately isolated
  privileged execution service is required.
- Tabu's deterministic first-eligible initialization can fail even when another
  feasible initialization exists; the planned result is a pipeline comparison
  and must state this limitation.
- Repair, feasibility, initialization, and neighborhood costs are outside the
  objective-call budget; runtime is therefore required for interpretation.
- Existing databases created before the Stage 5.4.2 trial columns need a
  separately reviewed migration. This work does not migrate or write to
  `faculty_workload.db`.
- A dirty working tree prevents source-level historical reproducibility even
  though the trial records the base revision and dirty status. Formal runs must
  use a committed revision.
