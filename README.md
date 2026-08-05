# Faculty Workload Allocation System

This repository contains a decoupled optimization-based faculty workload allocation platform.

## Structure

- `backend_api/`: FastAPI backend, database models, and optimization engine.
- `frontend_app/`: React dashboard for workload analysis, scenario simulation, and allocation review.

## Backend

The backend is organized into:

- `api/`: REST routes and dependencies.
- `core/`: application settings and database wiring.
- `models/`: SQLAlchemy ORM models.
- `schemas/`: Pydantic request and response models.
- `optimization_engine/`: genetic algorithm, constraint repair, tabu search, and fitness scoring.

## Frontend

The frontend provides the BI dashboard and administrative workflows described in the blueprint:

- dashboard analytics
- faculty management
- policy scenario simulation
- allocation review with explainability

## Run Locally

Prerequisites:

- Python 3.13+
- Node.js 18+

### Backend

1. Open a terminal in the repository root.
2. Install Python dependencies:

```bash
python -m pip install -r backend_api/requirements.txt
```

3. Start the API server:

```bash
python -m uvicorn --app-dir . backend_api.main:app --host 127.0.0.1 --port 8001
```

4. Verify the service:

```bash
curl http://127.0.0.1:8001/health
```

### Frontend

1. Open a second terminal in `frontend_app/`.
2. Install JavaScript dependencies:

```bash
npm install
```

3. Start the dashboard:

```bash
npm run dev
```

4. Build a production bundle when needed:

```bash
npm run build
```

## Notes

- The backend optimization endpoint is exposed at `/api/workload/optimize`.
- The dashboard Run Optimization action now calls the backend optimization API.
- The Scenario Builder now loads policy profiles from `/api/workload/policy-profiles` and posts real scenario weights to `/api/workload/optimize`.
- The Analytics page reads workload KPI history from `/api/analytics/kpi-history`.
- The Reports page exports workload summaries from `/api/reports/workload-summary.csv`.
- Institutional snapshot data is available from `/api/institutional/snapshot`.
- The default frontend API base URL is `http://127.0.0.1:8001` and can be overridden using `VITE_API_BASE_URL`.
- Demo input data is available from `/api/faculty/` and `/api/curriculum/` for local end-to-end testing.
- The as-is and to-be flow diagrams live in `SYSTEM_FLOW_STATUS.md`.
