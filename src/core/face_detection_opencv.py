import cv2
import numpy as np
import os
import pickle
from datetime import datetime
import threading
import time

class OpenCVFaceDetector:
    """Enhanced face detection using OpenCV with improved accuracy"""
    
    def __init__(self):
        # Load face cascade classifier
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Initialize simple, reliable face recognizer
        self.face_recognizer = cv2.face.LBPHFaceRecognizer_create(
            radius=1,           # Simple radius
            neighbors=8,        # Standard neighbors
            grid_x=8,          # Standard grid
            grid_y=8,
            threshold=100.0     # Standard threshold
        )
        
        print("Face recognition system initialized")
        
        # Camera properties
        self.cap = None
        self.is_running = False
        self.current_frame = None
        self.detected_faces = []
        
        # Known faces data with multiple samples per person
        self.known_faces = {}  # {student_id: {'samples': [face_data], 'name': name}}
        self.face_labels = {}  # {label_id: student_info}
        self.is_trained = False
        
        # Enhanced detection parameters
        self.detection_history = {}  # Track detection consistency
        self.confidence_threshold = 0.3  # Lower threshold for better recognition
        self.min_face_size = (60, 60)   # Smaller minimum face size
        self.max_face_size = (500, 500) # Larger max size for flexibility
        
        # Threading
        self.capture_thread = None
        self.detection_thread = None
        self.thread_lock = threading.Lock()
        
        # Load existing face data if available
        self.load_face_data()
    
    def add_student_face(self, student_id, student_name, image_path):
        """Add a new student's face to the recognition system with enhanced preprocessing"""
        try:
            print(f"Attempting to load image from: {image_path}")
            
            # Read the image
            image = cv2.imread(image_path)
            if image is None:
                return False, f"Could not load image from {image_path}"
            
            print(f"Image loaded successfully, shape: {image.shape}")
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply histogram equalization for better contrast
            gray = cv2.equalizeHist(gray)
            
            # Use conservative face detection for registration
            faces_frontal = self.face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.2,    # More conservative detection
                minNeighbors=8,     # Higher threshold for accuracy
                minSize=(60, 60),   # Reasonable minimum size
                maxSize=(400, 400), # Reasonable maximum size
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            # Filter for quality faces only
            quality_faces = []
            for (x, y, w, h) in faces_frontal:
                aspect_ratio = w / h
                if 0.75 <= aspect_ratio <= 1.25 and w >= 60 and h >= 60:
                    quality_faces.append((x, y, w, h))
            
            all_faces = quality_faces
            
            if len(all_faces) == 0:
                print("No faces detected in image")
                return False, "No face detected in image. Please ensure good lighting and face is clearly visible."
            
            print(f"Detected {len(all_faces)} face(s)")
            
            # Select the largest face (most likely to be the main subject)
            largest_face = max(all_faces, key=lambda face: face[2] * face[3])
            (x, y, w, h) = largest_face
            
            # Add padding around face for better context
            padding = int(0.2 * min(w, h))
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(gray.shape[1] - x, w + 2 * padding)
            h = min(gray.shape[0] - y, h + 2 * padding)
            
            # Extract face region
            face_roi = gray[y:y+h, x:x+w]
            
            # Apply additional preprocessing
            face_roi = cv2.equalizeHist(face_roi)  # Normalize lighting
            face_roi = cv2.GaussianBlur(face_roi, (3, 3), 0)  # Slight blur to reduce noise
            
            # Create fewer, higher quality samples
            face_samples = []
            
            # Original face (main sample)
            face_resized = cv2.resize(face_roi, (200, 200))
            face_samples.append(face_resized)
            
            # Only add one slight variation for robustness
            bright_face = cv2.convertScaleAbs(face_roi, alpha=1.1, beta=5)
            bright_face = cv2.resize(bright_face, (200, 200))
            face_samples.append(bright_face)
            
            # Store face data with multiple samples
            if student_id not in self.known_faces:
                label_id = len(self.face_labels)
                self.known_faces[student_id] = {
                    'label_id': label_id,
                    'samples': face_samples,
                    'student_name': student_name
                }
                
                self.face_labels[label_id] = {
                    'student_id': student_id,
                    'student_name': student_name
                }
            else:
                # Add to existing samples
                self.known_faces[student_id]['samples'].extend(face_samples)
                # Keep only the most recent 10 samples to avoid overfitting
                self.known_faces[student_id]['samples'] = self.known_faces[student_id]['samples'][-10:]
            
            # Retrain the recognizer
            self.train_recognizer()
            
            # Save face data
            self.save_face_data()
            
            return True, f"Face added successfully with {len(face_samples)} training samples"
            
        except Exception as e:
            return False, f"Error adding face: {str(e)}"
    
    def train_recognizer(self):
        """Train the face recognizer with current face data using multiple samples"""
        try:
            if len(self.known_faces) == 0:
                return False
            
            faces = []
            labels = []
            
            # Collect all face samples for training
            for student_id, face_info in self.known_faces.items():
                for sample in face_info['samples']:
                    faces.append(sample)
                    labels.append(face_info['label_id'])
            
            if len(faces) == 0:
                return False
            
            # Train the recognizer with all samples
            self.face_recognizer.train(faces, np.array(labels))
            self.is_trained = True
            
            print(f"Trained recognizer with {len(faces)} face samples from {len(self.known_faces)} students")
            return True
            
        except Exception as e:
            print(f"Error training recognizer: {e}")
            return False
    
    def save_face_data(self):
        """Save face data to file"""
        try:
            os.makedirs('face_data', exist_ok=True)
            
            # Save known faces
            with open('face_data/known_faces.pkl', 'wb') as f:
                pickle.dump(self.known_faces, f)
            
            # Save face labels
            with open('face_data/face_labels.pkl', 'wb') as f:
                pickle.dump(self.face_labels, f)
            
            # Save trained model if available
            if self.is_trained:
                self.face_recognizer.save('face_data/face_model.yml')
            
        except Exception as e:
            print(f"Error saving face data: {e}")
    
    def load_face_data(self):
        """Load face data from file"""
        try:
            print("Loading face data...")
            
            if os.path.exists('face_data/known_faces.pkl'):
                with open('face_data/known_faces.pkl', 'rb') as f:
                    self.known_faces = pickle.load(f)
                print(f"Loaded {len(self.known_faces)} known faces")
            
            if os.path.exists('face_data/face_labels.pkl'):
                with open('face_data/face_labels.pkl', 'rb') as f:
                    self.face_labels = pickle.load(f)
                print(f"Loaded {len(self.face_labels)} face labels")
            
            if os.path.exists('face_data/face_model.yml') and len(self.known_faces) > 0:
                try:
                    self.face_recognizer.read('face_data/face_model.yml')
                    self.is_trained = True
                    print("Face recognition model loaded successfully")
                except Exception as e:
                    print(f"Error loading face model: {e}")
                    self.is_trained = False
            else:
                print("No face model found or no known faces")
            
        except Exception as e:
            print(f"Error loading face data: {e}")
            self.known_faces = {}
            self.face_labels = {}
            self.is_trained = False
    
    def start_detection(self, camera_index=0):
        """Start enhanced face detection with optimized camera settings"""
        try:
            self.cap = cv2.VideoCapture(camera_index)
            if not self.cap.isOpened():
                return False, "Could not open camera"
            
            # Set optimized camera properties for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 800)    # Good resolution
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 600)
            self.cap.set(cv2.CAP_PROP_FPS, 20)             # Smooth frame rate
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)       # Reduce buffer lag
            self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75) # Better auto exposure
            
            self.is_running = True
            
            # Initialize detection history
            self.detection_history = {}
            
            # Start capture thread
            self.capture_thread = threading.Thread(target=self._capture_frames)
            self.capture_thread.daemon = True
            self.capture_thread.start()
            
            # Start detection thread
            self.detection_thread = threading.Thread(target=self._detect_faces)
            self.detection_thread.daemon = True
            self.detection_thread.start()
            
            return True, "Enhanced detection started successfully"
            
        except Exception as e:
            return False, f"Error starting detection: {str(e)}"
    
    def stop_detection(self):
        """Stop face detection"""
        self.is_running = False
        
        if self.capture_thread:
            self.capture_thread.join(timeout=1)
        
        if self.detection_thread:
            self.detection_thread.join(timeout=1)
        
        if self.cap:
            self.cap.release()
        
        return True, "Detection stopped"
    
    def _capture_frames(self):
        """Capture frames from camera"""
        while self.is_running:
            try:
                ret, frame = self.cap.read()
                if ret:
                    with self.thread_lock:
                        self.current_frame = frame.copy()
                else:
                    time.sleep(0.1)
            except Exception as e:
                print(f"Error capturing frame: {e}")
                time.sleep(0.1)
    
    def _detect_faces(self):
        """Enhanced face detection and recognition with improved accuracy"""
        while self.is_running:
            try:
                with self.thread_lock:
                    if self.current_frame is None:
                        time.sleep(0.1)
                        continue
                    frame = self.current_frame.copy()
                
                # Convert to grayscale and enhance
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.equalizeHist(gray)  # Improve contrast
                
                # Use balanced face detection parameters
                faces_frontal = self.face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=1.2,      # Smaller scale factor for better detection
                    minNeighbors=6,       # Lower neighbors requirement for better detection
                    minSize=(80, 80),     # Smaller minimum size
                    maxSize=(400, 400),   # Larger max size
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
                # Apply Non-Maximum Suppression to remove overlapping detections
                if len(faces_frontal) > 1:
                    # Convert to format needed for NMS
                    boxes = []
                    for (x, y, w, h) in faces_frontal:
                        boxes.append([x, y, x + w, y + h])
                    
                    # Apply NMS with overlap threshold
                    import cv2
                    indices = cv2.dnn.NMSBoxes(boxes, [1.0] * len(boxes), 0.3, 0.4)
                    
                    if len(indices) > 0:
                        faces_frontal = [faces_frontal[i] for i in indices.flatten()]
                
                # Filter faces by quality and remove duplicates
                quality_faces = []
                for (x, y, w, h) in faces_frontal:
                    # Check aspect ratio (faces should be roughly square)
                    aspect_ratio = w / h
                    if 0.7 <= aspect_ratio <= 1.4 and w >= 80 and h >= 80:
                        # Check if this face overlaps significantly with existing faces
                        is_duplicate = False
                        for (qx, qy, qw, qh) in quality_faces:
                            # Calculate overlap
                            overlap_x = max(0, min(x + w, qx + qw) - max(x, qx))
                            overlap_y = max(0, min(y + h, qy + qh) - max(y, qy))
                            overlap_area = overlap_x * overlap_y
                            
                            # If overlap is more than 50% of either face, consider it duplicate
                            if overlap_area > 0.5 * min(w * h, qw * qh):
                                is_duplicate = True
                                break
                        
                        if not is_duplicate:
                            quality_faces.append((x, y, w, h))
                
                # Limit to maximum 2 faces to prevent excessive detections
                all_faces = quality_faces[:2] if len(quality_faces) > 2 else quality_faces
                
                detected_faces = []
                
                for (x, y, w, h) in all_faces:
                    # Add padding for better recognition
                    padding = int(0.1 * min(w, h))
                    x_pad = max(0, x - padding)
                    y_pad = max(0, y - padding)
                    w_pad = min(gray.shape[1] - x_pad, w + 2 * padding)
                    h_pad = min(gray.shape[0] - y_pad, h + 2 * padding)
                    
                    # Extract and preprocess face region
                    face_roi = gray[y_pad:y_pad+h_pad, x_pad:x_pad+w_pad]
                    face_roi = cv2.equalizeHist(face_roi)
                    face_roi = cv2.GaussianBlur(face_roi, (3, 3), 0)
                    face_roi = cv2.resize(face_roi, (200, 200))
                    
                    # Recognize face if model is trained
                    student_id = None
                    student_name = "Unknown"
                    confidence = 0
                    
                    if self.is_trained and len(self.known_faces) > 0:
                        try:
                            # Simple, reliable prediction
                            label_id, conf = self.face_recognizer.predict(face_roi)
                            
                            # Convert LBPH confidence to similarity score (lower conf = better match)
                            # LBPH typically gives values 0-100+, lower is better
                            if conf < 100:  # Only consider reasonable confidence values
                                similarity = max(0, (100 - conf) / 100)
                                
                                # Only accept if confidence is above threshold
                                if similarity > self.confidence_threshold:
                                    if label_id in self.face_labels:
                                        student_info = self.face_labels[label_id]
                                        student_id = student_info['student_id']
                                        student_name = student_info['student_name']
                                        confidence = similarity
                        except Exception as e:
                            print(f"Recognition error: {e}")
                            pass
                    
                    # Create face detection entry
                    face_key = f"{x}_{y}_{w}_{h}"  # Simple position-based key
                    current_time = datetime.now()
                    
                    # Track detection stability
                    if face_key not in self.detection_history:
                        self.detection_history[face_key] = {
                            'count': 1,
                            'first_seen': current_time,
                            'last_seen': current_time,
                            'student_id': student_id,
                            'name': student_name,
                            'confidence': confidence,
                            'location': (x, y, w, h)
                        }
                    else:
                        # Update existing detection
                        self.detection_history[face_key]['count'] += 1
                        self.detection_history[face_key]['last_seen'] = current_time
                        # Update with better confidence if available
                        if confidence > self.detection_history[face_key]['confidence']:
                            self.detection_history[face_key]['confidence'] = confidence
                            self.detection_history[face_key]['student_id'] = student_id
                            self.detection_history[face_key]['name'] = student_name
                
                # Clean up old detections (older than 5 seconds)
                current_time = datetime.now()
                keys_to_remove = []
                for key, detection in self.detection_history.items():
                    if (current_time - detection['last_seen']).total_seconds() > 5:
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    del self.detection_history[key]
                
                # Include detections (no stability requirement for faster response)
                stable_faces = []
                for detection in self.detection_history.values():
                    stable_faces.append({
                        'student_id': detection['student_id'],
                        'name': detection['name'],
                        'confidence': detection['confidence'],
                        'location': detection['location'],
                        'timestamp': detection['last_seen']
                    })
                
                with self.thread_lock:
                    self.detected_faces = stable_faces
                
                time.sleep(0.5)  # Faster detection interval
                
            except Exception as e:
                print(f"Error in face detection: {e}")
                time.sleep(0.1)
    

    
    def get_current_frame_raw(self):
        """Get current frame without annotations (raw image)"""
        try:
            with self.thread_lock:
                if self.current_frame is None:
                    return None
                return self.current_frame.copy()
        except Exception as e:
            print(f"Error getting raw frame: {e}")
            return None
    
    def get_current_frame_with_annotations(self):
        """Get current frame with face detection annotations"""
        try:
            with self.thread_lock:
                if self.current_frame is None:
                    return None
                
                frame = self.current_frame.copy()
                detected_faces = self.detected_faces.copy()
            
            # Draw face rectangles and labels
            for face in detected_faces:
                x, y, w, h = face['location']
                
                # Choose color and label based on recognition
                if face['student_id'] and face['confidence'] > 0.4:
                    color = (0, 255, 0)  # Green for recognized (BGR format)
                    confidence_percent = int(face['confidence'] * 100)
                    label = f"{face['name']} ({confidence_percent}%)"
                    text_color = (255, 255, 255)  # White text
                else:
                    color = (0, 0, 255)  # Red for unknown (BGR format)
                    label = "Unknown Person"
                    text_color = (255, 255, 255)  # White text
                
                # Draw thick rectangle around face
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 3)
                
                # Calculate text size for proper background
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.7
                thickness = 2
                (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, thickness)
                
                # Draw label background rectangle
                bg_y1 = max(0, y - text_height - 10)
                bg_y2 = y
                bg_x1 = x
                bg_x2 = min(frame.shape[1], x + text_width + 10)
                
                cv2.rectangle(frame, (bg_x1, bg_y1), (bg_x2, bg_y2), color, -1)
                
                # Draw label text
                text_x = x + 5
                text_y = y - 5
                cv2.putText(frame, label, (text_x, text_y), font, font_scale, text_color, thickness)
                
                # Add a small circle at the center of the face for better visibility
                center_x = x + w // 2
                center_y = y + h // 2
                cv2.circle(frame, (center_x, center_y), 3, color, -1)
            
            return frame
            
        except Exception as e:
            print(f"Error annotating frame: {e}")
            return self.current_frame if self.current_frame is not None else None
    
    def get_detected_faces(self):
        """Get currently detected faces"""
        with self.thread_lock:
            return self.detected_faces.copy()
    
    def remove_student_face(self, student_id):
        """Remove a student's face from the recognition system"""
        try:
            if student_id in self.known_faces:
                # Remove from known faces
                label_id = self.known_faces[student_id]['label_id']
                del self.known_faces[student_id]
                
                # Remove from face labels
                if label_id in self.face_labels:
                    del self.face_labels[label_id]
                
                # Clear detection history for this student
                self.detection_history = {k: v for k, v in self.detection_history.items() 
                                        if v.get('label') != label_id}
                
                # Retrain if there are still faces
                if len(self.known_faces) > 0:
                    self.train_recognizer()
                else:
                    self.is_trained = False
                
                # Save updated data
                self.save_face_data()
                
                return True, "Face removed successfully"
            else:
                return False, "Student face not found"
                
        except Exception as e:
            return False, f"Error removing face: {str(e)}"
    
    def get_recognition_stats(self):
        """Get statistics about the face recognition system"""
        return {
            'total_students': len(self.known_faces),
            'total_samples': sum(len(face_info['samples']) for face_info in self.known_faces.values()),
            'is_trained': self.is_trained,
            'confidence_threshold': self.confidence_threshold,
            'detection_active': self.is_running
        }
    
    def update_confidence_threshold(self, threshold):
        """Update the confidence threshold for recognition"""
        self.confidence_threshold = max(0.1, min(1.0, threshold))
        return f"Confidence threshold updated to {self.confidence_threshold:.2f}"