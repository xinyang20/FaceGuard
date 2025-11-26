"""
System configuration API endpoints.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from core.config_manager import ConfigManager

router = APIRouter()


class ConfigResponse(BaseModel):
    """Response model for configuration."""
    frame_interval_ms: int
    recognition_threshold: float


class ConfigUpdateRequest(BaseModel):
    """Request model for updating configuration."""
    frame_interval_ms: int | None = None
    recognition_threshold: float | None = None


@router.get("/api/config", response_model=ConfigResponse)
async def get_config(db: Session = Depends(get_db)):
    """
    Get current system configuration.
    """
    config = ConfigManager.get_config(db)
    
    return ConfigResponse(
        frame_interval_ms=config.get("frame_interval_ms", 500),
        recognition_threshold=config.get("recognition_threshold", 0.5)
    )


@router.put("/api/config")
async def update_config(
    request: ConfigUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update system configuration.
    
    Args:
        request: Configuration updates
    """
    # Build update dictionary (only include non-None values)
    updates = {}
    
    if request.frame_interval_ms is not None:
        if request.frame_interval_ms < 100:
            raise HTTPException(
                status_code=400,
                detail="frame_interval_ms must be at least 100ms"
            )
        updates["frame_interval_ms"] = request.frame_interval_ms
    
    if request.recognition_threshold is not None:
        if not (0.0 <= request.recognition_threshold <= 1.0):
            raise HTTPException(
                status_code=400,
                detail="recognition_threshold must be between 0.0 and 1.0"
            )
        updates["recognition_threshold"] = request.recognition_threshold
    
    if not updates:
        raise HTTPException(status_code=400, detail="No valid updates provided")
    
    # Update configuration
    ConfigManager.update_config(db, updates)
    
    return {"detail": "Configuration updated"}
