from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.db.session import get_db
from app.models.user import User, Profile
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
        db.commit()
        db.refresh(db_profile)
        return db_profile
    db_profile = Profile(user_id=user_id, **profile.dict())
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
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
    
    db.commit()
    db.refresh(db_profile)
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
