from fastapi import APIRouter, Depends, HTTPException, status, Body, Query, Request
from typing import Union, Optional
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.db.session import get_db
from app.models.user import User, Profile, UserRole
from app.models.notification import Notification
from app.core.config import settings
import smtplib, ssl
from email.message import EmailMessage
from app.schemas.user import UserCreate, UserResponse, UserUpdate, ProfileCreate, ProfileResponse, ProfileUpdate
from app.core.config import settings

router = APIRouter()

@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    db_user = db.query(User).filter(User.clerk_user_id == user.clerk_user_id).first()
    if db_user:
        raise HTTPException(status_code=400, detail="User already registered")
    
    # Create new user
    db_user = User(
        clerk_user_id=user.clerk_user_id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role,
        phone_number=getattr(user, 'phone_number', None)
    )
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="User with same email or clerk_user_id already exists")
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.get("/clerk/{clerk_user_id}", response_model=UserResponse)
def get_user_by_clerk_id(clerk_user_id: str, db: Session = Depends(get_db)):
    """
    Get user by Clerk user ID
    """
    db_user = db.query(User).filter(User.clerk_user_id == clerk_user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(db_user)
    db.commit()
    return {"message": "User deleted successfully"}

@router.post("/{user_id}/profile", response_model=ProfileResponse)
def create_user_profile(user_id: int, profile: ProfileCreate, db: Session = Depends(get_db)):
    # Check if user exists
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Upsert profile: update if exists, else create
    db_profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if db_profile:
        update_data = profile.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_profile, key, value)
        # Any edit requires re-approval
        db_profile.is_approved = False
        db.commit()
        db.refresh(db_profile)
    else:
        db_profile = Profile(user_id=user_id, **profile.dict())
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)
    # Update user's profile_complete flag based on filled fields
    is_complete = all(
        [
            (db_profile.phone or '').strip() != '',
            (db_profile.degree or '').strip() != '',
            (db_profile.year or '').strip() != '',
            (db_profile.skills or '').strip() != '',
            (db_profile.about or '').strip() != '',
            (db_profile.alternate_email or '').strip() != '',
        ]
    )
    db_user.profile_complete = is_complete
    db.commit()
    db.refresh(db_user)
    return db_profile

@router.get("/{user_id}/profile", response_model=ProfileResponse)
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    db_profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return db_profile

@router.put("/{user_id}/profile", response_model=ProfileResponse)
def update_user_profile(user_id: int, profile_update: ProfileUpdate, db: Session = Depends(get_db)):
    db_profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    update_data = profile_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_profile, key, value)
    # Any edit requires re-approval
    db_profile.is_approved = False
    db.commit()
    db.refresh(db_profile)
    # Update user's profile_complete flag
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        is_complete = all(
            [
                (db_profile.phone or '').strip() != '',
                (db_profile.degree or '').strip() != '',
                (db_profile.year or '').strip() != '',
                (db_profile.skills or '').strip() != '',
                (db_profile.about or '').strip() != '',
                (db_profile.alternate_email or '').strip() != '',
            ]
        )
        db_user.profile_complete = is_complete
        db.commit()
        db.refresh(db_user)
    return db_profile
@router.get("/by-email/{email}", response_model=UserResponse)
def get_user_by_email(email: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        existing = db.query(User).filter((User.email == user.email) | (User.clerk_user_id == user.clerk_user_id)).first()
        if existing:
            return existing
        db_user = User(
            clerk_user_id=user.clerk_user_id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            phone_number=getattr(user, 'phone_number', None)
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="User with same email or clerk_user_id already exists")
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

# TPO Profile Endpoints
@router.get("/tpo/{user_id}/profile", response_model=ProfileResponse)
def get_tpo_profile(user_id: int, db: Session = Depends(get_db)):
    """
    Get TPO profile with alternate email and phone
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not db_profile:
        # Return empty profile if doesn't exist
        return ProfileResponse(
            id=0,
            user_id=user_id,
            phone=None,
            alternate_email=None,
            degree=None,
            year=None,
            skills=None,
            about=None,
            is_approved=False,
            created_at=None,
            updated_at=None
        )
    return db_profile

@router.post("/tpo/{user_id}/profile", response_model=ProfileResponse)
def save_tpo_profile(user_id: int, profile_data: ProfileUpdate, db: Session = Depends(get_db)):
    """
    Save or update TPO profile (alternate email and phone)
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    
    if db_profile:
        # Update existing profile
        update_data = profile_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_profile, key, value)
        db.commit()
        db.refresh(db_profile)
        return db_profile
    else:
        # Create new profile
        db_profile = Profile(
            user_id=user_id,
            phone=profile_data.phone,
            alternate_email=profile_data.alternate_email
        )
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)
        return db_profile

