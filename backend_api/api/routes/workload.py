"""Workload optimization endpoints."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import uuid
from datetime import datetime

from backend_api.core.database import get_db
from backend_api.models import Allocation, Faculty, Section, Subject, WorkloadPolicy
from backend_api.schemas import (
    OptimizationRequest, OptimizationResponse, AllocationDetailResponse,
    WorkloadPolicyResponse
)
from backend_api.optimization_engine import (
    GeneticAlgorithm, ConstraintRepair, FeasibilityCheck,
    TabuSearch, FitnessEvaluator
)

router = APIRouter()

# Storage for optimization runs (in production, use database)
optimization_runs = {}


@router.get("/policy-profiles", response_model=List[WorkloadPolicyResponse])
def get_policy_profiles(db: Session = Depends(get_db)):
    """Get available workload policy profiles."""
    policies = db.query(WorkloadPolicy).filter(WorkloadPolicy.active == True).all()
    
    if not policies:
        # Create default policy if none exist
        default_policy = WorkloadPolicy(
            name="Default Policy",
            ft_max_units=21,
            pt_max_units=12,
            overload_limit=3,
            specialization_required=True,
            consecutive_limit=2,
            balance_priority=0.7,
            active=True
        )
        db.add(default_policy)
        db.commit()
        return [default_policy]
    
    return policies


@router.post("/optimize", response_model=OptimizationResponse)
def run_optimization(
    request: OptimizationRequest,
    db: Session = Depends(get_db)
):
    """Execute the optimization algorithm."""
    run_id = str(uuid.uuid4())
    
    try:
        # Get policy
        if request.policy_id:
            policy = db.query(WorkloadPolicy).filter(
                WorkloadPolicy.id == request.policy_id
            ).first()
        else:
            policy = db.query(WorkloadPolicy).filter(
                WorkloadPolicy.active == True
            ).first()
        
        if not policy:
            raise HTTPException(status_code=404, detail="Policy not found")
        
        # Override policy with request parameters if provided
        ft_max = request.ft_max_units if request.ft_max_units is not None else policy.ft_max_units
        pt_max = request.pt_max_units if request.pt_max_units is not None else policy.pt_max_units
        overload_limit = request.overload_limit if request.overload_limit is not None else policy.overload_limit
        spec_required = request.specialization_required if request.specialization_required is not None else policy.specialization_required
        balance_priority = request.balance_priority if request.balance_priority is not None else policy.balance_priority
        
        # Fetch data for optimization
        faculty_list = db.query(Faculty).filter(Faculty.available == True).all()
        sections_list = db.query(Section).filter(Section.assigned == False).all()
        
        if not faculty_list or not sections_list:
            return OptimizationResponse(
                run_id=run_id,
                timestamp=datetime.utcnow(),
                status="failed",
                allocations=[],
                total_fitness=0.0,
                avg_match_quality=0.0,
                total_conflicts=0,
                facultyWithConflicts=[],
                metrics={"error": "Insufficient faculty or sections"}
            )
        
        # Prepare data structures for optimization
        faculty_specs = {}
        for fac in faculty_list:
            faculty_specs[fac.id] = {
                "id": fac.id,
                "full_name": fac.full_name,
                "employment_type": fac.employment_type,
                "max_units": pt_max if fac.employment_type == "part-time" else ft_max,
                "overload_allowed": overload_limit,
                "qualifications": [
                    {
                        "degree": q.degree,
                        "specialization": q.specialization,
                        "proficiency_level": q.proficiency_level
                    }
                    for q in fac.qualifications
                ],
                "availability": [
                    {
                        "day_of_week": a.day_of_week,
                        "start_time": a.start_time,
                        "end_time": a.end_time
                    }
                    for a in fac.availability
                ]
            }
        
        sections_data = {}
        for sec in sections_list:
            subject = sec.subject
            sections_data[sec.id] = {
                "id": sec.id,
                "section_code": sec.section_code,
                "subject_id": subject.id,
                "name": subject.name,
                "code": subject.code,
                "units": subject.units,
                "required_specialization": subject.required_specialization,
                "schedule_day": sec.schedule_day,
                "schedule_start_time": sec.schedule_start_time,
                "schedule_end_time": sec.schedule_end_time,
                "enrollment": sec.enrollment
            }
        
        policies_dict = {
            "ft_max_units": ft_max,
            "pt_max_units": pt_max,
            "overload_limit": overload_limit,
            "specialization_required": spec_required,
            "balance_priority": balance_priority
        }
        
        # Generate eligible pairs without weakening institutional policy.
        constraint_repair = ConstraintRepair(faculty_specs, sections_data, policies_dict)
        eligible_pairs = [
            (fac_id, sec_id)
            for fac_id in faculty_specs
            for sec_id in sections_data
            if (
                not spec_required
                or not sections_data[sec_id].get("required_specialization")
                or constraint_repair._has_specialization(
                    fac_id, sections_data[sec_id]["required_specialization"]
                )
            )
        ]
        if not eligible_pairs:
            raise HTTPException(
                status_code=422,
                detail="No faculty-section pairs satisfy the active specialization policy."
            )

        fitness_eval = FitnessEvaluator(faculty_specs, sections_data, policies_dict)
        ga = GeneticAlgorithm(
            population_size=30,
            generations=50,
            mutation_rate=0.15,
            crossover_rate=0.85,
        )
        best_ga = ga.evolve(
            fitness_func=lambda chromosome: fitness_eval.evaluate(chromosome.allocations),
            eligible_pairs=eligible_pairs,
        )

        repaired = constraint_repair.repair(best_ga.allocations, eligible_pairs)
        feasibility_check = FeasibilityCheck(constraint_repair)
        ts = TabuSearch(tabu_tenure=10, max_iterations=100)
        best_solution = ts.refine(
            initial_solution=repaired,
            fitness_func=fitness_eval.evaluate,
            eligible_pairs=eligible_pairs,
        )

        if not feasibility_check.is_feasible(best_solution):
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "No fully feasible allocation could be generated; no allocations were saved.",
                    "violations": [
                        {
                            "type": violation.type,
                            "faculty_id": violation.faculty_id,
                            "section_id": violation.section_id,
                            "details": violation.details,
                        }
                        for violation in constraint_repair.detect_violations(best_solution)
                    ],
                },
            )

        allocations_response = []
        total_fitness = fitness_eval.evaluate(best_solution)
        total_units_by_faculty = {}
        for faculty_id, section_id in best_solution:
            total_units_by_faculty[faculty_id] = (
                total_units_by_faculty.get(faculty_id, 0) + sections_data[section_id]["units"]
            )

        for faculty_id, section_id in best_solution:
            fac = faculty_specs[faculty_id]
            sec = sections_data[section_id]
            details = fitness_eval.get_allocation_details(faculty_id, section_id)
            max_units = max(int(fac["max_units"]), 1)
            workload_balance = min(1.0, total_units_by_faculty[faculty_id] / max_units)
            alloc = AllocationDetailResponse(
                faculty_name=fac["full_name"],
                faculty_id=faculty_id,
                section_code=sec["section_code"],
                subject_name=sec["name"],
                subject_code=sec["code"],
                semester=sec["semester"],
                units=sec["units"],
                match_quality=details["match_quality"],
                match_level=details["match_level"],
                workload_balance=workload_balance,
                conflict_score=0.0,
                explanation=details["explanation"],
                approval_status="pending",
            )
            allocations_response.append(alloc)
            db.add(Allocation(
                faculty_id=faculty_id,
                section_id=section_id,
                optimization_run_id=run_id,
                match_quality=details["match_quality"],
                workload_balance=workload_balance,
                conflict_score=0.0,
                explanation=details["explanation"],
                approval_status="pending",
            ))

        try:
            db.commit()
        except Exception:
            db.rollback()
            raise

        # Store run data
        optimization_runs[run_id] = {
            "allocations": allocations_response,
            "timestamp": datetime.utcnow(),
            "total_fitness": total_fitness
        }
        
        avg_match = (sum(a.match_quality for a in allocations_response) / len(allocations_response)
                    if allocations_response else 0.0)
        
        return OptimizationResponse(
            run_id=run_id,
            timestamp=datetime.utcnow(),
            status="success",
            allocations=allocations_response,
            total_fitness=total_fitness,
            avg_match_quality=avg_match,
            total_conflicts=len([a for a in allocations_response if a.conflict_score > 0]),
            facultyWithConflicts=[a.faculty_name for a in allocations_response if a.conflict_score > 0],
            metrics={
                "ga_generations": len(ga.fitness_history),
                "ts_iterations": len(ts.iteration_history),
                "total_sections": len(sections_list),
                "assigned_sections": len(allocations_response),
                "unassigned_sections": len(sections_list) - len(allocations_response)
            }
        )
    
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Workload optimization failed. Check the protected server logs.")
        return OptimizationResponse(
            run_id=run_id,
            timestamp=datetime.utcnow(),
            status="failed",
            allocations=[],
            total_fitness=0.0,
            avg_match_quality=0.0,
            total_conflicts=0,
            facultyWithConflicts=[],
            metrics={"error": str(e)}
        )


@router.get("/allocations", response_model=List[AllocationDetailResponse])
def get_allocations(run_id: str = None, db: Session = Depends(get_db)):
    """Get allocations from a specific run or latest run."""
    query = db.query(Allocation)
    if run_id:
        query = query.filter(Allocation.optimization_run_id == run_id)
    
    allocations = query.all()
    
    result = []
    for alloc in allocations:
        faculty = alloc.faculty
        section = alloc.section
        subject = section.subject
        
        result.append(AllocationDetailResponse(
            faculty_name=faculty.full_name,
            faculty_id=faculty.id,
            section_code=section.section_code,
            subject_name=subject.name,
            subject_code=subject.code,
            semester=section.semester,
            units=subject.units,
            match_quality=alloc.match_quality,
            match_level="Exact" if alloc.match_quality > 0.8 else "Partial" if alloc.match_quality > 0.5 else "Unmatched",
            workload_balance=alloc.workload_balance,
            conflict_score=alloc.conflict_score,
            explanation=alloc.explanation,
            approval_status=alloc.approval_status
        ))
    
    return result


@router.put("/allocations/{allocation_id}/status")
def update_allocation_status(
    allocation_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    """Update the approval status of an allocation."""
    allocation = db.query(Allocation).filter(Allocation.id == allocation_id).first()
    
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")
    
    if status not in ["pending", "approved", "flagged"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    allocation.approval_status = status
    db.commit()
    
    return {
        "id": allocation.id,
        "status": allocation.approval_status,
        "message": f"Allocation status updated to {status}"
    }
