"""Import all models to register with SQLAlchemy."""
from backend_api.models.models import (
    User,
    Faculty,
    Qualification,
    Availability,
    Subject,
    Section,
    WorkloadPolicy,
    Allocation,
)

__all__ = [
    "User",
    "Faculty",
    "Qualification",
    "Availability",
    "Subject",
    "Section",
    "WorkloadPolicy",
    "Allocation",
]

