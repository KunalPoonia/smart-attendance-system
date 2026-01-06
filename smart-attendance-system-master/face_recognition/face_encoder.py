#!/usr/bin/env python3
"""
Face Encoder Module - OpenCV Implementation
This module provides face encoding functionality using OpenCV
"""

import logging
import numpy as np
import os

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None

class FaceEncoder:
    def __init__(self, tolerance=0.6):
        self.tolerance = tolerance
        self.logger = logging.getLogger(__name__)
        
        if not CV2_AVAILABLE:
            self.logger.warning("OpenCV not available - face encoding disabled")
            self.face_cascade = None
            return
            
        # Load OpenCV face cascade
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        if self.face_cascade.empty():
            self.logger.error("Failed to load face cascade")
            self.face_cascade = None
        else:
            self.logger.info("Face encoder initialized with OpenCV")
    
    def encode_face_from_image(self, image_path):
        """Extract face encoding from image using OpenCV"""
        if not CV2_AVAILABLE or self.face_cascade is None:
            self.logger.warning("Face encoding not available")
            return None
            
        try:
            if not os.path.exists(image_path):
                self.logger.error(f"Image file not found: {image_path}")
                return None
                
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                self.logger.error(f"Failed to read image: {image_path}")
                return None
                
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=5, 
                minSize=(30, 30)
            )
            
            if len(faces) == 0:
                self.logger.warning(f"No faces detected in image: {image_path}")
                return None
                
            # Use the largest face
            largest_face = max(faces, key=lambda x: x[2] * x[3])
            x, y, w, h = largest_face
            
            # Extract face region
            face_roi = gray[y:y+h, x:x+w]
            
            # Resize to standard size for comparison
            face_roi = cv2.resize(face_roi, (100, 100))
            
            # Create a simple "encoding" using histogram
            hist = cv2.calcHist([face_roi], [0], None, [256], [0, 256])
            
            # Normalize histogram
            hist = hist.flatten()
            hist = hist / (np.sum(hist) + 1e-7)  # Avoid division by zero
            
            self.logger.info(f"Face encoding created for: {image_path}")
            return hist.tolist()  # Convert to list for JSON serialization
            
        except Exception as e:
            self.logger.error(f"Error encoding face from {image_path}: {str(e)}")
            return None
    
    def compare_faces(self, known_encodings, face_encoding, tolerance=None):
        """Compare face encodings using histogram correlation"""
        if not known_encodings:
            return []
        if face_encoding is None:
            return []
            
        if tolerance is None:
            tolerance = self.tolerance
            
        try:
            face_encoding = np.array(face_encoding)
            matches = []
            
            for known_encoding in known_encodings:
                if known_encoding is None:
                    matches.append(False)
                    continue
                    
                known_encoding = np.array(known_encoding)
                
                # Calculate correlation coefficient
                correlation = cv2.compareHist(
                    face_encoding.astype(np.float32), 
                    known_encoding.astype(np.float32), 
                    cv2.HISTCMP_CORREL
                )
                
                # Higher correlation means better match
                matches.append(correlation > (1.0 - tolerance))
                
            return matches
            
        except Exception as e:
            self.logger.error(f"Error comparing faces: {str(e)}")
            return []
    
    def face_distance(self, known_encodings, face_encoding):
        """Calculate face distances using histogram correlation"""
        if not known_encodings:
            return []
        if face_encoding is None:
            return []
            
        try:
            face_encoding = np.array(face_encoding)
            distances = []
            
            for known_encoding in known_encodings:
                if known_encoding is None:
                    distances.append(1.0)  # Maximum distance
                    continue
                    
                known_encoding = np.array(known_encoding)
                
                # Calculate correlation coefficient
                correlation = cv2.compareHist(
                    face_encoding.astype(np.float32), 
                    known_encoding.astype(np.float32), 
                    cv2.HISTCMP_CORREL
                )
                
                # Convert correlation to distance (0 = perfect match, 1 = no match)
                distance = 1.0 - correlation
                distances.append(max(0.0, min(1.0, distance)))
                
            return distances
            
        except Exception as e:
            self.logger.error(f"Error calculating face distances: {str(e)}")
            return []