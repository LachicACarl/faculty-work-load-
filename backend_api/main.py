"""Faculty Workload Allocation System - FastAPI Backend"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend_api.core.config import settings
from backend_api.core.database import init_db
from backend_api.api.routes import health, faculty, curriculum, workload, analytics, reports, institutional


# Initialize database on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    print("✓ Database initialized")
    yield
    # Shutdown
    print("✓ Application shutting down")


# Create FastAPI app
app = FastAPI(
    title="Faculty Workload Allocation System",
    description="Optimization-based faculty workload allocation using Modified Hybrid GA + Tabu Search",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(faculty.router, prefix="/api/faculty", tags=["Faculty"])
app.include_router(curriculum.router, prefix="/api/curriculum", tags=["Curriculum"])
app.include_router(workload.router, prefix="/api/workload", tags=["Workload"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(institutional.router, prefix="/api/institutional", tags=["Institutional"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend_api.main:app",
        host="127.0.0.1",
        port=8001,
        reload=True
    )
