from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os
import smtplib
import ssl
from email.message import EmailMessage
import json
import urllib.request

from app.db.session import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationCreate, NotificationResponse, NotificationUpdate
from app.core.config import settings

router = APIRouter()

@router.post("/", response_model=NotificationResponse)
def create_notification(notification: NotificationCreate, db: Session = Depends(get_db)):
    data = notification.dict()
    db_notification = Notification(user_id=data.get('user_id'), title=data.get('title'), message=data.get('message'))
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    try:
        user = db.query(User).filter(User.id == data.get('user_id')).first()
        if user:
            _send_email(user.email, data.get('title') or 'Message from TPO', data.get('message') or '')
    except Exception as e:
        print(f"Send after create failed: {e}")
    return db_notification

@router.post("/send-email")
def send_email_direct(email: str, subject: str, message: str):
    ok = _send_email(email, subject, message)
    return {"email_sent": ok}

@router.get("/by-user/{user_id}", response_model=List[NotificationResponse])
def get_notifications_by_user(user_id: int, db: Session = Depends(get_db)):
    notifications = db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).all()
    return notifications

@router.put("/read-all/{user_id}")
def mark_all_read(user_id: int, db: Session = Depends(get_db)):
    try:
        db.query(Notification).filter(Notification.user_id == user_id, Notification.is_read == False).update({ Notification.is_read: True }, synchronize_session=False)
        db.commit()
        return { "success": True }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark all read: {e}")

@router.get("/", response_model=List[NotificationResponse])
def get_notifications(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    notifications = db.query(Notification).offset(skip).limit(limit).all()
    return notifications

@router.get("/{notification_id}", response_model=NotificationResponse)
def get_notification(notification_id: int, db: Session = Depends(get_db)):
    db_notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not db_notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return db_notification

@router.put("/{notification_id}", response_model=NotificationResponse)
def update_notification(notification_id: int, notification_update: NotificationUpdate, db: Session = Depends(get_db)):
    db_notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not db_notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    update_data = notification_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_notification, key, value)
    
    db.commit()
    db.refresh(db_notification)
    return db_notification

@router.delete("/{notification_id}")
def delete_notification(notification_id: int, db: Session = Depends(get_db)):
    db_notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not db_notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(db_notification)
    db.commit()
    return {"message": "Notification deleted successfully"}
def _send_resend(to_email: str, subject: str, body: str) -> bool:
    api_key = settings.RESEND_API_KEY or os.getenv('RESEND_API_KEY', '')
    from_addr = settings.RESEND_FROM or os.getenv('RESEND_FROM', '') or (settings.SMTP_FROM or os.getenv('SMTP_FROM', ''))
    if not api_key or not from_addr:
        return False
    try:
        data = json.dumps({
            "from": from_addr,
            "to": to_email,
            "subject": subject or 'Message from TPO',
            "html": f"<p>{body or ''}</p>"
        }).encode('utf-8')
        req = urllib.request.Request('https://api.resend.com/emails', data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        req.add_header('Authorization', f'Bearer {api_key}')
        with urllib.request.urlopen(req) as resp:
            return 200 <= resp.getcode() < 300
    except Exception as e:
        print(f"Resend send failed: {e}")
        return False

def _send_email(to_email: str, subject: str, body: str) -> bool:
    host = settings.SMTP_HOST or os.getenv('SMTP_HOST', '')
    user = settings.SMTP_USER or os.getenv('SMTP_USER', '')
    pwd = settings.SMTP_PASS or os.getenv('SMTP_PASS', '')
    from_addr = settings.SMTP_FROM or os.getenv('SMTP_FROM', '') or user
    try:
        port = int(settings.SMTP_PORT or int(os.getenv('SMTP_PORT', '587')))
    except Exception:
        port = 587
    if not host or not user or not pwd or not to_email:
        return False
    try:
        msg = EmailMessage()
        msg['From'] = from_addr
        msg['To'] = to_email
        msg['Subject'] = subject or 'Message from TPO'
        msg.set_content(body or '')
        if port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=context) as server:
                server.login(user, pwd)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port) as server:
                server.ehlo()
                server.starttls()
                server.login(user, pwd)
                server.send_message(msg)
        return True
    except Exception as e:
        # Log only; do not raise to keep API success
        print(f"Email send failed: {e}")
        # Fallback to Resend if configured
        return _send_resend(to_email, subject, body)
