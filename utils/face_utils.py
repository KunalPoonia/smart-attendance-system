#!/usr/bin/env python3
"""
Face Recognition Utilities for Smart Attendance System
Provides comprehensive face detection, recognition, and processing utilities
with support for anti-spoofing, quality assessment, and batch processing.

Author: ayushap18
Date: January 2026
ECWoC 2026 Contribution
"""

import os
import logging
import json
import hashlib
import base64
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import io

# Try to import image processing libraries
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None
    np = None

try:
    from PIL import Image, ImageEnhance, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None
    ImageEnhance = None
    ImageFilter = None

# Configure logging
logger = logging.getLogger(__name__)


class FaceQuality(Enum):
    """Face image quality levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    REJECTED = "rejected"


class DetectionConfidence(Enum):
    """Face detection confidence levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class FaceRegion:
    """Represents a detected face region."""
    x: int
    y: int
    width: int
    height: int
    confidence: float = 0.0
    landmarks: Optional[Dict[str, Tuple[int, int]]] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    def get_center(self) -> Tuple[int, int]:
        """Get center point of face region."""
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    def get_area(self) -> int:
        """Get area of face region."""
        return self.width * self.height
    
    def expand(self, factor: float = 1.2) -> 'FaceRegion':
        """Expand face region by factor."""
        new_width = int(self.width * factor)
        new_height = int(self.height * factor)
        new_x = self.x - (new_width - self.width) // 2
        new_y = self.y - (new_height - self.height) // 2
        return FaceRegion(
            max(0, new_x), max(0, new_y), 
            new_width, new_height, 
            self.confidence, self.landmarks
        )


@dataclass
class FaceQualityReport:
    """Quality assessment report for a face image."""
    overall_quality: FaceQuality
    brightness_score: float
    contrast_score: float
    sharpness_score: float
    face_size_score: float
    face_position_score: float
    occlusion_score: float
    recommendations: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        result = asdict(self)
        result['overall_quality'] = self.overall_quality.value
        return result


class FaceDetector:
    """
    Advanced face detection with multiple backend support.
    """
    
    def __init__(self, backend: str = 'opencv'):
        """
        Initialize face detector.
        
        Args:
            backend: Detection backend ('opencv', 'dlib', 'mtcnn')
        """
        self.backend = backend
        self._cascade = None
        self._initialize_detector()
    
    def _initialize_detector(self):
        """Initialize the detection backend."""
        if not CV2_AVAILABLE:
            logger.warning("OpenCV not available. Face detection will be limited.")
            return
        
        if self.backend == 'opencv':
            cascade_paths = [
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml',
                cv2.data.haarcascades + 'haarcascade_frontalface_alt.xml',
                cv2.data.haarcascades + 'haarcascade_frontalface_alt2.xml'
            ]
            
            for path in cascade_paths:
                if os.path.exists(path):
                    self._cascade = cv2.CascadeClassifier(path)
                    if not self._cascade.empty():
                        logger.info(f"Loaded cascade classifier from {path}")
                        break
            
            if self._cascade is None or self._cascade.empty():
                logger.error("Failed to load cascade classifier")
    
    def detect_faces(self, image: Any, min_size: int = 30) -> List[FaceRegion]:
        """
        Detect faces in an image.
        
        Args:
            image: Image as numpy array, file path, or bytes
            min_size: Minimum face size to detect
            
        Returns:
            List of FaceRegion objects
        """
        if not CV2_AVAILABLE:
            return []
        
        # Load image
        img = self._load_image(image)
        if img is None:
            return []
        
        # Convert to grayscale
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        
        # Equalize histogram for better detection
        gray = cv2.equalizeHist(gray)
        
        faces = []
        
        if self._cascade is not None:
            # Detect faces using cascade classifier
            detections = self._cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(min_size, min_size),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            for (x, y, w, h) in detections:
                # Calculate confidence based on face size ratio
                img_area = gray.shape[0] * gray.shape[1]
                face_area = w * h
                confidence = min(1.0, (face_area / img_area) * 10)
                
                faces.append(FaceRegion(
                    x=int(x), y=int(y), 
                    width=int(w), height=int(h),
                    confidence=confidence
                ))
        
        return faces
    
    def detect_single_face(self, image: Any) -> Optional[FaceRegion]:
        """
        Detect single face in image (returns largest if multiple).
        
        Args:
            image: Input image
            
        Returns:
            FaceRegion or None if no face detected
        """
        faces = self.detect_faces(image)
        if not faces:
            return None
        
        # Return largest face
        return max(faces, key=lambda f: f.get_area())
    
    def _load_image(self, image: Any) -> Optional[Any]:
        """Load image from various sources."""
        if not CV2_AVAILABLE:
            return None
        
        if isinstance(image, np.ndarray):
            return image
        
        if isinstance(image, str):
            if os.path.exists(image):
                return cv2.imread(image)
            # Try base64
            try:
                img_data = base64.b64decode(image)
                nparr = np.frombuffer(img_data, np.uint8)
                return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            except Exception:
                pass
        
        if isinstance(image, bytes):
            nparr = np.frombuffer(image, np.uint8)
            return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        return None


