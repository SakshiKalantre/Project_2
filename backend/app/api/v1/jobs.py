from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import func

from app.db.session import get_db
from app.models.job import Job, JobApplication
from app.schemas.job import JobCreate, JobResponse, JobUpdate, JobApplicationCreate, JobApplicationResponse, JobApplicationUpdate

router = APIRouter()
tpo_router = APIRouter()

@router.post("/", response_model=JobResponse)
def create_job(job: JobCreate, db: Session = Depends(get_db)):
    db_job = Job(**job.dict())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    cnt = db.query(func.count(JobApplication.id)).filter(JobApplication.job_id == db_job.id).scalar() or 0
    return JobResponse(
        id=db_job.id,
        title=db_job.title,
        company=db_job.company,
        location=db_job.location,
        description=db_job.description,
        requirements=db_job.requirements,
        salary=db_job.salary,
        type=getattr(db_job, 'type', None),
        job_url=getattr(db_job, 'job_url', None),
        deadline=getattr(db_job, 'deadline', None),
        is_active=(str(getattr(db_job, 'status', 'Active')).lower() != 'closed'),
        created_by=getattr(db_job, 'created_by', None),
        created_at=getattr(db_job, 'posted', None),
        updated_at=getattr(db_job, 'updated_at', None),
        applicants=cnt
    )

@router.get("/", response_model=List[JobResponse])
def get_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    rows = db.query(Job).filter(func.lower(Job.status) != 'closed').order_by(Job.posted.desc()).offset(skip).limit(limit).all()
    out: List[JobResponse] = []
    for j in rows:
        cnt = db.query(func.count(JobApplication.id)).filter(JobApplication.job_id == j.id).scalar() or 0
        jd = JobResponse(
            id=j.id,
            title=j.title,
            company=j.company,
            location=j.location,
            description=j.description,
            requirements=j.requirements,
            salary=getattr(j, 'salary', None),
            type=getattr(j, 'type', None),
            job_url=getattr(j, 'job_url', None),
            deadline=getattr(j, 'deadline', None),
            is_active=(str(getattr(j, 'status', 'Active')).lower() != 'closed'),
            created_by=getattr(j, 'created_by', None),
            created_at=getattr(j, 'posted', None),
            updated_at=getattr(j, 'updated_at', None),
            applicants=cnt
        )
        out.append(jd)
    return out

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    cnt = db.query(func.count(JobApplication.id)).filter(JobApplication.job_id == db_job.id).scalar() or 0
    return JobResponse(
        id=db_job.id,
        title=db_job.title,
        company=db_job.company,
        location=db_job.location,
        description=db_job.description,
        requirements=db_job.requirements,
        salary=getattr(db_job, 'salary', None),
        type=getattr(db_job, 'type', None),
        job_url=getattr(db_job, 'job_url', None),
        deadline=getattr(db_job, 'deadline', None),
        is_active=(str(getattr(db_job, 'status', 'Active')).lower() != 'closed'),
        created_by=getattr(db_job, 'created_by', None),
        created_at=getattr(db_job, 'posted', None),
        updated_at=getattr(db_job, 'updated_at', None),
        applicants=cnt
    )

@router.put("/{job_id}", response_model=JobResponse)
def update_job(job_id: int, job_update: JobUpdate, db: Session = Depends(get_db)):
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    update_data = job_update.dict(exclude_unset=True)
    status = update_data.pop('status', None)
    if status:
        db_job.status = status
    for key, value in update_data.items():
        setattr(db_job, key, value)
    
    db.commit()
    db.refresh(db_job)
    cnt = db.query(func.count(JobApplication.id)).filter(JobApplication.job_id == db_job.id).scalar() or 0
    return JobResponse(
        id=db_job.id,
        title=db_job.title,
        company=db_job.company,
        location=db_job.location,
        description=db_job.description,
        requirements=db_job.requirements,
        salary=getattr(db_job, 'salary', None),
        type=getattr(db_job, 'type', None),
        job_url=getattr(db_job, 'job_url', None),
        deadline=getattr(db_job, 'deadline', None),
        is_active=(str(getattr(db_job, 'status', 'Active')).lower() != 'closed'),
        created_by=getattr(db_job, 'created_by', None),
        created_at=getattr(db_job, 'posted', None),
        updated_at=getattr(db_job, 'updated_at', None),
        applicants=cnt
    )

@router.delete("/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    db_job = db.query(Job).filter(Job.id == job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    db.delete(db_job)
    db.commit()
    return {"message": "Job deleted successfully"}

@router.post("/applications", response_model=JobApplicationResponse)
def create_application(application: JobApplicationCreate, db: Session = Depends(get_db)):
    # Check if job exists
    db_job = db.query(Job).filter(Job.id == application.job_id).first()
    if not db_job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check if user exists
    # (In a real app, you would also verify the user exists)
    
    # Create application
    db_application = JobApplication(**application.dict())
    db.add(db_application)
    db.commit()
    db.refresh(db_application)
    return db_application

@router.get("/applications/", response_model=List[JobApplicationResponse])
def get_applications(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    applications = db.query(JobApplication).offset(skip).limit(limit).all()
    return applications

@router.get("/{job_id}/applications", response_model=List[JobApplicationResponse])
def get_applications_by_job(job_id: int, db: Session = Depends(get_db)):
    applications = db.query(JobApplication).filter(JobApplication.job_id == job_id).all()
    return applications

# TPO convenience routes
@router.get("/tpo/jobs", response_model=List[JobResponse])
def tpo_list_jobs(db: Session = Depends(get_db)):
    return get_jobs(0, 100, db)

@router.post("/tpo/jobs", response_model=JobResponse)
def tpo_create_job(job: JobCreate, db: Session = Depends(get_db)):
    return create_job(job, db)

@router.put("/tpo/jobs/{job_id}", response_model=JobResponse)
def tpo_update_job(job_id: int, job_update: JobUpdate, db: Session = Depends(get_db)):
    return update_job(job_id, job_update, db)

@router.get("/tpo/jobs/{job_id}/applications", response_model=List[JobApplicationResponse])
def tpo_get_job_apps(job_id: int, db: Session = Depends(get_db)):
    return get_applications_by_job(job_id, db)

# Top-level TPO router under /api/v1/tpo
@tpo_router.get("/jobs", response_model=List[JobResponse])
def tpo_jobs_list(db: Session = Depends(get_db)):
    return get_jobs(0, 100, db)

@tpo_router.post("/jobs", response_model=JobResponse)
def tpo_jobs_create(job: JobCreate, db: Session = Depends(get_db)):
    return create_job(job, db)

@tpo_router.put("/jobs/{job_id}", response_model=JobResponse)
def tpo_jobs_update(job_id: int, job_update: JobUpdate, db: Session = Depends(get_db)):
    return update_job(job_id, job_update, db)

@tpo_router.get("/jobs/{job_id}/applications", response_model=List[JobApplicationResponse])
def tpo_jobs_get_apps(job_id: int, db: Session = Depends(get_db)):
    return get_applications_by_job(job_id, db)

@router.put("/applications/{application_id}", response_model=JobApplicationResponse)
def update_application(application_id: int, application_update: JobApplicationUpdate, db: Session = Depends(get_db)):
    db_application = db.query(JobApplication).filter(JobApplication.id == application_id).first()
    if not db_application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    update_data = application_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_application, key, value)
    
    db.commit()
    db.refresh(db_application)
    return db_application
