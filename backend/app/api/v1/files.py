from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
from pathlib import Path

from app.db.session import get_db
from app.models.resume import Resume
from app.models.user import User
from app.models.notification import Notification
from app.core.config import settings
import smtplib, ssl
from email.message import EmailMessage
from app.models.certificate import Certificate
from app.schemas.file import ResumeResponse, ResumeUpdate, CertificateResponse, CertificateUpdate
from app.core.config import settings
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from urllib.parse import urlparse

router = APIRouter()

def get_s3():
    if not settings.R2_ENDPOINT or not settings.R2_ACCESS_KEY_ID or not settings.R2_SECRET_ACCESS_KEY or not settings.R2_BUCKET_NAME:
        raise HTTPException(status_code=500, detail="Object storage not configured")
    return boto3.client(
        "s3",
        endpoint_url=settings.R2_ENDPOINT,
        region_name="auto",
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4")
    )

def upload_to_r2(prefix: str, upload_file: UploadFile, user_id: int) -> str:
    s3 = get_s3()
    ext = os.path.splitext(upload_file.filename or "")[1]
    key = f"{prefix}/{user_id}/{uuid.uuid4()}{ext}"
    try:
        upload_file.file.seek(0)
        s3.upload_fileobj(upload_file.file, settings.R2_BUCKET_NAME, key, ExtraArgs={"ContentType": upload_file.content_type or "application/octet-stream"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload to storage: {e}")
    if not settings.R2_PUBLIC_BASE_URL:
        # If no public base URL configured, return S3-style URL
        return f"{settings.R2_ENDPOINT.rstrip('/')}/{settings.R2_BUCKET_NAME}/{key}"
    return f"{settings.R2_PUBLIC_BASE_URL.rstrip('/')}/{key}"

@router.post("/resumes", response_model=ResumeResponse)
async def upload_resume(
    user_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Server enforces type only; size handled by storage limits
    
    # Validate file type
    allowed_types = ["application/pdf", "image/jpeg", "image/png"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # Generate unique filename
    # Upload to Cloudflare R2
    public_url = upload_to_r2("resume", file, user_id)
    
    # Create resume record
    db_resume = Resume(
        user_id=user_id,
        filename=file.filename,
        file_url=public_url,
        is_primary=False,
        is_verified=False
    )
    db.add(db_resume)
    db.commit()
    db.refresh(db_resume)
    return db_resume

@router.post("/certificates", response_model=CertificateResponse)
async def upload_certificate(
    user_id: int = Form(...),
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Server enforces type only; size handled by storage limits
    
    # Validate file type
    allowed_types = ["application/pdf", "image/jpeg", "image/png"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # Generate unique filename
    # Upload to Cloudflare R2
    public_url = upload_to_r2("certificate", file, user_id)
    
    # Create certificate record
    db_certificate = Certificate(
        user_id=user_id,
        title=title,
        issuer="",
        file_url=public_url,
        is_verified=False
    )
    db.add(db_certificate)
    db.commit()
    db.refresh(db_certificate)
    return db_certificate

@router.get("/resumes/{resume_id}", response_model=ResumeResponse)
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    db_resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not db_resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return db_resume

@router.put("/resumes/{resume_id}", response_model=ResumeResponse)
def update_resume(resume_id: int, resume_update: ResumeUpdate, db: Session = Depends(get_db)):
    db_resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not db_resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    update_data = resume_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_resume, key, value)
    
    db.commit()
    db.refresh(db_resume)
    return db_resume

@router.delete("/resumes/{resume_id}")
def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    db_resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not db_resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # Delete file from storage
    try:
        if hasattr(db_resume, "file_url") and db_resume.file_url:
            # delete from R2
            base = settings.R2_PUBLIC_BASE_URL.rstrip('/') if settings.R2_PUBLIC_BASE_URL else f"{settings.R2_ENDPOINT.rstrip('/')}/{settings.R2_BUCKET_NAME}"
            prefix = base.rstrip('/') + '/'
            if db_resume.file_url.startswith(prefix):
                key = db_resume.file_url[len(prefix):]
                s3 = get_s3()
                s3.delete_object(Bucket=settings.R2_BUCKET_NAME, Key=key)
    except Exception:
        pass  # Log this in a real application
    
    db.delete(db_resume)
    db.commit()
    return {"message": "Resume deleted successfully"}

@router.get("/certificates/{certificate_id}", response_model=CertificateResponse)
def get_certificate(certificate_id: int, db: Session = Depends(get_db)):
    db_certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not db_certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return db_certificate

@router.put("/certificates/{certificate_id}", response_model=CertificateResponse)
def update_certificate(certificate_id: int, certificate_update: CertificateUpdate, db: Session = Depends(get_db)):
    db_certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not db_certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    update_data = certificate_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_certificate, key, value)
    
    db.commit()
    db.refresh(db_certificate)
    return db_certificate

@router.delete("/certificates/{certificate_id}")
def delete_certificate(certificate_id: int, db: Session = Depends(get_db)):
    db_certificate = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if not db_certificate:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    # Delete file from storage
    try:
        if hasattr(db_certificate, "file_url") and db_certificate.file_url:
            base = settings.R2_PUBLIC_BASE_URL.rstrip('/') if settings.R2_PUBLIC_BASE_URL else f"{settings.R2_ENDPOINT.rstrip('/')}/{settings.R2_BUCKET_NAME}"
            prefix = base.rstrip('/') + '/'
            if db_certificate.file_url.startswith(prefix):
                key = db_certificate.file_url[len(prefix):]
                s3 = get_s3()
                s3.delete_object(Bucket=settings.R2_BUCKET_NAME, Key=key)
    except Exception:
        pass  # Log this in a real application
    
    db.delete(db_certificate)
    db.commit()
    return {"message": "Certificate deleted successfully"}

def _key_from_url(file_url: str) -> str:
    parsed = urlparse(file_url)
    # Paths can be /bucket/key or just /key depending on base URL used
    path = parsed.path.lstrip('/')
    parts = path.split('/')
    if parts and parts[0] == settings.R2_BUCKET_NAME and len(parts) > 1:
        return '/'.join(parts[1:])
    return path

def _exists_in_r2(file_url: str) -> bool:
    # If storage is not configured, assume files exist (do not purge DB rows)
    if not settings.R2_ENDPOINT or not settings.R2_BUCKET_NAME:
        return True
    try:
        s3 = get_s3()
        key = _key_from_url(file_url)
        s3.head_object(Bucket=settings.R2_BUCKET_NAME, Key=key)
        return True
    except ClientError as e:
        try:
            code = e.response.get('Error', {}).get('Code')
            # Only treat NotFound as missing; for auth or other errors, assume present
            return code != 'NotFound' and code != '404'
        except Exception:
            return True
    except Exception:
        return False

@router.get("/{file_id}")
def get_file_info(file_id: int, db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == file_id).first()
    if resume:
        return {"id": resume.id, "file_type": "resume", "filename": resume.filename, "file_url": resume.file_url}
    cert = db.query(Certificate).filter(Certificate.id == file_id).first()
    if cert:
        return {"id": cert.id, "file_type": "certificate", "title": cert.title, "file_url": cert.file_url}
    raise HTTPException(status_code=404, detail="File not found")

@router.get("/{file_id}/presigned")
def get_presigned(file_id: int, db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == file_id).first()
    target_url = resume.file_url if resume else None
    if not target_url:
        cert = db.query(Certificate).filter(Certificate.id == file_id).first()
        target_url = cert.file_url if cert else None
    if not target_url:
        raise HTTPException(status_code=404, detail="File not found")
    key = _key_from_url(target_url)
    s3 = get_s3()
    try:
        url = s3.generate_presigned_url('get_object', Params={'Bucket': settings.R2_BUCKET_NAME, 'Key': key}, ExpiresIn=300)
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate presigned URL: {e}")

@router.get("/by-user/{user_id}")
def list_files_by_user(user_id: int, db: Session = Depends(get_db)):
    resumes = db.query(Resume).filter(Resume.user_id == user_id).all()
    certs = db.query(Certificate).filter(Certificate.user_id == user_id).all()
    out: List[dict] = []
    for r in resumes:
        if not r.file_url:
            continue
        exists = _exists_in_r2(r.file_url)
        if exists:
            out.append({"id": r.id, "file_type": "resume", "filename": r.filename, "file_url": r.file_url, "uploaded_at": getattr(r, 'uploaded_at', None)})
        # Do not delete DB records during listing; storage availability may be transient
    for c in certs:
        if not c.file_url:
            continue
        exists = _exists_in_r2(c.file_url)
        if exists:
            out.append({"id": c.id, "file_type": "certificate", "title": c.title, "file_url": c.file_url, "uploaded_at": getattr(c, 'uploaded_at', None)})
        # Do not delete DB records during listing; storage availability may be transient
    db.commit()
    out.sort(key=lambda x: x.get('uploaded_at', 0), reverse=True)
    return out

# TPO views for resumes
@router.get("/tpo/pending-resumes")
def tpo_pending_resumes(db: Session = Depends(get_db)):
    rows = (
        db.query(Resume)
        .filter(Resume.is_verified == False)
        .all()
    )
    out = []
    for r in rows:
        # join user lazily to include name/email
        u = getattr(r, 'user', None)
        out.append({
            "id": r.id,
            "user_id": r.user_id,
            "first_name": getattr(u, 'first_name', None),
            "last_name": getattr(u, 'last_name', None),
            "email": getattr(u, 'email', None),
            "file_name": r.filename,
            "file_url": r.file_url,
            "is_verified": r.is_verified,
            "uploaded_at": getattr(r, 'uploaded_at', None),
        })
    return out

@router.get("/tpo/verified-resumes")
def tpo_verified_resumes(db: Session = Depends(get_db)):
    rows = (
        db.query(Resume)
        .filter(Resume.is_verified == True)
        .all()
    )
    out = []
    for r in rows:
        u = getattr(r, 'user', None)
        out.append({
            "id": r.id,
            "user_id": r.user_id,
            "first_name": getattr(u, 'first_name', None),
            "last_name": getattr(u, 'last_name', None),
            "email": getattr(u, 'email', None),
            "file_name": r.filename,
            "file_url": r.file_url,
            "is_verified": r.is_verified,
            "uploaded_at": getattr(r, 'uploaded_at', None),
        })
    return out

@router.put("/resumes/{resume_id}/verify")
def verify_resume(resume_id: int, db: Session = Depends(get_db)):
    r = db.query(Resume).filter(Resume.id == resume_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Resume not found")
    r.is_verified = True
    db.commit()
    db.refresh(r)
    return {"id": r.id, "is_verified": True}

@router.put("/resumes/{resume_id}/reject")
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
        msg['Subject'] = subject or 'Resume Rejected'
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
        print(f"Email send failed (files.reject): {e}")
        return False

def reject_resume(resume_id: int, reason: dict | None = None, db: Session = Depends(get_db)):
    r = db.query(Resume).filter(Resume.id == resume_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Resume not found")
    r.is_verified = False
    db.commit()
    db.refresh(r)
    email_sent = False
    try:
        user = db.query(User).filter(User.id == r.user_id).first()
        note = Notification(user_id=r.user_id, title='Resume Rejected', message=(reason or {}).get('reason') or 'Your resume was rejected')
        db.add(note); db.commit(); db.refresh(note)
        if user:
            email_sent = _send_email(user.email, 'Resume Rejected', note.message)
    except Exception as e:
        print(f"Reject resume notify failed: {e}")
    return {"id": r.id, "is_verified": False, "email_sent": email_sent}
