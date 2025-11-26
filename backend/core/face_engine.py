"""
Face recognition engine using ULFD for detection and ArcFace for feature extraction.
"""
import os
import json
from typing import Dict, List, Optional, Tuple
import numpy as np
from PIL import Image
import onnxruntime as ort
from sqlalchemy.orm import Session

from database import User
from utils.image_utils import pil_to_numpy, crop_face


class FaceEngine:
    """
    Face detection and recognition engine.
    Uses ULFD for detection and ArcFace for feature extraction.
    """

    def __init__(self, ulfd_model_path: str = "models/ulfd.onnx",
                 arcface_model_path: str = "models/arcface.onnx"):
        """
        Initialize face recognition engine.

        Args:
            ulfd_model_path: Path to ULFD ONNX model
            arcface_model_path: Path to ArcFace ONNX model
        """
        self.ulfd_model_path = ulfd_model_path
        self.arcface_model_path = arcface_model_path

        # In-memory face database: {user_id: feature_vector}
        self.face_database: Dict[int, np.ndarray] = {}

        # Initialize models (will be loaded when models are available)
        self.ulfd_session = None
        self.arcface_session = None

        self._load_models()
    
    def _load_models(self):
        """Load ONNX models if they exist."""
        try:
            if os.path.exists(self.ulfd_model_path):
                self.ulfd_session = ort.InferenceSession(self.ulfd_model_path)
                print(f"✓ ULFD model loaded from {self.ulfd_model_path}")
            else:
                print(f"⚠ ULFD model not found at {self.ulfd_model_path}")
                print("  Face detection will not work until model is provided.")

            if os.path.exists(self.arcface_model_path):
                self.arcface_session = ort.InferenceSession(self.arcface_model_path)
                print(f"✓ ArcFace model loaded from {self.arcface_model_path}")
            else:
                print(f"⚠ ArcFace model not found at {self.arcface_model_path}")
                print("  Feature extraction will not work until model is provided.")
        except Exception as e:
            print(f"⚠ Error loading models: {e}")
    
    def detect_faces(self, image: Image.Image) -> List[List[float]]:
        """
        Detect faces in image using ULFD.

        Args:
            image: PIL Image object

        Returns:
            List of bounding boxes [[x, y, width, height], ...]
        """
        if self.ulfd_session is None:
            raise RuntimeError("ULFD model not loaded. Please provide model file.")

        # Save original dimensions
        orig_w, orig_h = image.size

        # Step 1: Resize to model input size (320x240)
        resized = image.resize((320, 240), Image.BILINEAR)

        # Step 2: Convert to numpy array and normalize
        # Normalization: (image - mean) / std
        img_array = np.array(resized, dtype=np.float32)
        normalized = (img_array - 127.0) / 128.0

        # Step 3: Transpose HWC to CHW
        img_chw = np.transpose(normalized, (2, 0, 1))

        # Step 4: Add batch dimension (1, 3, 240, 320)
        input_blob = np.expand_dims(img_chw, axis=0).astype(np.float32)

        # Step 5: Run ONNX inference
        input_name = self.ulfd_session.get_inputs()[0].name
        outputs = self.ulfd_session.run(None, {input_name: input_blob})

        # Step 6: Parse outputs
        # outputs[0]: confidences (1, num_boxes, 2)
        # outputs[1]: boxes (1, num_boxes, 4)
        confidences = outputs[0][0]  # Remove batch dimension
        boxes = outputs[1][0]        # Remove batch dimension

        # Step 7: Filter by confidence threshold
        confidence_threshold = 0.7
        valid_idx = confidences[:, 1] > confidence_threshold  # Class 1 = face

        if not np.any(valid_idx):
            return []

        filtered_boxes = boxes[valid_idx]
        filtered_scores = confidences[valid_idx, 1]

        # Step 8: Apply NMS (Non-Maximum Suppression)
        nms_boxes = self._apply_nms(filtered_boxes, filtered_scores, iou_threshold=0.3)

        # Step 9: Convert normalized coordinates to original image scale
        result = []
        for box in nms_boxes:
            # box format: [x_min, y_min, x_max, y_max] (normalized 0-1)
            x_min = box[0] * orig_w
            y_min = box[1] * orig_h
            x_max = box[2] * orig_w
            y_max = box[3] * orig_h

            # Convert to [x, y, width, height]
            width = x_max - x_min
            height = y_max - y_min

            result.append([float(x_min), float(y_min), float(width), float(height)])

        return result
    
    def extract_features(self, face_image: Image.Image) -> np.ndarray:
        """
        Extract 512-dimensional feature vector from face image using ArcFace.

        Args:
            face_image: PIL Image of cropped face

        Returns:
            512-dimensional feature vector as numpy array
        """
        if self.arcface_session is None:
            raise RuntimeError("ArcFace model not loaded. Please provide model file.")

        # Step 1: Resize to model input size (112x112)
        resized = face_image.resize((112, 112), Image.BILINEAR)

        # Step 2: Convert to numpy array and normalize
        # Normalization: (image - 127.5) / 127.5
        img_array = np.array(resized, dtype=np.float32)
        normalized = (img_array - 127.5) / 127.5

        # Step 3: Add batch dimension (1, 112, 112, 3) - HWC format
        # Note: garavv/arcface-onnx expects HWC format, not CHW
        input_blob = np.expand_dims(normalized, axis=0).astype(np.float32)

        # Step 4: Run ONNX inference
        input_name = self.arcface_session.get_inputs()[0].name
        outputs = self.arcface_session.run(None, {input_name: input_blob})

        # Step 5: Extract feature vector
        feature = outputs[0][0]  # Remove batch dimension

        # Step 6: L2 normalization (important for cosine similarity)
        norm = np.linalg.norm(feature)
        if norm > 0:
            feature = feature / norm

        return feature.astype(np.float32)

    @staticmethod
    def _apply_nms(boxes: np.ndarray, scores: np.ndarray, iou_threshold: float = 0.3) -> np.ndarray:
        """
        Apply Non-Maximum Suppression (NMS) to filter overlapping boxes.

        Args:
            boxes: Array of shape (N, 4) with format [x_min, y_min, x_max, y_max]
            scores: Array of shape (N,) with confidence scores
            iou_threshold: IoU threshold for suppression

        Returns:
            Filtered boxes after NMS
        """
        if len(boxes) == 0:
            return np.array([])

        # Sort by score (descending)
        order = scores.argsort()[::-1]

        keep = []
        while order.size > 0:
            # Pick the box with highest score
            i = order[0]
            keep.append(i)

            if order.size == 1:
                break

            # Calculate IoU with remaining boxes
            xx1 = np.maximum(boxes[i, 0], boxes[order[1:], 0])
            yy1 = np.maximum(boxes[i, 1], boxes[order[1:], 1])
            xx2 = np.minimum(boxes[i, 2], boxes[order[1:], 2])
            yy2 = np.minimum(boxes[i, 3], boxes[order[1:], 3])

            w = np.maximum(0.0, xx2 - xx1)
            h = np.maximum(0.0, yy2 - yy1)
            intersection = w * h

            area_i = (boxes[i, 2] - boxes[i, 0]) * (boxes[i, 3] - boxes[i, 1])
            area_others = (boxes[order[1:], 2] - boxes[order[1:], 0]) * \
                          (boxes[order[1:], 3] - boxes[order[1:], 1])
            union = area_i + area_others - intersection

            iou = intersection / (union + 1e-8)

            # Keep boxes with IoU < threshold
            inds = np.where(iou <= iou_threshold)[0]
            order = order[inds + 1]

        return boxes[keep]

    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First feature vector
            vec2: Second feature vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        # Normalize vectors
        vec1_norm = vec1 / (np.linalg.norm(vec1) + 1e-8)
        vec2_norm = vec2 / (np.linalg.norm(vec2) + 1e-8)
        
        # Calculate cosine similarity
        similarity = np.dot(vec1_norm, vec2_norm)
        
        # Ensure result is in [0, 1] range
        return float(max(0.0, min(1.0, similarity)))
    
    def recognize(self, image: Image.Image, threshold: float = 0.5) -> Dict:
        """
        Full recognition pipeline: detect, extract, match.
        
        Args:
            image: PIL Image to recognize
            threshold: Similarity threshold for recognition
            
        Returns:
            Dictionary with recognition results:
            {
                "status": "PASS" | "REJECT" | "NO_FACE",
                "user_id": int or None,
                "name": str or None,
                "confidence": float or None,
                "box": [x, y, w, h] or None
            }
        """
        # Step 1: Detect faces
        try:
            boxes = self.detect_faces(image)
        except RuntimeError as e:
            # Model not loaded
            return {
                "status": "NO_FACE",
                "user_id": None,
                "name": None,
                "confidence": None,
                "box": None,
                "error": str(e)
            }
        
        if not boxes:
            return {
                "status": "NO_FACE",
                "user_id": None,
                "name": None,
                "confidence": None,
                "box": None
            }
        
        # Step 2: Process the largest face (assume it's the main subject)
        largest_box = max(boxes, key=lambda b: b[2] * b[3])  # max by area
        
        # Step 3: Extract features
        try:
            face_img = crop_face(image, largest_box)
            current_vector = self.extract_features(face_img)
        except RuntimeError as e:
            return {
                "status": "NO_FACE",
                "user_id": None,
                "name": None,
                "confidence": None,
                "box": largest_box,
                "error": str(e)
            }
        
        # Step 4: Match against database
        if not self.face_database:
            # No registered users
            return {
                "status": "REJECT",
                "user_id": None,
                "name": "Unknown",
                "confidence": 0.0,
                "box": largest_box
            }
        
        best_match_id = None
        max_score = 0.0
        
        for user_id, registered_vector in self.face_database.items():
            score = self.cosine_similarity(current_vector, registered_vector)
            if score > max_score:
                max_score = score
                best_match_id = user_id
        
        # Step 5: Threshold decision
        if max_score >= threshold:
            return {
                "status": "PASS",
                "user_id": best_match_id,
                "name": None,  # Will be filled by caller from DB
                "confidence": max_score,
                "box": largest_box
            }
        else:
            return {
                "status": "REJECT",
                "user_id": None,
                "name": "Unknown",
                "confidence": max_score,
                "box": largest_box
            }
    
    def load_face_database(self, db: Session):
        """
        Load all user face features from database into memory.
        
        Args:
            db: Database session
        """
        users = db.query(User).all()
        self.face_database.clear()
        
        for user in users:
            try:
                # Deserialize feature vector from JSON
                feature_vector = np.array(json.loads(user.feature_vector), dtype=np.float32)
                self.face_database[user.id] = feature_vector
            except Exception as e:
                print(f"⚠ Error loading features for user {user.id}: {e}")
        
        print(f"✓ Loaded {len(self.face_database)} face features into memory")
    
    def add_user_to_database(self, user_id: int, feature_vector: np.ndarray):
        """
        Add a user's feature vector to in-memory database.
        
        Args:
            user_id: User ID
            feature_vector: 512-dim feature vector
        """
        self.face_database[user_id] = feature_vector
    
    def remove_user_from_database(self, user_id: int):
        """
        Remove a user from in-memory database.
        
        Args:
            user_id: User ID to remove
        """
        if user_id in self.face_database:
            del self.face_database[user_id]


# Global face engine instance
face_engine: Optional[FaceEngine] = None


def get_face_engine() -> FaceEngine:
    """Get the global face engine instance."""
    global face_engine
    if face_engine is None:
        face_engine = FaceEngine()
    return face_engine
