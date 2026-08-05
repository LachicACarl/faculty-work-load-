from pydantic import BaseModel


class FacultyRead(BaseModel):
    id: int
    employee_code: str
    department: str
    employment_type: str
    tenure_status: bool