class FaceQualityAssessor:
    """
    Assesses quality of face images for recognition.
    """
    
    # Quality thresholds
    BRIGHTNESS_THRESHOLD = (0.3, 0.7)
    CONTRAST_THRESHOLD = 0.3
    SHARPNESS_THRESHOLD = 100
    MIN_FACE_SIZE_RATIO = 0.1
    MAX_FACE_SIZE_RATIO = 0.8
    
    def __init__(self):
        """Initialize quality assessor."""
        self.detector = FaceDetector()
    
    def assess_quality(self, image: Any) -> FaceQualityReport:
        """
        Assess the quality of a face image.
        
        Args:
            image: Input image
            
        Returns:
            FaceQualityReport
        """
        recommendations = []
        
        # Load image
        if CV2_AVAILABLE:
            img = self._load_image(image)
            if img is None:
                return FaceQualityReport(
                    overall_quality=FaceQuality.REJECTED,
                    brightness_score=0,
                    contrast_score=0,
                    sharpness_score=0,
                    face_size_score=0,
                    face_position_score=0,
                    occlusion_score=0,
                    recommendations=["Failed to load image"]
                )
        else:
            return FaceQualityReport(
                overall_quality=FaceQuality.REJECTED,
                brightness_score=0,
                contrast_score=0,
                sharpness_score=0,
                face_size_score=0,
                face_position_score=0,
                occlusion_score=0,
                recommendations=["Image processing libraries not available"]
            )
        
        # Detect face
        face = self.detector.detect_single_face(img)
        if not face:
            return FaceQualityReport(
                overall_quality=FaceQuality.REJECTED,
                brightness_score=0,
                contrast_score=0,
                sharpness_score=0,
                face_size_score=0,
                face_position_score=0,
                occlusion_score=0,
                recommendations=["No face detected in image"]
            )
        
        # Extract face region
        face_img = img[face.y:face.y+face.height, face.x:face.x+face.width]
        
        # Calculate individual scores
        brightness_score = self._calculate_brightness(face_img)
        contrast_score = self._calculate_contrast(face_img)
        sharpness_score = self._calculate_sharpness(face_img)
        face_size_score = self._calculate_face_size_score(face, img.shape)
        face_position_score = self._calculate_position_score(face, img.shape)
        occlusion_score = self._estimate_occlusion(face_img)
        
        # Generate recommendations
        if brightness_score < self.BRIGHTNESS_THRESHOLD[0]:
            recommendations.append("Image is too dark. Increase lighting.")
        elif brightness_score > self.BRIGHTNESS_THRESHOLD[1]:
            recommendations.append("Image is too bright. Reduce lighting or avoid direct light.")
        
        if contrast_score < self.CONTRAST_THRESHOLD:
            recommendations.append("Image has low contrast. Improve lighting conditions.")
        
        if sharpness_score < self.SHARPNESS_THRESHOLD:
            recommendations.append("Image is blurry. Hold camera steady or increase focus.")
        
        if face_size_score < 0.5:
            recommendations.append("Face is too small. Move closer to the camera.")
        elif face_size_score > 0.95:
            recommendations.append("Face is too large. Move back from the camera.")
        
        if face_position_score < 0.5:
            recommendations.append("Face is not centered. Position face in center of frame.")
        
        if occlusion_score < 0.7:
            recommendations.append("Face may be partially obscured. Remove any obstructions.")
        
        # Calculate overall quality
        scores = [
            brightness_score,
            contrast_score / 1.0,  # Normalize
            min(1.0, sharpness_score / 200),  # Normalize
            face_size_score,
            face_position_score,
            occlusion_score
        ]
        avg_score = sum(scores) / len(scores)
        
        if avg_score >= 0.8:
            overall_quality = FaceQuality.EXCELLENT
        elif avg_score >= 0.65:
            overall_quality = FaceQuality.GOOD
        elif avg_score >= 0.5:
            overall_quality = FaceQuality.ACCEPTABLE
        elif avg_score >= 0.3:
            overall_quality = FaceQuality.POOR
        else:
            overall_quality = FaceQuality.REJECTED
        
        return FaceQualityReport(
            overall_quality=overall_quality,
            brightness_score=round(brightness_score, 3),
            contrast_score=round(contrast_score, 3),
            sharpness_score=round(sharpness_score, 3),
            face_size_score=round(face_size_score, 3),
            face_position_score=round(face_position_score, 3),
            occlusion_score=round(occlusion_score, 3),
            recommendations=recommendations
        )
    
    def _load_image(self, image: Any) -> Optional[Any]:
        """Load image from various sources."""
        if isinstance(image, np.ndarray):
            return image
        if isinstance(image, str) and os.path.exists(image):
            return cv2.imread(image)
        if isinstance(image, bytes):
            nparr = np.frombuffer(image, np.uint8)
            return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return None
    
    def _calculate_brightness(self, image: Any) -> float:
        """Calculate brightness score (0-1)."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        return np.mean(gray) / 255.0
    
    def _calculate_contrast(self, image: Any) -> float:
        """Calculate contrast score."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        return np.std(gray) / 128.0  # Normalize to roughly 0-1 range
    
    def _calculate_sharpness(self, image: Any) -> float:
        """Calculate sharpness score using Laplacian variance."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        return cv2.Laplacian(gray, cv2.CV_64F).var()
    
    def _calculate_face_size_score(self, face: FaceRegion, img_shape: Tuple) -> float:
        """Calculate face size score relative to image."""
        img_area = img_shape[0] * img_shape[1]
        face_area = face.get_area()
        ratio = face_area / img_area
        
        if ratio < self.MIN_FACE_SIZE_RATIO:
            return ratio / self.MIN_FACE_SIZE_RATIO
        elif ratio > self.MAX_FACE_SIZE_RATIO:
            return max(0, 1 - (ratio - self.MAX_FACE_SIZE_RATIO) * 2)
        else:
            # Optimal range
            return 1.0
    
    def _calculate_position_score(self, face: FaceRegion, img_shape: Tuple) -> float:
        """Calculate face position score (centered is better)."""
        img_center = (img_shape[1] // 2, img_shape[0] // 2)
        face_center = face.get_center()
        
        # Calculate distance from center
        max_dist = ((img_shape[0] / 2) ** 2 + (img_shape[1] / 2) ** 2) ** 0.5
        dist = ((face_center[0] - img_center[0]) ** 2 + 
                (face_center[1] - img_center[1]) ** 2) ** 0.5
        
        return max(0, 1 - (dist / max_dist))
    
    def _estimate_occlusion(self, face_image: Any) -> float:
        """
        Estimate face occlusion (simplified).
        Returns score from 0 (heavily occluded) to 1 (no occlusion).
        """
        # Simple heuristic based on edge density
        if len(face_image.shape) == 3:
            gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
        else:
            gray = face_image
        
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.count_nonzero(edges) / edges.size
        
        # Expected edge density for non-occluded face
        expected_density = 0.15
        
        if edge_density < 0.05:
            return 0.5  # Too few edges, might be occluded
        elif edge_density > 0.3:
            return 0.7  # Too many edges, might have obstructions
        else:
            return min(1.0, edge_density / expected_density)


class FaceImageProcessor:
    """
    Image processing utilities for face recognition.
    """
    
    def __init__(self):
        """Initialize processor."""
        pass
    
    def normalize_face(self, image: Any, target_size: Tuple[int, int] = (224, 224)) -> Optional[Any]:
        """
        Normalize face image for recognition.
        
        Args:
            image: Input image
            target_size: Target output size
            
        Returns:
            Normalized image
        """
        if not CV2_AVAILABLE:
            return None
        
        img = self._load_image(image)
        if img is None:
            return None
        
        # Resize
        img = cv2.resize(img, target_size)
        
        # Convert to float and normalize
        img = img.astype(np.float32) / 255.0
        
        # Apply histogram equalization per channel
        for i in range(3):
            img[:, :, i] = cv2.equalizeHist((img[:, :, i] * 255).astype(np.uint8)) / 255.0
        
        return img
    
    def enhance_face(self, image: Any) -> Optional[Any]:
        """
        Enhance face image quality.
        
        Args:
            image: Input image
            
        Returns:
            Enhanced image
        """
        if not CV2_AVAILABLE:
            return None
        
        img = self._load_image(image)
        if img is None:
            return None
        
        # Apply bilateral filter to reduce noise while keeping edges sharp
        img = cv2.bilateralFilter(img, 9, 75, 75)
        
        # Increase contrast
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        lab = cv2.merge([l, a, b])
        img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # Slight sharpening
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]])
        img = cv2.filter2D(img, -1, kernel * 0.3 + np.array([[0, 0, 0], [0, 1, 0], [0, 0, 0]]) * 0.7)
        
        return img
    
    def crop_face(self, image: Any, face: FaceRegion, padding: float = 0.2) -> Optional[Any]:
        """
        Crop face from image with padding.
        
        Args:
            image: Input image
            face: FaceRegion to crop
            padding: Padding ratio around face
            
        Returns:
            Cropped face image
        """
        if not CV2_AVAILABLE:
            return None
        
        img = self._load_image(image)
        if img is None:
            return None
        
        h, w = img.shape[:2]
        
        # Calculate padded region
        pad_w = int(face.width * padding)
        pad_h = int(face.height * padding)
        
        x1 = max(0, face.x - pad_w)
        y1 = max(0, face.y - pad_h)
        x2 = min(w, face.x + face.width + pad_w)
        y2 = min(h, face.y + face.height + pad_h)
        
        return img[y1:y2, x1:x2]
    
    def align_face(self, image: Any, landmarks: Dict[str, Tuple[int, int]] = None) -> Optional[Any]:
        """
        Align face based on eye positions.
        
        Args:
            image: Input image
            landmarks: Face landmarks with 'left_eye' and 'right_eye'
            
        Returns:
            Aligned face image
        """
        if not CV2_AVAILABLE or landmarks is None:
            return None
        
        img = self._load_image(image)
        if img is None:
            return None
        
        left_eye = landmarks.get('left_eye')
        right_eye = landmarks.get('right_eye')
        
        if not left_eye or not right_eye:
            return img
        
        # Calculate angle
        dY = right_eye[1] - left_eye[1]
        dX = right_eye[0] - left_eye[0]
        angle = np.degrees(np.arctan2(dY, dX))
        
        # Calculate center
        eye_center = (
            (left_eye[0] + right_eye[0]) // 2,
            (left_eye[1] + right_eye[1]) // 2
        )
        
        # Get rotation matrix
        h, w = img.shape[:2]
        M = cv2.getRotationMatrix2D(eye_center, angle, 1.0)
        
        # Apply rotation
        aligned = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC)
        
        return aligned
    
    def convert_to_grayscale(self, image: Any) -> Optional[Any]:
        """Convert image to grayscale."""
        if not CV2_AVAILABLE:
            return None
        
        img = self._load_image(image)
        if img is None:
            return None
        
        if len(img.shape) == 3:
            return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return img
    
    def resize_image(self, image: Any, size: Tuple[int, int]) -> Optional[Any]:
        """Resize image to specified size."""
        if not CV2_AVAILABLE:
            return None
        
        img = self._load_image(image)
        if img is None:
            return None
        
        return cv2.resize(img, size, interpolation=cv2.INTER_AREA)
    
    def _load_image(self, image: Any) -> Optional[Any]:
        """Load image from various sources."""
        if isinstance(image, np.ndarray):
            return image.copy()
        if isinstance(image, str) and os.path.exists(image):
            return cv2.imread(image)
        if isinstance(image, bytes):
            nparr = np.frombuffer(image, np.uint8)
            return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return None


class FaceEncodingManager:
    """
    Manages face encodings for recognition.
    """
    
    def __init__(self, storage_path: str = 'face_encodings'):
        """
        Initialize encoding manager.
        
        Args:
            storage_path: Path to store face encodings
        """
        self.storage_path = storage_path
        self.encodings: Dict[str, List[Any]] = {}
        self._ensure_storage_path()
    
    def _ensure_storage_path(self):
        """Ensure storage directory exists."""
        os.makedirs(self.storage_path, exist_ok=True)
    
    def add_encoding(self, person_id: str, encoding: Any, metadata: Dict = None):
        """
        Add a face encoding for a person.
        
        Args:
            person_id: Unique person identifier
            encoding: Face encoding vector
            metadata: Optional metadata
        """
        if person_id not in self.encodings:
            self.encodings[person_id] = []
        
        self.encodings[person_id].append({
            'encoding': encoding.tolist() if hasattr(encoding, 'tolist') else encoding,
            'metadata': metadata or {},
            'added_at': datetime.now().isoformat()
        })
    
    def get_encodings(self, person_id: str) -> List[Any]:
        """Get all encodings for a person."""
        return self.encodings.get(person_id, [])
    
    def remove_encodings(self, person_id: str):
        """Remove all encodings for a person."""
        if person_id in self.encodings:
            del self.encodings[person_id]
    
    def get_all_person_ids(self) -> List[str]:
        """Get all person IDs with encodings."""
        return list(self.encodings.keys())
    
    def save_to_file(self, filename: str = 'encodings.json'):
        """Save encodings to file."""
        filepath = os.path.join(self.storage_path, filename)
        with open(filepath, 'w') as f:
            json.dump(self.encodings, f, indent=2, default=str)
        logger.info(f"Saved encodings to {filepath}")
    
    def load_from_file(self, filename: str = 'encodings.json'):
        """Load encodings from file."""
        filepath = os.path.join(self.storage_path, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                self.encodings = json.load(f)
            logger.info(f"Loaded encodings from {filepath}")
        else:
            logger.warning(f"Encoding file not found: {filepath}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get encoding statistics."""
        total_encodings = sum(len(v) for v in self.encodings.values())
        return {
            'total_persons': len(self.encodings),
            'total_encodings': total_encodings,
            'average_per_person': total_encodings / len(self.encodings) if self.encodings else 0,
            'persons': {pid: len(encs) for pid, encs in self.encodings.items()}
        }


