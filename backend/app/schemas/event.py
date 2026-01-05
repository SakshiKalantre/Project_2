from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EventBase(BaseModel):
    title: str
    description: str
    location: str
    event_date: datetime
    event_time: str
    status: Optional[str] = None
    form_url: Optional[str] = None
    template_url: Optional[str] = None
    category: Optional[str] = None

class EventCreate(EventBase):
    created_by: int

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    event_date: Optional[datetime] = None
    event_time: Optional[str] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None
    form_url: Optional[str] = None
    template_url: Optional[str] = None
    category: Optional[str] = None

class EventResponse(EventBase):
    id: int
    status: Optional[str] = None
    is_active: bool
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class EventRegisterRequest(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    clerkUserId: Optional[str] = None
