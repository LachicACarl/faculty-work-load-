from pydantic import BaseModel, Field


class ObjectiveWeights(BaseModel):
    spec_match: float = 10.0
    utilization: float = 5.0
    conflict: float = 50.0
    policy_violation: float = 40.0
    unassigned: float = 30.0


class PolicyProfileInput(BaseModel):
    id: str = "custom"
    name: str = "Custom Scenario"
    full_time_max_units: float = 21.0
    part_time_max_units: float = 12.0
    allowable_overload: float = 3.0
    specialization_required: bool = True
    consecutive_limit: int = 2
    balance_priority: float = 70.0
    utilization_target: float = 80.0


class SectionInput(BaseModel):
    id: str
    code: str
    required_specialization: str
    day: str
    start_time: float
    end_time: float
    units: float = 3.0


class FacultyInput(BaseModel):
    id: str
    name: str
    specializations: list[str] = Field(default_factory=list)
    min_units: float = 9.0
    max_units: float = 18.0


class OptimizeWorkloadRequest(BaseModel):
    sections: list[SectionInput] = Field(default_factory=list)
    faculty: list[FacultyInput] = Field(default_factory=list)
    policy_profile: PolicyProfileInput = Field(default_factory=PolicyProfileInput)
    objective_weights: ObjectiveWeights = Field(default_factory=ObjectiveWeights)
