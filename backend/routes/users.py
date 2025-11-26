"""
User management API endpoints.
"""
import os
import json
from typing import List
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
from PIL import Image
import io
import numpy as np

from database import get_db, User
from core.face_engine import get_face_engine
from utils.image_utils import save_image
from utils.file_utils import generate_unique_filename

router = APIRouter()


class UserResponse(BaseModel):
    """Response model for user."""
    id: int
    name: str
    avatar_path: str
    
    class Config:
        from_attributes = True


@router.post("/api/users", response_model=UserResponse)
async def create_user(
    name: str = Form(...),
    photo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Register a new user with facial photo.
    
    Args:
        name: User's name
        photo: User's facial photo
    """
    # Get face engine
    engine = get_face_engine()
    
    # Load image
    try:
        contents = await photo.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {str(e)}")
    
    # Extract face features
    try:
        # Detect face
        boxes = engine.detect_faces(image)
        if not boxes:
            raise HTTPException(status_code=400, detail="No face detected in photo")
        
        # Use largest face
        from utils.image_utils import crop_face
        largest_box = max(boxes, key=lambda b: b[2] * b[3])
        face_img = crop_face(image, largest_box)
        
        # Extract features
        feature_vector = engine.extract_features(face_img)
        
    except RuntimeError as e:
        # Model not loaded
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Feature extraction failed: {str(e)}")
    
    # Save avatar
    try:
        avatar_filename = generate_unique_filename(prefix=f"user_{name}", extension="jpg")
        avatar_path = f"static/avatars/{avatar_filename}"
        save_image(image, avatar_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save avatar: {str(e)}")
    
    # Create user in database
    try:
        # Serialize feature vector to JSON
        feature_json = json.dumps(feature_vector.tolist())
        
        new_user = User(
            name=name,
            feature_vector=feature_json,
            avatar_path=avatar_path,
            created_at=datetime.utcnow()
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Add to in-memory database
        engine.add_user_to_database(new_user.id, feature_vector)
        
        return UserResponse(
            id=new_user.id,
            name=new_user.name,
            avatar_path=new_user.avatar_path
        )
    except Exception as e:
        db.rollback()
        # Clean up avatar file
        if os.path.exists(avatar_path):
            os.remove(avatar_path)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/api/users", response_model=List[UserResponse])
async def list_users(db: Session = Depends(get_db)):
    """
    Get list of all registered users.
    """
    users = db.query(User).all()
    return [UserResponse(id=u.id, name=u.name, avatar_path=u.avatar_path) for u in users]


@router.delete("/api/users/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Delete a user and their stored data.
    
    Args:
        user_id: ID of user to delete
    """
    # Find user
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete avatar file
    try:
        if os.path.exists(user.avatar_path):
            os.remove(user.avatar_path)
    except Exception as e:
        print(f"⚠ Failed to delete avatar: {e}")
    
    # Delete from database
    db.delete(user)
    db.commit()
    
    # Remove from in-memory database
    engine = get_face_engine()
    engine.remove_user_from_database(user_id)
    
    return {"detail": "User deleted successfully"}
