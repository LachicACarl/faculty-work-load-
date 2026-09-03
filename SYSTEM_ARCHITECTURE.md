# Faculty Workload Allocation System - Architecture & Data Flow

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         WEB BROWSER (React SPA)                                  │
│  http://localhost:5173/dashboard                                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────────────────────────────┐    │
│ │ Presentation Layer - UI Components & Pages                              │    │
│ ├──────────────────────────────────────────────────────────────────────────┤    │
│ │ • Dashboard.tsx           → Run optimization, view status               │    │
│ │ • ScenarioBuilder.tsx     → Simulate policies, adjust weights          │    │
│ │ • AllocationReview.tsx    → Approve/flag assignments                   │    │
│ │ • Faculty.tsx             → Manage faculty profiles                     │    │
│ │ • Analytics.tsx           → KPI trends and metrics                      │    │
│ │ • Reports.tsx             → Export workload summaries                   │    │
│ └──────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        ▼ (HTTP/JSON)
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend Server (Port 8001)                            │
│  http://127.0.0.1:8001                                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ API Routes Layer (REST Endpoints)                                        │   │
│  ├──────────────────────────────────────────────────────────────────────────┤   │
│  │ ┌─ /health ─────────────────────────────────┐                            │   │
│  │ ├─ /api/faculty/* ──────────────────────────┤ CRUD Operations           │   │
│  │ ├─ /api/curriculum/* ──────────────────────┤                            │   │
│  │ ├─ /api/workload/policy-profiles ──────────┤                            │   │
│  │ ├─ /api/workload/optimize ─────────────────┤ ◄─── Main Orchestration   │   │
│  │ ├─ /api/analytics/kpi-history ─────────────┤                            │   │
│  │ ├─ /api/reports/workload-summary ──────────┤                            │   │
│  │ └─ /api/institutional/snapshot ────────────┘                            │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                  ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ Optimization Engine (Core Logic)                                         │   │
│  ├──────────────────────────────────────────────────────────────────────────┤   │
│  │                                                                            │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │   │
│  │  │ 1. DATA PREPARATION                                              │    │   │
│  │  │    ├─ Load faculty (employment_type, max_units, qualifications)  │    │   │
│  │  │    ├─ Load sections (schedule, required_specialization)         │    │   │
│  │  │    ├─ Load policies (ft_max, pt_max, overload_limit)           │    │   │
│  │  │    └─ Generate eligible pairs (feasible allocations)           │    │   │
│  │  └─────────────────────────────────────────────────────────────────┘    │   │
│  │                                          ▼                                │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │   │
│  │  │ 2. GENETIC ALGORITHM (Global Exploration)                        │    │   │
│  │  │    genetic_algorithm.py                                          │    │   │
│  │  │    ┌──────────────────────────────────────────────────────────┐ │    │   │
│  │  │    │ • Population size: 30-50 chromosomes                     │ │    │   │
│  │  │    │ • Generations: 50-100 iterations                         │ │    │   │
│  │  │    │ • Selection: Tournament (k=3)                            │ │    │   │
│  │  │    │ • Crossover: Two-point (85% rate)                       │ │    │   │
│  │  │    │ • Mutation: Reassign/Insert/Delete (15% rate)           │ │    │   │
│  │  │    │ • Elitism: Preserve best solution each generation        │ │    │   │
│  │  │    │                                                            │ │    │   │
│  │  │    │ Output: Best GA solution (elite chromosome)             │ │    │   │
│  │  │    └──────────────────────────────────────────────────────────┘ │    │   │
│  │  └─────────────────────────────────────────────────────────────────┘    │   │
│  │                                          ▼                                │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │   │
│  │  │ 3. CONSTRAINT REPAIR (Feasibility Restoration)                 │    │   │
│  │  │    constraint_repair.py                                         │    │   │
│  │  │    ┌──────────────────────────────────────────────────────────┐ │    │   │
│  │  │    │ Detect Violations:                                       │ │    │   │
│  │  │    │  • V_h1: Schedule conflicts                             │ │    │   │
│  │  │    │  • V_h2: Workload overloads                             │ │    │   │
│  │  │    │  • V_h3: Specialization mismatches                      │ │    │   │
│  │  │    │                                                            │ │    │   │
│  │  │    │ Repair Strategy:                                         │ │    │   │
│  │  │    │  1. Reassign conflicting faculty                         │ │    │   │
│  │  │    │  2. Remove problematic allocations                       │ │    │   │
│  │  │    │  3. Reorder to respect consecutive limits                │ │    │   │
│  │  │    │                                                            │ │    │   │
│  │  │    │ Output: Feasible or near-feasible solution               │ │    │   │
│  │  │    └──────────────────────────────────────────────────────────┘ │    │   │
│  │  └─────────────────────────────────────────────────────────────────┘    │   │
│  │                                          ▼                                │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │   │
│  │  │ 4. FEASIBILITY CHECK (Validation Checkpoint)                    │    │   │
│  │  │    constraint_repair.py / FeasibilityCheck                      │    │   │
│  │  │    ┌──────────────────────────────────────────────────────────┐ │    │   │
│  │  │    │ Validation: V_h(x) = 0? (all hard constraints met)      │ │    │   │
│  │  │    │                                                            │ │    │   │
│  │  │    │ ✓ Pass → Proceed to Tabu Search                         │ │    │   │
│  │  │    │ ✗ Fail → Re-repair or flag for review                   │ │    │   │
│  │  │    └──────────────────────────────────────────────────────────┘ │    │   │
│  │  └─────────────────────────────────────────────────────────────────┘    │   │
│  │                                          ▼                                │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │   │
│  │  │ 5. TABU SEARCH (Local Refinement)                               │    │   │
│  │  │    tabu_search.py                                               │    │   │
│  │  │    ┌──────────────────────────────────────────────────────────┐ │    │   │
│  │  │    │ • Tabu tenure: 10 iterations                             │ │    │   │
│  │  │    │ • Max iterations: 200                                    │ │    │   │
│  │  │    │ • Neighborhood: Reassign, Exchange, Insert, Delete      │ │    │   │
│  │  │    │ • Aspiration criteria: Override tabu if better           │ │    │   │
│  │  │    │ • Diversification: Limit neighborhood size               │ │    │   │
│  │  │    │                                                            │ │    │   │
│  │  │    │ Output: Elite solution (best found)                     │ │    │   │
│  │  │    └──────────────────────────────────────────────────────────┘ │    │   │
│  │  └─────────────────────────────────────────────────────────────────┘    │   │
│  │                                          ▼                                │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐    │   │
│  │  │ 6. EXPLANATION & OUTPUT GENERATION                              │    │   │
│  │  │    fitness.py                                                    │    │   │
│  │  │    ┌──────────────────────────────────────────────────────────┐ │    │   │
│  │  │    │ For each allocation (faculty → section):                │ │    │   │
│  │  │    │  1. Calculate match_quality (specialization match %)   │ │    │   │
│  │  │    │  2. Generate explanation                              │ │    │   │
│  │  │    │     "Assigned Dr. Santos to CS301 with 100% match"    │ │    │   │
│  │  │    │  3. Calculate workload_balance (utilization %)        │ │    │   │
│  │  │    │  4. Set approval_status (pending)                     │ │    │   │
│  │  │    │                                                            │ │    │   │
│  │  │    │ Output: OptimizationResponse                            │ │    │   │
│  │  │    │  • allocations[] (with explanations)                   │ │    │   │
│  │  │    │  • total_fitness                                       │ │    │   │
│  │  │    │  • avg_match_quality                                   │ │    │   │
│  │  │    │  • total_conflicts                                     │ │    │   │
│  │  │    │  • metrics {}                                          │ │    │   │
│  │  │    └──────────────────────────────────────────────────────────┘ │    │   │
│  │  └─────────────────────────────────────────────────────────────────┘    │   │
│  │                                                                            │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                  ▼                                               │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │ Data Persistence Layer (SQLAlchemy ORM)                                  │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
│                                  ▼                                               │
└─────────────────────────────────────────────────────────────────────────────────┘
                                  ▼
        ┌─────────────────────────────────────────────────┐
        │         SQLite Database                         │
        │  faculty_workload.db                            │
        ├─────────────────────────────────────────────────┤
        │ Tables:                                          │
        │ • users          → Admin/faculty accounts       │
        │ • faculty        → Faculty profiles             │
        │ • qualifications → Degrees & specializations    │
        │ • availability   → Teaching time slots          │
        │ • subjects       → Course catalog               │
        │ • sections       → Section instances            │
        │ • workload_policies → Policy profiles           │
        │ • allocations    → Final assignments (results)  │
        └─────────────────────────────────────────────────┘
```

---

## Data Flow: End-to-End Optimization

```
User Action: Click "Run Optimization"
                    ▼
        POST /api/workload/optimize
                    ▼
    ┌─────────────────────────────────┐
    │ 1. Query Database               │
    │    - Load active faculty        │
    │    - Load unassigned sections   │
    │    - Load policy settings       │
    └─────────────────────────────────┘
                    ▼
    ┌─────────────────────────────────┐
    │ 2. Build Data Structures        │
    │    - faculty_specs dict         │
    │    - sections_data dict         │
    │    - policies_dict              │
    │    - eligible_pairs list        │
    └─────────────────────────────────┘
                    ▼
    ┌─────────────────────────────────┐
    │ 3. Initialize GA                │
    │    - population_size=30         │
    │    - generations=50             │
    │    - mutation_rate=0.15         │
    │    - crossover_rate=0.85        │
    └─────────────────────────────────┘
                    ▼
    ┌─────────────────────────────────┐
    │ 4. Evolve Population (50 gen)   │
    │    - Initialize random pop      │
    │    - Evaluate fitness           │
    │    - Select parents             │
    │    - Crossover & mutate         │
    │    - Preserve elite             │
    │    → best_ga_chromosome         │
    └─────────────────────────────────┘
                    ▼
    ┌─────────────────────────────────┐
    │ 5. Repair Constraints           │
    │    - Detect violations          │
    │    - Reassign conflicts         │
    │    - Remove problematic allocs  │
    │    → repaired_allocations       │
    └─────────────────────────────────┘
                    ▼
    ┌─────────────────────────────────┐
    │ 6. Validate Feasibility         │
    │    - Check V_h(x) = 0           │
    │    - If fail, re-repair         │
    │    - If pass, proceed           │
    │    → feasible_allocations       │
    └─────────────────────────────────┘
                    ▼
    ┌─────────────────────────────────┐
    │ 7. Tabu Search (200 iter)       │
    │    - Generate neighborhood      │
    │    - Find best non-tabu move    │
    │    - Apply aspiration criteria  │
    │    - Update tabu list           │
    │    → best_tabu_solution         │
    └─────────────────────────────────┘
                    ▼
    ┌─────────────────────────────────┐
    │ 8. Generate Explanations        │
    │    - For each allocation:       │
    │      • Calculate match quality  │
    │      • Generate text explanation│
    │      • Compute workload %       │
    │    → explained_allocations      │
    └─────────────────────────────────┘
                    ▼
    ┌─────────────────────────────────┐
    │ 9. Persist Results              │
    │    - Save to allocations table  │
    │    - Link to run_id             │
    │    - Store metrics              │
    │    → database updated           │
    └─────────────────────────────────┘
                    ▼
    ┌─────────────────────────────────┐
    │ 10. Return Response             │
    │     OptimizationResponse        │
    │     ├─ run_id                   │
    │     ├─ timestamp                │
    │     ├─ status: "success"        │
    │     ├─ allocations[]            │
    │     ├─ total_fitness            │
    │     ├─ avg_match_quality        │
    │     ├─ total_conflicts          │
    │     └─ metrics {}               │
    └─────────────────────────────────┘
                    ▼
    Frontend receives response
    Updates UI with results
    User sees allocations with explanations
    → AllocationReview page ready for approval
```

---

## Fitness Calculation Example

```
Given allocation: Dr. Santos → CS301 (Machine Learning)

Input:
- Faculty: Dr. Santos
  - specializations: ["Machine Learning"]
  - max_units: 21
  - current_load: 8 units

- Section: CS301
  - subject.name: "Machine Learning"
  - units: 4
  - required_specialization: "Machine Learning"

- Policy:
  - specialization_required: true
  - balance_priority: 0.7

Calculation:

1. Specialization Match
   - Required: "Machine Learning"
   - Faculty specialization: "Machine Learning"
   - Match: EXACT (100%)
   - F_specialization = 1.0

2. Utilization Impact
   - Current load: 8 units
   - New load: 8 + 4 = 12 units
   - Max allowed: 21 units
   - Utilization: 12/21 = 57.1%
   - Target: 85%
   - Deviation: |57.1 - 85| = 27.9%
   - Penalty: 1.0 - (27.9 * 1.2%) = 0.67
   - F_utilization = 0.67

3. Composite Fitness
   - w_specialization = 0.3 (1 - balance_priority)
   - w_utilization = 0.7 (balance_priority)
   - F(x) = 0.3 * 1.0 + 0.7 * 0.67 = 0.3 + 0.47 = 0.77

4. Output
   - match_quality: 1.0 (100% specialization match)
   - match_level: "Exact"
   - workload_balance: 0.57 (57% utilization)
   - explanation: "Assigned Dr. Maria Santos to Machine Learning with 
                   100% specialization match and 57% workload utilization"
```

---

## Constraint Examples

### Hard Constraint V_h1: Schedule Conflict
```
Faculty: Prof. Wilson
Available: Tue 9AM-1PM, Thu 2PM-5PM

Section: CS101-A
Schedule: Tue 11AM-1PM (within availability) ✓

Section: CS301-A
Schedule: Mon 10AM-12PM (NOT in availability) ✗
→ VIOLATION: Schedule conflict detected
→ ACTION: Reassign CS301-A to different faculty
```

### Hard Constraint V_h2: Workload Overload
```
Faculty: Dr. Emily Chen (Part-time)
Max units: 12
Overload allowed: 0 (part-time)
Current assignments: CS101 (3 units), CS201 (4 units)
Current load: 7 units

New section: CS301 (4 units)
New load: 7 + 4 = 11 units ✓ (within 12)

Another section: CS501 (3 units)
Total: 11 + 3 = 14 units ✗ (exceeds 12)
→ VIOLATION: Workload overload
→ ACTION: Reassign CS501 to full-time faculty or remove
```

### Hard Constraint V_h3: Specialization Required
```
Faculty: Prof. Brown
Specializations: ["Data Science", "Web Development"]

Section: CS301 - Machine Learning
Required: "Machine Learning"
Match: NO specialization match ✗
→ VIOLATION: Specialization mismatch

If policy.specialization_required = true:
→ ACTION: Reassign to Dr. Santos (has "Machine Learning")

If policy.specialization_required = false:
→ ALLOWED: Soft penalty in fitness score (-0.2 points)
```

---

## Performance Metrics

```
Standard Test Case (6 sections, 4 faculty):

GA Phase:
  • Population: 30
  • Generations: 50
  • Avg fitness progression: 0.55 → 0.78
  • Time: ~2-3 seconds

Constraint Repair:
  • Initial violations: 2-4
  • Violations after repair: 0
  • Time: <1 second

Tabu Search:
  • Iterations: 200
  • Improvements: 15-25% over GA solution
  • Final fitness: 0.85-0.92
  • Time: ~3-5 seconds

Total Pipeline: ~5-8 seconds
→ Real-time interactive experience for users
```

---

## Configuration & Customization

### Adjust GA Parameters (backend_api/core/config.py)
```python
GA_POPULATION_SIZE = 50      # Larger = more exploration
GA_GENERATIONS = 100         # More = better solution (slower)
GA_MUTATION_RATE = 0.15      # 0-1: Higher = more variation
GA_CROSSOVER_RATE = 0.85     # 0-1: Higher = more inheritance
```

### Adjust Tabu Search Parameters
```python
TABU_TENURE = 10             # Iterations move stays tabu
TABU_MAX_ITERATIONS = 200    # Local search depth
```

### Adjust Policy Weights (Frontend or API)
```json
{
  "balance_priority": 0.7,     // 0-1: Weight for utilization
  "specialization_required": true,
  "ft_max_units": 21,
  "pt_max_units": 12
}
```

---

**End of Architecture & Data Flow Documentation**
