import uuid
from typing import Optional
from fastapi import UploadFile
import cloudinary
import cloudinary.uploader
from app.core.config import settings


def _ensure_config():
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )


def upload_to_cloudinary(file: UploadFile, user_id: int, file_kind: str) -> Optional[dict]:
    """Upload a file to Cloudinary and return dict with url and public_id.

    file_kind: 'resume' | 'certificate'
    """
    _ensure_config()

    public_id = f"prepsphere/user_{user_id}/{file_kind}/{uuid.uuid4()}"
    content_type = file.content_type or "application/octet-stream"

    # Choose resource type
    resource_type = "image" if content_type.startswith("image/") else "raw"

    try:
        # file.file is a SpooledTemporaryFile; Cloudinary can accept file-like objects
        result = cloudinary.uploader.upload(
            file.file,
            resource_type=resource_type,
            folder=settings.CLOUDINARY_FOLDER,
            public_id=public_id,
            overwrite=False,
            use_filename=True,
            unique_filename=True,
        )
        return {
            "url": result.get("secure_url") or result.get("url"),
            "public_id": result.get("public_id"),
            "resource_type": result.get("resource_type"),
        }
    except Exception:
        return None
