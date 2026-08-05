from copy import deepcopy

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend_api.api.sample_data import SAMPLE_FACULTY

router = APIRouter()

FACULTY_STORE = deepcopy(SAMPLE_FACULTY)


class FacultyUpdate(BaseModel):
    name: str | None = None
    department: str | None = None
    employment_type: str | None = None
    specializations: list[str] | None = None
    min_units: float | None = Field(default=None, ge=0)
    max_units: float | None = Field(default=None, ge=0)
    current_load: float | None = Field(default=None, ge=0)
    degrees: list[str] | None = None
    availability: dict[str, list[str]] | None = None


class FacultyCreate(FacultyUpdate):
    id: str


@router.get("/")
def list_faculty() -> list[dict[str, object]]:
    return FACULTY_STORE


@router.post("/")
def create_faculty(payload: FacultyCreate) -> dict[str, object]:
    if any(item["id"] == payload.id for item in FACULTY_STORE):
        raise HTTPException(status_code=409, detail="Faculty id already exists")

    record: dict[str, object] = {
        "id": payload.id,
        "name": payload.name,
        "employee_code": payload.id,
        "department": payload.department or "IT",
        "employment_type": payload.employment_type or "Full-time",
        "tenure_status": (payload.employment_type or "Full-time") == "Full-time",
        "specializations": payload.specializations or [],
        "min_units": payload.min_units if payload.min_units is not None else 0.0,
        "max_units": payload.max_units if payload.max_units is not None else 18.0,
        "current_load": payload.current_load if payload.current_load is not None else 0.0,
        "degrees": payload.degrees or [],
        "availability": payload.availability or {"Mon": [], "Tue": [], "Wed": [], "Thu": [], "Fri": []},
    }
    FACULTY_STORE.append(record)
    return record


@router.patch("/{faculty_id}")
def update_faculty(faculty_id: str, payload: FacultyUpdate) -> dict[str, object]:
    for index, item in enumerate(FACULTY_STORE):
        if item["id"] != faculty_id:
            continue

        updated = {**item}
        if payload.name is not None:
            updated["name"] = payload.name
        if payload.department is not None:
            updated["department"] = payload.department
        if payload.employment_type is not None:
            updated["employment_type"] = payload.employment_type
            updated["tenure_status"] = payload.employment_type == "Full-time"
        if payload.specializations is not None:
            updated["specializations"] = payload.specializations
        if payload.min_units is not None:
            updated["min_units"] = payload.min_units
        if payload.max_units is not None:
            updated["max_units"] = payload.max_units
        if payload.current_load is not None:
            updated["current_load"] = payload.current_load
        if payload.degrees is not None:
            updated["degrees"] = payload.degrees
        if payload.availability is not None:
            updated["availability"] = payload.availability

        FACULTY_STORE[index] = updated
        return updated

    raise HTTPException(status_code=404, detail="Faculty member not found")
