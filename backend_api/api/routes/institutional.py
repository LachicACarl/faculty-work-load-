from fastapi import APIRouter

from backend_api.api.sample_data import INSTITUTIONAL_SOURCES, SAMPLE_FACULTY, SAMPLE_SECTIONS, SAMPLE_SUBJECTS

router = APIRouter()


@router.get("/snapshot")
def institutional_snapshot() -> dict[str, object]:
    return {
        "sources": INSTITUTIONAL_SOURCES,
        "faculty": SAMPLE_FACULTY,
        "curriculum": {
            "subjects": SAMPLE_SUBJECTS,
            "sections": SAMPLE_SECTIONS,
        },
    }