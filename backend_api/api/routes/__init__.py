"""API routes initialization."""
from backend_api.api.routes import (
    health,
    faculty,
    curriculum,
    workload,
    analytics,
    reports,
    institutional
)

__all__ = [
    "health",
    "faculty",
    "curriculum",
    "workload",
    "analytics",
    "reports",
    "institutional",
]
