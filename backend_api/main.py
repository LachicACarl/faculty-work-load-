from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend_api.api.routes import analytics, curriculum, faculty, institutional, reports, workload
from backend_api.core.config import settings


app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(faculty.router, prefix="/api/faculty", tags=["faculty"])
app.include_router(curriculum.router, prefix="/api/curriculum", tags=["curriculum"])
app.include_router(institutional.router, prefix="/api/institutional", tags=["institutional"])
app.include_router(workload.router, prefix="/api")
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}
