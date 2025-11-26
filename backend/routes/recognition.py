"""
Recognition API endpoint.
"""
import os
import json
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db, User, AccessLog
from core.face_engine import get_face_engine
from core.config_manager import ConfigManager
from utils.image_utils import decode_base64_image, load_image, save_image
from utils.file_utils import generate_unique_filename
from utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


class RecognizeBase64Request(BaseModel):
    """Request model for base64 image recognition."""
    image_base64: str


class RecognizeResponse(BaseModel):
    """Response model for recognition."""
    status: str
    name: Optional[str] = None
    box: Optional[list] = None
    confidence: Optional[float] = None
    snapshot_path: Optional[str] = None


@router.post("/api/recognize", response_model=RecognizeResponse)
async def recognize_face(
    file: Optional[UploadFile] = File(None),
    request: Optional[RecognizeBase64Request] = None,
    db: Session = Depends(get_db)
):
    """
    Recognize face in uploaded image or base64 image.

    Accepts either:
    - Multipart form-data with 'file' field
    - JSON with 'image_base64' field
    """
    logger.info("🔍 Recognition request received")

    # Get face engine and config
    engine = get_face_engine()
    threshold = ConfigManager.get_value(db, "recognition_threshold", 0.5)
    logger.info(f"Using recognition threshold: {threshold}")

    # Load image from file or base64
    try:
        if file:
            # Load from uploaded file
            from PIL import Image
            import io
            logger.info(f"Loading image from file upload: {file.filename}")
            contents = await file.read()
            image = Image.open(io.BytesIO(contents)).convert("RGB")
            logger.info(f"Image loaded: size={image.size}, mode={image.mode}")
        elif request and request.image_base64:
            # Load from base64
            logger.info("Loading image from base64")
            image = decode_base64_image(request.image_base64)
            logger.info(f"Image loaded: size={image.size}, mode={image.mode}")
        else:
            logger.warning("No image provided in request")
            raise HTTPException(status_code=400, detail="No image provided")
    except Exception as e:
        logger.error(f"Failed to load image: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")

    # Perform recognition
    logger.info("Starting face recognition...")
    result = engine.recognize(image, threshold=threshold)
    logger.info(f"Recognition completed: status={result['status']}, confidence={result.get('confidence')}")
    
    # Save snapshot
    snapshot_path = None
    try:
        snapshot_filename = generate_unique_filename(prefix="snapshot", extension="jpg")
        snapshot_path = f"static/logs/{snapshot_filename}"
        save_image(image, snapshot_path)
        logger.info(f"Snapshot saved: {snapshot_path}")
    except Exception as e:
        logger.warning(f"Failed to save snapshot: {e}")

    # Get user name if recognized
    user_name = "Unknown"
    user_id = None

    if result["status"] == "PASS" and result["user_id"]:
        user = db.query(User).filter(User.id == result["user_id"]).first()
        if user:
            user_name = user.name
            user_id = user.id
            logger.info(f"✓ User recognized: {user_name} (ID: {user_id})")
    elif result["status"] == "REJECT":
        logger.info("✗ Unknown person rejected")
    elif result["status"] == "NO_FACE":
        logger.info("⚠ No face detected in image")

    # Create access log
    log_entry = AccessLog(
        user_id=user_id,
        user_name=user_name,
        status=result["status"],
        confidence=result.get("confidence"),
        snapshot_path=snapshot_path,
        timestamp=datetime.utcnow()
    )
    db.add(log_entry)
    db.commit()
    logger.info(f"Access log created: {result['status']}")

    # Return response
    logger.info(f"Recognition complete. Returning response: {result['status']}")
    return RecognizeResponse(
        status=result["status"],
        name=user_name if result["status"] == "PASS" else None,
        box=result.get("box"),
        confidence=result.get("confidence"),
        snapshot_path=snapshot_path
    )
