"""
File management utilities.
"""
import os
import uuid
from pathlib import Path
from datetime import datetime


def ensure_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        "static/avatars",
        "static/logs",
        "models"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


def generate_unique_filename(prefix: str = "", extension: str = "jpg") -> str:
    """
    Generate a unique filename using timestamp and UUID.
    
    Args:
        prefix: Optional prefix for filename
        extension: File extension (without dot)
        
    Returns:
        Unique filename string
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    
    if prefix:
        return f"{prefix}_{timestamp}_{unique_id}.{extension}"
    else:
        return f"{timestamp}_{unique_id}.{extension}"


def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename.
    
    Args:
        filename: Name of file
        
    Returns:
        File extension (without dot)
    """
    return os.path.splitext(filename)[1].lstrip(".")
