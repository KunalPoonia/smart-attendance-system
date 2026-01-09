#!/usr/bin/env python3
"""
Face Detector Module - OpenCV Implementation
This module provides real-time face detection and recognition functionality
"""

import logging
import threading
import time
import numpy as np
from datetime import datetime

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    cv2 = None

class FaceDetector:
    def __init__(self, camera_index=0, tolerance=0.6):
        self.camera_index = camera_index
        self.tolerance = tolerance
        self.is_running = False
        self.known_faces = []
        self.detected_faces = []
        self.current_frame = None
        self.cap = None
        self.lock = threading.Lock()
        self.detection_thread = None
        
        self.logger = logging.getLogger(__name__)
        
        if not CV2_AVAILABLE:
            self.logger.warning("OpenCV not available - face detection disabled")
            self.face_cascade = None
            return
            
        # Load OpenCV face cascade
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        if self.face_cascade.empty():
            self.logger.error("Failed to load face cascade")
            self.face_cascade = None
        else:
            self.logger.info("Face detector initialized with OpenCV")
    
    def load_known_faces(self, students_data):
        """Load known faces from student data"""
        with self.lock:
            self.known_faces = []
            for student in students_data:
                encoding = student.get('face_encoding')
                # Check if encoding exists and has data (handle numpy arrays properly)
                has_encoding = encoding is not None and (
                    (hasattr(encoding, '__len__') and len(encoding) > 0) or
                    (isinstance(encoding, (list, tuple)) and len(encoding) > 0)
                )
                if has_encoding:
                    self.known_faces.append({
                        'id': student['id'],
                        'name': student['name'],
                        'student_id': student['student_id'],
                        'encoding': encoding
                    })
        
        self.logger.info(f"Loaded {len(self.known_faces)} student faces for recognition")
        return True
    
    def start_detection(self):
        """Start face detection"""
        if not CV2_AVAILABLE or self.face_cascade is None:
            self.logger.error("Face detection not available")
            return False
            
        if self.is_running:
            return True
            
        try:
            # Initialize camera
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                self.logger.error(f"Failed to open camera {self.camera_index}")
                return False
                
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            self.is_running = True
            
            # Start detection thread
            self.detection_thread = threading.Thread(target=self._detection_loop)
            self.detection_thread.daemon = True
            self.detection_thread.start()
            
            self.logger.info("Face detection started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting face detection: {str(e)}")
            return False
    
    def stop_detection(self):
        """Stop face detection"""
        try:
            self.is_running = False
            
            if self.detection_thread:
                self.detection_thread.join(timeout=2)
                
            if self.cap:
                self.cap.release()
                self.cap = None
                
            with self.lock:
                self.current_frame = None
                self.detected_faces = []
                
            self.logger.info("Face detection stopped")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping face detection: {str(e)}")
            return False
    
    def _detection_loop(self):
        """Main detection loop running in background thread"""
        while self.is_running and self.cap:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    self.logger.warning("Failed to read frame from camera")
                    time.sleep(0.1)
                    continue
                    
                # Process frame for face detection
                self._process_frame(frame)
                
                with self.lock:
                    self.current_frame = frame.copy()
                    
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                self.logger.error(f"Error in detection loop: {str(e)}")
                break
    
    def _process_frame(self, frame):
        """Process frame for face detection and recognition"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(50, 50)
            )
            
            detected_faces = []
            
            for (x, y, w, h) in faces:
                # Extract face region
                face_roi = gray[y:y+h, x:x+w]
                face_roi = cv2.resize(face_roi, (100, 100))
                
                # Create histogram encoding
                hist = cv2.calcHist([face_roi], [0], None, [256], [0, 256])
                hist = hist.flatten()
                hist = hist / (np.sum(hist) + 1e-7)
                
                # Try to recognize face
                recognized_student = self._recognize_face(hist.tolist())
                
                if recognized_student:
                    detected_faces.append({
                        'student_id': recognized_student['student_id'],
                        'name': recognized_student['name'],
                        'confidence': recognized_student['confidence'],
                        'location': [x, y, w, h],
                        'timestamp': datetime.now()
                    })
                else:
                    # Unknown face
                    detected_faces.append({
                        'student_id': None,
                        'name': 'Unknown',
                        'confidence': 0.0,
                        'location': [x, y, w, h],
                        'timestamp': datetime.now()
                    })
            
            with self.lock:
                self.detected_faces = detected_faces
                
        except Exception as e:
            self.logger.error(f"Error processing frame: {str(e)}")
    
    def _recognize_face(self, face_encoding):
        """Recognize face against known faces"""
        if not self.known_faces:
            return None
        if face_encoding is None:
            return None
            
        try:
            face_encoding = np.array(face_encoding)
            best_match = None
            best_confidence = 0.0
            
            for known_face in self.known_faces:
                known_encoding = np.array(known_face['encoding'])
                
                # Calculate correlation
                correlation = cv2.compareHist(
                    face_encoding.astype(np.float32),
                    known_encoding.astype(np.float32),
                    cv2.HISTCMP_CORREL
                )
                
                # Check if this is a good match
                if correlation > (1.0 - self.tolerance) and correlation > best_confidence:
                    best_confidence = correlation
                    best_match = {
                        'student_id': known_face['student_id'],
                        'name': known_face['name'],
                        'confidence': correlation
                    }
            
            return best_match
            
        except Exception as e:
            self.logger.error(f"Error recognizing face: {str(e)}")
            return None
    
    def get_detected_faces(self):
        """Get currently detected faces"""
        with self.lock:
            return self.detected_faces.copy()
    
    def get_current_frame_with_annotations(self):
        """Get current frame with face annotations"""
        with self.lock:
            if self.current_frame is None:
                return None
                
            frame = self.current_frame.copy()
            detected_faces = self.detected_faces.copy()
        
        # Draw face rectangles and labels
        for face in detected_faces:
            x, y, w, h = face['location']
            
            # Choose color based on recognition
            if face['student_id']:
                color = (0, 255, 0)  # Green for recognized
                label = f"{face['name']} ({face['confidence']:.2f})"
            else:
                color = (0, 0, 255)  # Red for unknown
                label = "Unknown"
            
            # Draw rectangle
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            
            # Draw label background
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(frame, (x, y - 25), (x + label_size[0], y), color, -1)
            
            # Draw label text
            cv2.putText(frame, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Add status
        status = f"Faces: {len(detected_faces)} | Recognition: {'ON' if self.known_faces else 'OFF'}"
        cv2.putText(frame, status, (10, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        return frame
    
    def is_detection_running(self):
        """Check if detection is running"""
        return self.is_running