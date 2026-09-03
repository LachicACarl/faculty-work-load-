# Faculty Workload Allocation System - Quick Start Guide

## 🚀 System Status: FULLY OPERATIONAL

```
✅ Backend API:        Running on http://127.0.0.1:8001
✅ Frontend Dashboard: Running on http://localhost:5173  
✅ Database:          Seeded with demo data
✅ Optimization:      Ready for allocation optimization
```

---

## 📱 Quick Access URLs

| Component | URL | Purpose |
|-----------|-----|---------|
| **Dashboard** | http://localhost:5173/dashboard | View and run optimizations |
| **Scenario Builder** | http://localhost:5173/scenario-builder | Test policies |
| **Allocations** | http://localhost:5173/allocations | Review and approve |
| **Reports** | http://localhost:5173/reports | Export summaries |
| **API Docs** | http://127.0.0.1:8001/docs | Interactive API playground |
| **Health Check** | http://127.0.0.1:8001/health | Backend status |

---

## 🎯 First-Time User: 5-Minute Quick Start

### Step 1: Verify Backend is Running
```bash
curl http://127.0.0.1:8001/health
```
Expected response:
```json
{"status": "healthy", "version": "1.0.0", "database": "initialized"}
```

### Step 2: Open Dashboard
Navigate to: **http://localhost:5173/dashboard**

### Step 3: Run Optimization
1. Click **"Run Optimization"** button
2. System automatically:
   - Loads 4 faculty with qualifications and availability
   - Loads 6 course sections across the week
   - Runs hybrid GA + Constraint Repair + Tabu Search
   - Generates explanations for each assignment
3. Results appear within 5-10 seconds

### Step 4: Review Allocations
Navigate to: **http://localhost:5173/allocations**
- See each faculty → section assignment
- View quality score (0-100%)
- Read explanation text
- Approve or flag problematic assignments

### Step 5: Try Scenarios
Navigate to: **http://localhost:5173/scenario-builder**
1. Select a policy or create custom
2. Adjust balance_priority (specialization vs. utilization weight)
3. Click "Simulate"
4. Compare results vs. previous run

---

## 📊 Key Features

### Optimization Algorithm
- **Hybrid Metaheuristic**: Genetic Algorithm + Constraint Repair + Tabu Search
- **Hard Constraints**: No schedule conflicts, workload limits, specialization matching
- **Soft Objectives**: Maximize specialization match quality, balance workload utilization
- **Explainability**: Every allocation has text explanation

### Dashboard Capabilities
- ✅ Run optimization with one click
- ✅ View total fitness score
- ✅ Monitor average match quality (%)
- ✅ Track conflict count
- ✅ See faculty utilization percentages

### Allocation Review
- ✅ Faculty → Section assignments
- ✅ Match quality breakdown
- ✅ Workload utilization
- ✅ Specialization match explanation
- ✅ Approve/Flag/Edit status

### Scenario Builder
- ✅ Load policy profiles
- ✅ Adjust policy parameters
- ✅ Simulate optimization
- ✅ Compare scenarios side-by-side

### Analytics & Reports
- ✅ KPI history (7-day trends)
- ✅ Conflict analysis by faculty
- ✅ Export workload summary (CSV)
- ✅ Institutional snapshot

---

## 🔧 API Quick Reference

### Core Optimization Endpoint
```bash
POST /api/workload/optimize
Content-Type: application/json

{
  "policy_id": 1,
  "ft_max_units": 21,
  "pt_max_units": 12,
  "specialization_required": true,
  "balance_priority": 0.7
}
```

**Response:**
```json
{
  "run_id": "uuid-string",
  "status": "success",
  "allocations": [
    {
      "faculty_name": "Dr. Maria Santos",
      "section_code": "CS301-A",
      "subject_name": "Machine Learning",
      "units": 4,
      "match_quality": 1.0,
      "match_level": "Exact",
      "explanation": "Assigned Dr. Maria Santos to Machine Learning with 100% specialization match",
      "approval_status": "pending"
    }
  ],
  "total_fitness": 0.87,
  "avg_match_quality": 0.92,
  "total_conflicts": 0,
  "metrics": {}
}
```

### Fetch Policy Profiles
```bash
GET /api/workload/policy-profiles
```

### Fetch Previous Results
```bash
GET /api/workload/allocations?run_id=<uuid>
```

### Faculty Management
```bash
GET /api/faculty/                          # List all
POST /api/faculty/                         # Create
GET /api/faculty/{id}                      # Get one
PUT /api/faculty/{id}                      # Update
DELETE /api/faculty/{id}                   # Delete
```