class AntiSpoofingChecker:
    """
    Basic anti-spoofing checks for face recognition.
    """
    
    def __init__(self):
        """Initialize anti-spoofing checker."""
        self.texture_threshold = 100
        self.reflection_threshold = 200
    
    def check_liveness(self, image: Any) -> Dict[str, Any]:
        """
        Perform basic liveness checks on face image.
        
        Args:
            image: Input face image
            
        Returns:
            Liveness check results
        """
        if not CV2_AVAILABLE:
            return {
                'is_live': None,
                'confidence': 0,
                'checks': {},
                'message': 'Image processing not available'
            }
        
        img = self._load_image(image)
        if img is None:
            return {
                'is_live': None,
                'confidence': 0,
                'checks': {},
                'message': 'Failed to load image'
            }
        
        checks = {
            'texture': self._check_texture(img),
            'color_distribution': self._check_color_distribution(img),
            'reflection': self._check_reflection(img),
            'edge_density': self._check_edge_density(img)
        }
        
        # Calculate overall confidence
        passed_checks = sum(1 for v in checks.values() if v['passed'])
        total_checks = len(checks)
        confidence = passed_checks / total_checks
        
        is_live = confidence >= 0.6
        
        return {
            'is_live': is_live,
            'confidence': round(confidence, 3),
            'checks': checks,
            'message': 'Passed liveness check' if is_live else 'Failed liveness check'
        }
    
    def _load_image(self, image: Any) -> Optional[Any]:
        """Load image."""
        if isinstance(image, np.ndarray):
            return image
        if isinstance(image, str) and os.path.exists(image):
            return cv2.imread(image)
        if isinstance(image, bytes):
            nparr = np.frombuffer(image, np.uint8)
            return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return None
    
    def _check_texture(self, image: Any) -> Dict[str, Any]:
        """Check image texture complexity."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        passed = laplacian_var > self.texture_threshold
        
        return {
            'passed': passed,
            'score': round(laplacian_var, 2),
            'threshold': self.texture_threshold,
            'message': 'Texture complexity check' + (' passed' if passed else ' failed')
        }
    
    def _check_color_distribution(self, image: Any) -> Dict[str, Any]:
        """Check for natural color distribution."""
        # Check if image has natural skin tone distribution
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Typical skin tone ranges in HSV
        lower_skin = np.array([0, 20, 70])
        upper_skin = np.array([20, 255, 255])
        
        mask = cv2.inRange(hsv, lower_skin, upper_skin)
        skin_ratio = np.count_nonzero(mask) / mask.size
        
        # Expect some skin tone in face image
        passed = 0.1 < skin_ratio < 0.8
        
        return {
            'passed': passed,
            'score': round(skin_ratio, 3),
            'message': 'Color distribution check' + (' passed' if passed else ' failed')
        }
    
    def _check_reflection(self, image: Any) -> Dict[str, Any]:
        """Check for unusual reflections (screen/paper)."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Count very bright spots (potential screen reflections)
        bright_pixels = np.count_nonzero(gray > self.reflection_threshold)
        bright_ratio = bright_pixels / gray.size
        
        # Too many bright spots may indicate screen
        passed = bright_ratio < 0.15
        
        return {
            'passed': passed,
            'score': round(bright_ratio, 3),
            'message': 'Reflection check' + (' passed' if passed else ' failed')
        }
    
    def _check_edge_density(self, image: Any) -> Dict[str, Any]:
        """Check edge density (printed photos have different edge patterns)."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.count_nonzero(edges) / edges.size
        
        # Natural faces have moderate edge density
        passed = 0.05 < edge_density < 0.25
        
        return {
            'passed': passed,
            'score': round(edge_density, 3),
            'message': 'Edge density check' + (' passed' if passed else ' failed')
        }


class FaceRecognitionCache:
    """
    Caching system for face recognition results.
    """
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        """
        Initialize cache.
        
        Args:
            max_size: Maximum cache entries
            ttl_seconds: Time to live for cache entries
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Dict] = {}
    
    def _generate_key(self, image: Any) -> str:
        """Generate cache key from image."""
        if isinstance(image, np.ndarray):
            data = image.tobytes()
        elif isinstance(image, bytes):
            data = image
        elif isinstance(image, str):
            data = image.encode()
        else:
            data = str(image).encode()
        
        return hashlib.md5(data).hexdigest()
    
    def get(self, image: Any) -> Optional[Dict]:
        """Get cached result for image."""
        key = self._generate_key(image)
        
        if key in self._cache:
            entry = self._cache[key]
            # Check TTL
            age = (datetime.now() - datetime.fromisoformat(entry['timestamp'])).seconds
            if age < self.ttl_seconds:
                return entry['result']
            else:
                del self._cache[key]
        
        return None
    
    def set(self, image: Any, result: Dict):
        """Cache result for image."""
        # Evict old entries if at capacity
        if len(self._cache) >= self.max_size:
            self._evict_oldest()
        
        key = self._generate_key(image)
        self._cache[key] = {
            'result': result,
            'timestamp': datetime.now().isoformat()
        }
    
    def _evict_oldest(self):
        """Evict oldest cache entries."""
        if not self._cache:
            return
        
        # Sort by timestamp and remove oldest 10%
        sorted_keys = sorted(
            self._cache.keys(),
            key=lambda k: self._cache[k]['timestamp']
        )
        
        to_remove = max(1, len(sorted_keys) // 10)
        for key in sorted_keys[:to_remove]:
            del self._cache[key]
    
    def clear(self):
        """Clear all cache entries."""
        self._cache = {}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'ttl_seconds': self.ttl_seconds,
            'utilization': len(self._cache) / self.max_size if self.max_size > 0 else 0
        }


