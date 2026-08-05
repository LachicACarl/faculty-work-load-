from fastapi import APIRouter

from backend_api.api.sample_data import SAMPLE_SECTIONS, SAMPLE_SUBJECTS

router = APIRouter()


@router.get("/")
def list_curriculum() -> dict[str, list[dict[str, object]]]:
    return {"subjects": SAMPLE_SUBJECTS, "sections": SAMPLE_SECTIONS}