### Analytics
```bash
GET /api/analytics/kpi-history             # KPI trends
GET /api/analytics/conflict-analysis       # Conflict breakdown
GET /api/reports/workload-summary          # JSON export
GET /api/reports/workload-summary.csv      # CSV export
```

---

## 📚 Demo Data Included

### Faculty
1. **Dr. Maria Santos** (Full-time, ML specialist)
   - Available: Mon 8AM-12PM, Wed 2PM-6PM
2. **Prof. James Wilson** (Full-time, Web Development)
   - Available: Tue 9AM-1PM, Thu 2PM-5PM
3. **Dr. Emily Chen** (Part-time, Databases)
   - Available: Wed 6PM-9PM, Fri 7PM-10PM
4. **Prof. Michael Brown** (Full-time, Data Science)
   - Available: Tue 8AM-12PM, Fri 2PM-6PM

### Courses (6 Sections)
- CS101-A, CS101-B (Intro Programming, 3 units each)
- CS201-A (Data Structures, 4 units)
- CS301-A (Machine Learning, 4 units)
- CS401-A (Algorithms, 3 units)
- CS501-A (Databases, 3 units)

### Policies
- Default Policy (Fall 2024)
  - Full-time: 21 units max
  - Part-time: 12 units max
  - Overload: 3 units allowed
  - Specialization: Required

---

## 🆘 Troubleshooting

### Backend not responding?
```bash
# Check if server is running
curl http://127.0.0.1:8001/health

# If not, restart:
.\.venv\Scripts\python.exe -m uvicorn --app-dir . backend_api.main:app --host 127.0.0.1 --port 8001 --reload
```

### Frontend showing "Cannot connect to API"?
```bash
# Check backend is on port 8001
netstat -ano | findstr :8001

# Verify frontend .env has:
VITE_API_BASE_URL=http://127.0.0.1:8001
```

### Database issues?
```bash
# Check database file exists
dir faculty_workload.db

# Reseed demo data:
.\.venv\Scripts\python.exe -m backend_api.seed_data
```

### Port already in use?
```bash
# Change backend port (update both API and frontend .env)
.\.venv\Scripts\python.exe -m uvicorn --app-dir . backend_api.main:app --host 127.0.0.1 --port 8002
```

---

## 📖 Documentation Files

- **[IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)** - Complete system overview and phases
- **[SYSTEM_ARCHITECTURE.md](./SYSTEM_ARCHITECTURE.md)** - Architecture diagrams and data flows
- **[backend_api/README.md](./backend_api/README.md)** - Backend API documentation
- **[subject_failure_extracted/README.md](./subject_failure_extracted/README.md)** - Frontend documentation

---

## 🎓 Understanding the Optimization

### What Happens When You Click "Run Optimization"?

1. **Data Collection**: Loads all faculty, sections, and policies from database
2. **Algorithm Execution** (5-8 seconds):
   - GA: Global search with 50 population, 50 generations
   - Constraint Repair: Fixes schedule conflicts and overloads
   - Tabu Search: Local refinement for 200 iterations
3. **Validation**: Checks all hard constraints satisfied
4. **Explanation**: Generates text reason for each assignment
5. **Persistence**: Stores results in database
6. **Response**: Returns to frontend with scores and explanations

### Fitness Score Explained

- **Total Fitness** (0-1 scale):
  - 0.0 = Worst possible allocation
  - 0.5 = Acceptable allocation
  - 1.0 = Perfect allocation (unlikely)
  - Typical: 0.75-0.92

- **Match Quality** (0-1 scale per allocation):
  - Exact specialization match = 1.0
  - Partial match = 0.5
  - No specialization = 0.0

- **Utilization %**:
  - Target: 85% (optimal workload)
  - Too low: Indicates underutilization
  - Too high: Risk of overload

---

## 🚀 Next Steps for Power Users

1. **Customize Policies**: Create new WorkloadPolicy in database
2. **Add Faculty**: POST to `/api/faculty/` with qualifications
3. **Add Sections**: POST to `/api/curriculum/sections` for courses
4. **Tune Algorithm**: Adjust GA parameters in `config.py`
5. **Integrate Historical Data**: Import previous allocations
6. **Deploy to Production**: Migrate SQLite to PostgreSQL

---

**Ready to optimize? Start with the Dashboard! 🎯**

Questions? Check the SYSTEM_ARCHITECTURE.md or API docs at http://127.0.0.1:8001/docs
