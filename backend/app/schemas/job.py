from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

class JobBase(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    salary: Optional[str] = None
    type: Optional[str] = None
    job_url: Optional[str] = None

class JobCreate(JobBase):
    deadline: Optional[date] = None
    created_by: Optional[int] = None

class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    salary: Optional[str] = None
    type: Optional[str] = None
    deadline: Optional[date] = None
    status: Optional[str] = None

class JobResponse(JobBase):
    id: int
    deadline: Optional[date] = None
    is_active: bool
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    applicants: Optional[int] = None
    
    class Config:
        from_attributes = True

class JobApplicationBase(BaseModel):
    job_id: int
    user_id: int
    cover_letter: Optional[str] = None

class JobApplicationCreate(JobApplicationBase):
    pass

class JobApplicationUpdate(BaseModel):
    status: Optional[str] = None

class JobApplicationResponse(JobApplicationBase):
    id: int
    status: str
    applied_at: datetime
    
    class Config:
        from_attributes = True
