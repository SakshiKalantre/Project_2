from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
from pathlib import Path

from app.db.session import get_db
from app.models.resume import Resume
from app.models.certificate import Certificate
from app.schemas.file import ResumeResponse, ResumeUpdate, CertificateResponse, CertificateUpdate
from app.core.config import settings
import boto3
from botocore.config import Config
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
    public_url = upload_to_r2("resumes", file, user_id)
    
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
    public_url = upload_to_r2("certificates", file, user_id)
    
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
        out.append({"id": r.id, "file_type": "resume", "filename": r.filename, "file_url": r.file_url})
    for c in certs:
        out.append({"id": c.id, "file_type": "certificate", "title": c.title, "file_url": c.file_url})
    # newest first
    out.sort(key=lambda x: x.get('uploaded_at', 0), reverse=True)
    return out
