from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.session import get_db
from app.models.event import Event, EventRegistration
from app.models.notification import Notification, NotificationType
from app.models.user import User
from app.core.config import settings
import smtplib
import ssl
from email.message import EmailMessage
from app.schemas.event import EventCreate, EventResponse, EventUpdate

router = APIRouter()

@router.post("/", response_model=EventResponse)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    db_event = Event(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

@router.get("/", response_model=List[EventResponse])
def get_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    events = db.query(Event).offset(skip).limit(limit).all()
    return events

@router.get("/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    return db_event

@router.put("/{event_id}", response_model=EventResponse)
def update_event(event_id: int, event_update: EventUpdate, db: Session = Depends(get_db)):
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    update_data = event_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_event, key, value)
    
    db.commit()
    db.refresh(db_event)
    try:
        if update_data.get('is_active') is not None:
            pass
        if update_data.get('event_time') or update_data.get('event_date'):
            pass
        if update_data.get('title'):
            pass
        # If marked completed, notify registrants
        if update_data.get('is_active') is False or (hasattr(db_event, 'is_active') and db_event.is_active is False) or (hasattr(db_event, 'status') and getattr(db_event, 'status', None) == 'Completed'):
            regs = db.query(EventRegistration).filter(EventRegistration.event_id == event_id).all()
            for r in regs:
                n = Notification(user_id=r.user_id, title='Event Completed', message=f"{getattr(db_event,'title','Event')} has been marked as completed.", notification_type=NotificationType.EVENT_REMINDER, related_id=event_id, related_type='event')
                db.add(n)
            db.commit()
            # Attempt email
            _send_email_bulk(db, regs, f"Event Completed: {getattr(db_event,'title','Event')}")
    except Exception:
        pass
    return db_event

@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    db.delete(db_event)
    db.commit()
    return {"message": "Event deleted successfully"}

@router.get("/{event_id}/registrations")
def get_event_registrations(event_id: int, db: Session = Depends(get_db)):
    regs = db.query(EventRegistration, User).join(User, User.id == EventRegistration.user_id).filter(EventRegistration.event_id == event_id).all()
    return [{
        'id': er.EventRegistration.id,
        'user_id': er.EventRegistration.user_id,
        'registered_at': None,
        'first_name': u.first_name,
        'last_name': u.last_name,
        'email': u.email,
    } for er, u in regs]

@router.post("/{event_id}/reminders")
def send_event_reminders(event_id: int, db: Session = Depends(get_db)):
    ev = db.query(Event).filter(Event.id == event_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    regs = db.query(EventRegistration, User).join(User, User.id == EventRegistration.user_id).filter(EventRegistration.event_id == event_id).all()
    msg = f"Reminder: {getattr(ev,'title','Event')} at {getattr(ev,'location','')} on {getattr(ev,'event_date', '')} {getattr(ev,'event_time','')}"
    for er, u in regs:
        n = Notification(user_id=u.id, title='Event Reminder', message=msg, notification_type=NotificationType.EVENT_REMINDER, related_id=event_id, related_type='event')
        db.add(n)
    db.commit()
    try:
        _send_email_bulk(db, [ (er.EventRegistration, u) for er,u in regs ], 'Event Reminder', msg)
    except Exception:
        pass
    return { 'success': True, 'count': len(regs) }

def _send_email_bulk(db: Session, regs, subject: str, body: str = None):
    host = settings.SMTP_HOST
    user = settings.SMTP_USER
    pwd = settings.SMTP_PASS
    from_addr = settings.SMTP_FROM or user
    port = settings.SMTP_PORT or 587
    if not host or not user or not pwd:
        return False
    try:
        use_ssl = (port == 465)
        if use_ssl:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(host, port, context=context)
        else:
            server = smtplib.SMTP(host, port)
            server.ehlo(); server.starttls()
        server.login(user, pwd)
        for _, u in regs:
            if not u.email:
                continue
            msg = EmailMessage()
            msg['From'] = from_addr
            msg['To'] = u.email
            msg['Subject'] = subject
            msg.set_content(body or subject)
            try:
                server.send_message(msg)
            except Exception:
                continue
        server.quit()
        return True
    except Exception:
        return False