# Convenience functions

def detect_faces(image: Any) -> List[FaceRegion]:
    """
    Quick function to detect faces in an image.
    
    Args:
        image: Input image
        
    Returns:
        List of detected face regions
    """
    detector = FaceDetector()
    return detector.detect_faces(image)


def assess_face_quality(image: Any) -> Dict[str, Any]:
    """
    Quick function to assess face image quality.
    
    Args:
        image: Input image
        
    Returns:
        Quality assessment results
    """
    assessor = FaceQualityAssessor()
    report = assessor.assess_quality(image)
    return report.to_dict()


def check_liveness(image: Any) -> Dict[str, Any]:
    """
    Quick function to check face liveness.
    
    Args:
        image: Input face image
        
    Returns:
        Liveness check results
    """
    checker = AntiSpoofingChecker()
    return checker.check_liveness(image)


def enhance_face_image(image: Any) -> Optional[Any]:
    """
    Quick function to enhance face image.
    
    Args:
        image: Input image
        
    Returns:
        Enhanced image
    """
    processor = FaceImageProcessor()
    return processor.enhance_face(image)


if __name__ == '__main__':
    print("=== Face Recognition Utilities ===")
    print(f"OpenCV Available: {CV2_AVAILABLE}")
    print(f"PIL Available: {PIL_AVAILABLE}")
    
    if CV2_AVAILABLE:
        print("\nTesting face detection...")
        detector = FaceDetector()
        print(f"Detector initialized with backend: {detector.backend}")
        
        print("\nTesting quality assessor...")
        assessor = FaceQualityAssessor()
        print("Quality assessor initialized")
        
        print("\nTesting anti-spoofing checker...")
        checker = AntiSpoofingChecker()
        print("Anti-spoofing checker initialized")
        
        print("\nTesting image processor...")
        processor = FaceImageProcessor()
        print("Image processor initialized")
        
        print("\nAll modules initialized successfully!")
    else:
        print("\nOpenCV not available. Face processing features are limited.")
