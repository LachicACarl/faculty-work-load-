"""Health check endpoints."""
from fastapi import APIRouter
from backend_api.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        database="initialized"
    )
