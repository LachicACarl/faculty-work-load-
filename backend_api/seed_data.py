"""Seed database with demo data."""
from sqlalchemy.orm import Session
from backend_api.core.database import SessionLocal, init_db
from backend_api.models import (
    Faculty, Qualification, Availability,
    Subject, Section, WorkloadPolicy
)


def seed_demo_data():
    """Populate database with sample data for testing."""
    db = SessionLocal()
    
    try:
        # Clear existing data
        db.query(Section).delete()
        db.query(Subject).delete()
        db.query(Availability).delete()
        db.query(Qualification).delete()
        db.query(Faculty).delete()
        db.query(WorkloadPolicy).delete()
        db.commit()
        
        # Create policy
        policy = WorkloadPolicy(
            name="Fall 2024 Policy",
            ft_max_units=21,
            pt_max_units=12,
            overload_limit=3,
            specialization_required=True,
            consecutive_limit=2,
            balance_priority=0.7,
            active=True
        )
        db.add(policy)
        db.commit()
        
        # Create faculty
        faculty_data = [
            {
                "employee_id": "F001",
                "full_name": "Dr. Maria Santos",
                "employment_type": "full-time",
                "tenure_status": "tenured",
                "max_units": 21,
                "qualifications": [
                    {"degree": "PhD", "specialization": "Machine Learning", "institution": "MIT", "year_awarded": 2010}
                ],
                "availability": [
                    {"day_of_week": 0, "start_time": "08:00", "end_time": "12:00"},
                    {"day_of_week": 2, "start_time": "14:00", "end_time": "18:00"},
                ]
            },
            {
                "employee_id": "F002",
                "full_name": "Prof. James Wilson",
                "employment_type": "full-time",
                "tenure_status": "tenured",
                "max_units": 21,
                "qualifications": [
                    {"degree": "MS", "specialization": "Web Development", "institution": "Stanford", "year_awarded": 2008}
                ],
                "availability": [
                    {"day_of_week": 1, "start_time": "09:00", "end_time": "13:00"},
                    {"day_of_week": 3, "start_time": "14:00", "end_time": "17:00"},
                ]
            },
            {
                "employee_id": "F003",
                "full_name": "Dr. Emily Chen",
                "employment_type": "part-time",
                "tenure_status": "non-tenured",
                "max_units": 12,
                "qualifications": [
                    {"degree": "PhD", "specialization": "Databases", "institution": "Berkeley", "year_awarded": 2015}
                ],
                "availability": [
                    {"day_of_week": 2, "start_time": "18:00", "end_time": "21:00"},
                    {"day_of_week": 4, "start_time": "19:00", "end_time": "22:00"},
                ]
            },
            {
                "employee_id": "F004",
                "full_name": "Prof. Michael Brown",
                "employment_type": "full-time",
                "tenure_status": "non-tenured",
                "max_units": 21,
                "qualifications": [
                    {"degree": "MS", "specialization": "Data Science", "institution": "CMU", "year_awarded": 2018}
                ],
                "availability": [
                    {"day_of_week": 1, "start_time": "08:00", "end_time": "12:00"},
                    {"day_of_week": 4, "start_time": "14:00", "end_time": "18:00"},
                ]
            },
        ]
        
        faculty_objs = []
        for fdata in faculty_data:
            fac = Faculty(
                employee_id=fdata["employee_id"],
                full_name=fdata["full_name"],
                employment_type=fdata["employment_type"],
                tenure_status=fdata["tenure_status"],
                max_units=fdata["max_units"]
            )
            
            for qual in fdata["qualifications"]:
                q = Qualification(
                    degree=qual["degree"],
                    specialization=qual["specialization"],
                    institution=qual["institution"],
                    year_awarded=qual["year_awarded"],
                    proficiency_level=1.0
                )
                fac.qualifications.append(q)
            
            for avail in fdata["availability"]:
                a = Availability(
                    day_of_week=avail["day_of_week"],
                    start_time=avail["start_time"],
                    end_time=avail["end_time"]
                )
                fac.availability.append(a)
            
            db.add(fac)
            faculty_objs.append(fac)
        
        db.commit()
        
        # Create subjects
        subject_data = [
            {"code": "CS101", "name": "Introduction to Programming", "units": 3, "required_specialization": "Web Development"},
            {"code": "CS201", "name": "Data Structures", "units": 4, "required_specialization": "Databases"},
            {"code": "CS301", "name": "Machine Learning", "units": 4, "required_specialization": "Machine Learning"},
            {"code": "CS401", "name": "Advanced Algorithms", "units": 3, "required_specialization": "Data Science"},
            {"code": "CS501", "name": "Database Design", "units": 3, "required_specialization": "Databases"},
        ]
        
        subject_objs = []
        for sdata in subject_data:
            subj = Subject(
                code=sdata["code"],
                name=sdata["name"],
                units=sdata["units"],
                required_specialization=sdata["required_specialization"],
                active=True
            )
            db.add(subj)
            subject_objs.append(subj)
        
        db.commit()
        
        # Create sections
        section_configs = [
            {"subject": 0, "section": "A", "day": 0, "start": "08:00", "end": "10:00", "room": "101"},
            {"subject": 0, "section": "B", "day": 2, "start": "14:00", "end": "16:00", "room": "102"},
            {"subject": 1, "section": "A", "day": 1, "start": "09:00", "end": "11:00", "room": "201"},
            {"subject": 2, "section": "A", "day": 0, "start": "10:00", "end": "12:00", "room": "301"},
            {"subject": 3, "section": "A", "day": 3, "start": "14:00", "end": "17:00", "room": "401"},
            {"subject": 4, "section": "A", "day": 2, "start": "18:00", "end": "20:00", "room": "501"},
        ]
        
        for sconfig in section_configs:
            sec = Section(
                subject_id=subject_objs[sconfig["subject"]].id,
                section_code=f"{subject_objs[sconfig['subject']].code}-{sconfig['section']}",
                semester="Fall2024",
                schedule_day=sconfig["day"],
                schedule_start_time=sconfig["start"],
                schedule_end_time=sconfig["end"],
                room=sconfig["room"],
                enrollment=30,
                assigned=False
            )
            db.add(sec)
        
        db.commit()
        
        print("✓ Demo data seeded successfully!")
        print(f"  - {len(faculty_objs)} faculty members")
        print(f"  - {len(subject_objs)} subjects")
        print(f"  - {len(section_configs)} sections")
        
    except Exception as e:
        print(f"✗ Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    seed_demo_data()
