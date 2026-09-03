"""SQLAlchemy ORM models for Faculty Workload System."""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime

from backend_api.core.database import Base


class User(Base):
    """Administrator and faculty system users."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(String)  # admin, dean, faculty
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    faculty = relationship("Faculty", back_populates="user")


class Faculty(Base):
    """Faculty member profiles."""
    __tablename__ = "faculty"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    employee_id = Column(String, unique=True, index=True)
    full_name = Column(String)
    employment_type = Column(String)  # full-time, part-time
    tenure_status = Column(String)  # tenured, non-tenured
    max_units = Column(Integer)  # Department policy limit
    overload_allowed = Column(Integer, default=0)  # Additional units allowed
    available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="faculty")
    qualifications = relationship("Qualification", back_populates="faculty", cascade="all, delete-orphan")
    availability = relationship("Availability", back_populates="faculty", cascade="all, delete-orphan")
    allocations = relationship("Allocation", back_populates="faculty")


class Qualification(Base):
    """Faculty academic qualifications and specializations."""
    __tablename__ = "qualifications"
    
    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id"))
    degree = Column(String)  # BS, MS, PhD, etc.
    specialization = Column(String, index=True)
    institution = Column(String)
    year_awarded = Column(Integer)
    proficiency_level = Column(Float, default=1.0)  # 0.0-1.0 match score
    
    faculty = relationship("Faculty", back_populates="qualifications")


class Availability(Base):
    """Faculty teaching availability windows."""
    __tablename__ = "availability"
    
    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id"))
    day_of_week = Column(Integer)  # 0=Mon, 6=Sun
    start_time = Column(String)  # HH:MM format
    end_time = Column(String)  # HH:MM format
    recurring = Column(Boolean, default=True)
    
    faculty = relationship("Faculty", back_populates="availability")


class Subject(Base):
    """Course catalog entries."""
    __tablename__ = "subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    name = Column(String)
    units = Column(Integer)  # Credit/teaching units
    required_specialization = Column(String, nullable=True)
    min_class_size = Column(Integer, default=1)
    max_class_size = Column(Integer, default=50)
    active = Column(Boolean, default=True)
    
    sections = relationship("Section", back_populates="subject")


class Section(Base):
    """Specific course section instance."""
    __tablename__ = "sections"
    
    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    section_code = Column(String, index=True)
    semester = Column(String)  # e.g., "Fall2024"
    schedule_day = Column(Integer)  # 0=Mon, 6=Sun
    schedule_start_time = Column(String)
    schedule_end_time = Column(String)
    room = Column(String, nullable=True)
    enrollment = Column(Integer, default=0)
    assigned = Column(Boolean, default=False)
    
    subject = relationship("Subject", back_populates="sections")
    allocation = relationship("Allocation", back_populates="section", uselist=False)


class WorkloadPolicy(Base):
    """Institutional workload constraints and policies."""
    __tablename__ = "workload_policies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    version = Column(Integer, default=1)
    ft_max_units = Column(Integer)  # Full-time max
    pt_max_units = Column(Integer)  # Part-time max
    overload_limit = Column(Integer)  # Max additional units
    specialization_required = Column(Boolean, default=True)
    consecutive_limit = Column(Integer, default=2)  # Max consecutive hours
    balance_priority = Column(Float, default=0.7)  # 0-1 weighting
    created_at = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)


class Allocation(Base):
    """Final faculty-section assignment output."""
    __tablename__ = "allocations"
    
    id = Column(Integer, primary_key=True, index=True)
    faculty_id = Column(Integer, ForeignKey("faculty.id"))
    section_id = Column(Integer, ForeignKey("sections.id"))
    optimization_run_id = Column(String, index=True)  # Track which optimization run produced this
    match_quality = Column(Float)  # 0-1 specialization match
    workload_balance = Column(Float)  # Faculty utilization %
    conflict_score = Column(Float, default=0.0)  # 0 = no conflicts
    explanation = Column(Text)  # Why this assignment was made
    approval_status = Column(String, default="pending")  # pending, approved, flagged
    created_at = Column(DateTime, default=datetime.utcnow)
    
    faculty = relationship("Faculty", back_populates="allocations")
    section = relationship("Section", back_populates="allocation")
