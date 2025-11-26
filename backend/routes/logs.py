"""
Access logs API endpoint.
"""
from typing import List
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db, AccessLog

router = APIRouter()


class LogItem(BaseModel):
    """Response model for a single log entry."""
    id: int
    user_id: int | None
    user_name: str
    status: str
    confidence: float | None
    snapshot_path: str | None
    timestamp: datetime
    
    class Config:
        from_attributes = True


class LogsResponse(BaseModel):
    """Response model for paginated logs."""
    total: int
    page: int
    size: int
    items: List[LogItem]


@router.get("/api/logs", response_model=LogsResponse)
async def get_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get paginated access logs.
    
    Args:
        page: Page number (1-indexed)
        size: Number of items per page
    """
    # Calculate offset
    offset = (page - 1) * size
    
    # Get total count
    total = db.query(AccessLog).count()
    
    # Get paginated logs (ordered by timestamp descending)
    logs = db.query(AccessLog)\
        .order_by(AccessLog.timestamp.desc())\
        .offset(offset)\
        .limit(size)\
        .all()
    
    # Convert to response model
    items = [
        LogItem(
            id=log.id,
            user_id=log.user_id,
            user_name=log.user_name,
            status=log.status,
            confidence=log.confidence,
            snapshot_path=log.snapshot_path,
            timestamp=log.timestamp
        )
        for log in logs
    ]
    
    return LogsResponse(
        total=total,
        page=page,
        size=size,
        items=items
    )
