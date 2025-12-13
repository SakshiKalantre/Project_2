from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ResumeUpdate(BaseModel):
    is_primary: Optional[bool] = None
    is_verified: Optional[bool] = None

class ResumeResponse(BaseModel):
    id: int
    user_id: int
    filename: str
    file_url: str
    is_primary: bool
    is_verified: bool
    uploaded_at: datetime
    
    class Config:
        from_attributes = True

class CertificateUpdate(BaseModel):
    title: Optional[str] = None
    issuer: Optional[str] = None
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    credential_url: Optional[str] = None
    description: Optional[str] = None

class CertificateResponse(BaseModel):
    id: int
    user_id: int
    title: str
    issuer: str
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    credential_url: Optional[str] = None
    description: Optional[str] = None
    file_url: Optional[str] = None
    is_verified: bool
    uploaded_at: datetime
    
    class Config:
        from_attributes = True
