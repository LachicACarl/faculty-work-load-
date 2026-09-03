"""Pydantic schemas for request/response validation."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ───── Faculty Schemas ─────
class QualificationBase(BaseModel):
    degree: str
    specialization: str
    institution: str
    year_awarded: int
    proficiency_level: float = Field(default=1.0, ge=0.0, le=1.0)


class QualificationResponse(QualificationBase):
    id: int
    faculty_id: int
    
    class Config:
        from_attributes = True


class AvailabilityBase(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_time: str  # HH:MM
    end_time: str  # HH:MM
    recurring: bool = True


class AvailabilityResponse(AvailabilityBase):
    id: int
    faculty_id: int
    
    class Config:
        from_attributes = True


class FacultyBase(BaseModel):
    employee_id: str
    full_name: str
    employment_type: str  # full-time, part-time
    tenure_status: str
    max_units: int
    overload_allowed: int = 0
    available: bool = True


class FacultyCreate(FacultyBase):
    qualifications: Optional[List[QualificationBase]] = []
    availability: Optional[List[AvailabilityBase]] = []


class FacultyResponse(FacultyBase):
    id: int
    user_id: Optional[int]
    created_at: datetime
    qualifications: List[QualificationResponse]
    availability: List[AvailabilityResponse]
    
    class Config:
        from_attributes = True


class FacultyList(BaseModel):
    id: int
    employee_id: str
    full_name: str
    employment_type: str
    max_units: int
    available: bool


# ───── Curriculum Schemas ─────
class SubjectBase(BaseModel):
    code: str
    name: str
    units: int
    required_specialization: Optional[str] = None
    min_class_size: int = 1
    max_class_size: int = 50
    active: bool = True


class SubjectResponse(SubjectBase):
    id: int
    
    class Config:
        from_attributes = True


class SectionBase(BaseModel):
    subject_id: int
    section_code: str
    semester: str
    schedule_day: int
    schedule_start_time: str
    schedule_end_time: str
    room: Optional[str] = None
    enrollment: int = 0
    assigned: bool = False


class SectionResponse(SectionBase):
    id: int
    
    class Config:
        from_attributes = True


# ───── Workload Policy Schemas ─────
class WorkloadPolicyBase(BaseModel):
    name: str
    ft_max_units: int
    pt_max_units: int
    overload_limit: int
    specialization_required: bool = True
    consecutive_limit: int = 2
    balance_priority: float = Field(default=0.7, ge=0.0, le=1.0)
    active: bool = True


class WorkloadPolicyResponse(WorkloadPolicyBase):
    id: int
    version: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# ───── Allocation Schemas ─────
class AllocationBase(BaseModel):
    faculty_id: int
    section_id: int
    match_quality: float
    workload_balance: float
    conflict_score: float = 0.0
    explanation: str
    approval_status: str = "pending"


class AllocationResponse(AllocationBase):
    id: int
    optimization_run_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ───── Optimization Request/Response ─────
class OptimizationRequest(BaseModel):
    """Request to run the optimization algorithm."""
    policy_id: Optional[int] = None  # Use default policy if not specified
    scenario_weights: Optional[dict] = None  # Custom weights for objectives
    ft_max_units: Optional[int] = None
    pt_max_units: Optional[int] = None
    overload_limit: Optional[int] = None
    specialization_required: Optional[bool] = None
    balance_priority: Optional[float] = None


class AllocationDetailResponse(BaseModel):
    """Detail view of a single allocation with faculty and section info."""
    faculty_name: str
    faculty_id: int
    section_code: str
    subject_name: str
    subject_code: str
    semester: str
    units: int
    match_quality: float
    match_level: str  # Exact, Partial, Unmatched
    workload_balance: float
    conflict_score: float
    explanation: str
    approval_status: str


class OptimizationResponse(BaseModel):
    """Response from optimization run."""
    run_id: str
    timestamp: datetime
    status: str  # success, partial, failed
    allocations: List[AllocationDetailResponse]
    total_fitness: float
    avg_match_quality: float
    total_conflicts: int
    facultyWithConflicts: List[str]  # Faculty names with conflicts
    metrics: dict  # Additional metrics


class OptimizationRunLog(BaseModel):
    """Log entry for optimization run."""
    run_id: str
    timestamp: datetime
    event: str
    event_type: str  # info, warning, error, success
    details: Optional[dict] = None


# ───── Analytics Schemas ─────
class KPIDataPoint(BaseModel):
    timestamp: str
    metric_name: str
    value: float


class KPIHistory(BaseModel):
    kpi_points: List[KPIDataPoint]
    metric_summary: dict


class WorkloadSummaryRow(BaseModel):
    faculty_name: str
    employment_type: str
    assigned_units: int
    max_units: int
    utilization_percent: float
    num_sections: int
    avg_match_quality: float
    conflicts: int


# ───── Health Check ─────
class HealthResponse(BaseModel):
    status: str
    version: str
    database: str


# ───── Institutional Snapshot ─────
class InstitutionalSnapshot(BaseModel):
    total_faculty: int
    total_sections: int
    total_subjects: int
    faculty_full_time: int
    faculty_part_time: int
    avg_specialization_match: float
    total_workload_units: int
    avg_utilization: float
    timestamp: datetime