# TPO: Pending profiles (students needing review)
@router.get("/tpo/pending-profiles")
def tpo_pending_profiles(db: Session = Depends(get_db)):
    students = (
        db.query(User, Profile)
        .outerjoin(Profile, Profile.user_id == User.id)
        .filter(User.role == UserRole.STUDENT)
        .all()
    )
    rows = []
    for u, p in students:
        has_profile = p is not None
        profile_is_approved = bool(getattr(p, 'is_approved', False)) if p else False
        user_is_approved = bool(getattr(u, 'is_approved', False))
        if (not has_profile) or (not profile_is_approved) or (not user_is_approved):
            rows.append({
                "user_id": u.id,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "email": u.email,
                "phone": getattr(p, 'phone', None) if p else None,
                "degree": getattr(p, 'degree', None) if p else None,
                "year": getattr(p, 'year', None) if p else None,
                "has_profile": has_profile,
                "profile_is_approved": profile_is_approved,
                "user_is_approved": user_is_approved,
            })
    return rows

# TPO: Approve a student's profile
@router.put("/tpo/profiles/{user_id}/approve")
def tpo_approve_profile(user_id: int, db: Session = Depends(get_db)):
    db_profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    db_profile.is_approved = True
    db.commit()
    db.refresh(db_profile)
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db_user.is_approved = True
        db.commit()
        db.refresh(db_user)
    return { "user_id": user_id, "is_approved": True }

def _send_email(to_email: str, subject: str, body: str) -> bool:
    host = settings.SMTP_HOST
    user = settings.SMTP_USER
    pwd = settings.SMTP_PASS
    from_addr = settings.SMTP_FROM or user
    port = int(getattr(settings, 'SMTP_PORT', 587))
    try:
        msg = EmailMessage()
        msg['From'] = from_addr
        msg['To'] = to_email
        msg['Subject'] = subject or 'Profile Rejected'
        msg.set_content(body or '')
        if port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=context) as server:
                server.login(user, pwd)
                server.send_message(msg)
        else:
            with smtplib.SMTP(host, port) as server:
                server.ehlo(); server.starttls(); server.login(user, pwd); server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email send failed (users.reject): {e}")
        return False

@router.put("/tpo/profiles/{user_id}/reject")
async def tpo_reject_profile(user_id: int, request: Request, reason: Union[str, dict, None] = Body(None), reason_q: Optional[str] = Query(None), db: Session = Depends(get_db)):
    db_profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    db_profile.is_approved = True
    db_profile.is_approved = False
    msg_in = None
    if isinstance(reason, str):
        msg_in = reason
    elif isinstance(reason, dict):
        msg_in = reason.get('reason')
    if not msg_in:
        try:
            payload = await request.json()
            if isinstance(payload, dict):
                msg_in = payload.get('reason')
        except Exception:
            pass
    if msg_in:
        db_profile.approval_notes = msg_in
    elif reason_q:
        db_profile.approval_notes = reason_q
    db.commit()
    db.refresh(db_profile)
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db_user.is_approved = False
        db.commit()
        db.refresh(db_user)
        email_sent = False
        try:
            msg = None
            if isinstance(reason, str):
                msg = reason
            elif isinstance(reason, dict):
                msg = reason.get('reason')
            if not msg:
                try:
                    payload = await request.json()
                    if isinstance(payload, dict):
                        msg = payload.get('reason')
                except Exception:
                    pass
            if not msg:
                msg = reason_q
            note = Notification(user_id=user_id, title='Profile Rejected', message=(msg or 'Your profile was rejected'))
            db.add(note); db.commit(); db.refresh(note)
            email_sent = _send_email(db_user.email, 'Profile Rejected', note.message)
        except Exception as e:
            print(f"Profile reject notify failed: {e}")
        return { "user_id": user_id, "is_approved": False, "email_sent": email_sent }
    return { "user_id": user_id, "is_approved": False }

# TPO: Approved students list
@router.get("/tpo/approved-students")
def tpo_approved_students(db: Session = Depends(get_db)):
    rows_raw = (
        db.query(User, Profile)
        .join(Profile, Profile.user_id == User.id)
        .filter(User.role == UserRole.STUDENT)
        .filter(User.is_approved == True)
        .filter(Profile.is_approved == True)
        .all()
    )
    rows = []
    for u, p in rows_raw:
        rows.append({
            "user_id": u.id,
            "first_name": u.first_name,
            "last_name": u.last_name,
            "email": u.email,
            "degree": p.degree,
            "year": p.year,
        })
    return rows
