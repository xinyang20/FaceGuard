"""
Image processing utilities for face recognition system.
"""
import base64
import io
from typing import Tuple, List
from PIL import Image
import numpy as np


def decode_base64_image(base64_string: str) -> Image.Image:
    """
    Decode base64 string to PIL Image.
    
    Args:
        base64_string: Base64 encoded image string
        
    Returns:
        PIL Image object
    """
    # Remove data URL prefix if present
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]
    
    image_data = base64.b64decode(base64_string)
    image = Image.open(io.BytesIO(image_data))
    return image.convert("RGB")


def save_image(image: Image.Image, filepath: str) -> None:
    """
    Save PIL Image to file.
    
    Args:
        image: PIL Image object
        filepath: Destination file path
    """
    image.save(filepath, format="JPEG", quality=95)


def load_image(filepath: str) -> Image.Image:
    """
    Load image from file path.
    
    Args:
        filepath: Path to image file
        
    Returns:
        PIL Image object in RGB mode
    """
    image = Image.open(filepath)
    return image.convert("RGB")


def crop_face(image: Image.Image, box: List[float]) -> Image.Image:
    """
    Crop face region from image given bounding box.
    
    Args:
        image: PIL Image object
        box: Bounding box [x, y, width, height]
        
    Returns:
        Cropped PIL Image of face region
    """
    x, y, w, h = box
    # Convert to (left, top, right, bottom) format for PIL
    left = int(x)
    top = int(y)
    right = int(x + w)
    bottom = int(y + h)
    
    # Ensure coordinates are within image bounds
    left = max(0, left)
    top = max(0, top)
    right = min(image.width, right)
    bottom = min(image.height, bottom)
    
    return image.crop((left, top, right, bottom))


def pil_to_numpy(image: Image.Image) -> np.ndarray:
    """
    Convert PIL Image to numpy array.
    
    Args:
        image: PIL Image object
        
    Returns:
        Numpy array in RGB format (H, W, C)
    """
    return np.array(image)


def numpy_to_pil(array: np.ndarray) -> Image.Image:
    """
    Convert numpy array to PIL Image.
    
    Args:
        array: Numpy array (H, W, C)
        
    Returns:
        PIL Image object
    """
    return Image.fromarray(array.astype('uint8'), 'RGB')
