import cv2
import numpy as np
import os
import pickle
from datetime import datetime
import threading
import time

class EnhancedFaceRecognition:
    """Completely rewritten face recognition system with larger camera feed"""
    
    def __init__(self):
        print("🚀 Initializing New Enhanced Face Recognition System...")
        
        # Initialize face detector
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Initialize face recognizer with more lenient settings
        self.recognizer = cv2.face.LBPHFaceRecognizer_create(
            radius=1, neighbors=8, grid_x=8, grid_y=8, threshold=100.0
        )
        
        # Camera settings
        self.cap = None
        self.is_running = False
        self.current_frame = None
        self.detected_faces = []
        
        # Face data
        self.known_faces = {}
        self.face_labels = {}
        self.is_trained = False
        
        # Threading
        self.capture_thread = None
        self.detection_thread = None
        self.thread_lock = threading.RLock()
        
        # Load existing data
        self.load_face_data()
        
        print(f"✅ New system ready with {len(self.known_faces)} known faces")
    
    def detect_faces(self, frame):
        """Simple but effective face detection"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply histogram equalization for better detection
        gray = cv2.equalizeHist(gray)
        
        # Detect faces with optimized parameters
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(60, 60),
            maxSize=(300, 300),
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        return faces
    
    def preprocess_face(self, face_roi):
        """Simple face preprocessing"""
        if face_roi.size == 0:
            return None
        
        # Resize to standard size
        face_resized = cv2.resize(face_roi, (200, 200))
        
        # Apply histogram equalization
        face_eq = cv2.equalizeHist(face_resized)
        
        return face_eq
    
    def add_student_face(self, student_id, student_name, image_path):
        """Add student face with multiple samples"""
        try:
            print(f"🎯 Adding face for {student_name} (ID: {student_id})")
            
            if not os.path.exists(image_path):
                return False, f"Image file not found: {image_path}"
            
            image = cv2.imread(image_path)
            if image is None:
                return False, "Could not load image"
            
            # Detect faces
            faces = self.detect_faces(image)
            
            if len(faces) == 0:
                return False, "No face detected in image"
            
            # Use the largest face
            largest_face = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = largest_face
            
            # Extract face region with padding
            padding = 20
            x_start = max(0, x - padding)
            y_start = max(0, y - padding)
            x_end = min(image.shape[1], x + w + padding)
            y_end = min(image.shape[0], y + h + padding)
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            face_roi = gray[y_start:y_end, x_start:x_end]
            
            # Preprocess face
            processed_face = self.preprocess_face(face_roi)
            if processed_face is None:
                return False, "Face preprocessing failed"
            
            # Create multiple variations for better training
            face_samples = [processed_face]
            
            # Add slightly rotated versions
            for angle in [-5, 5]:
                center = (processed_face.shape[1]//2, processed_face.shape[0]//2)
                rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
                rotated = cv2.warpAffine(processed_face, rotation_matrix, 
                                       (processed_face.shape[1], processed_face.shape[0]))
                face_samples.append(rotated)
            
            # Add brightness variations
            bright = cv2.convertScaleAbs(processed_face, alpha=1.2, beta=10)
            dark = cv2.convertScaleAbs(processed_face, alpha=0.8, beta=-10)
            face_samples.extend([bright, dark])
            
            # Store face data
            if student_id not in self.known_faces:
                label_id = len(self.face_labels)
                self.known_faces[student_id] = {
                    'name': student_name,
                    'label_id': label_id,
                    'images': face_samples,
                    'registration_date': datetime.now()
                }
                self.face_labels[label_id] = {
                    'student_id': student_id,
                    'name': student_name
                }
            else:
                # Update existing
                self.known_faces[student_id]['name'] = student_name
                self.known_faces[student_id]['images'] = face_samples
            
            # Train recognizer
            success = self.train_recognizer()
            if success:
                self.save_face_data()
                return True, f"Face registered for {student_name} with {len(face_samples)} samples"
            else:
                return False, "Failed to train recognizer"
            
        except Exception as e:
            print(f"Error adding face: {e}")
            return False, f"Error: {str(e)}"
    
    def train_recognizer(self):
        """Train the face recognizer"""
        try:
            if len(self.known_faces) == 0:
                self.is_trained = False
                return False
            
            faces = []
            labels = []
            
            for student_id, face_data in self.known_faces.items():
                for face_image in face_data['images']:
                    faces.append(face_image)
                    labels.append(face_data['label_id'])
            
            if len(faces) < 2:
                self.is_trained = False
                return False
            
            # Train the recognizer
            self.recognizer.train(faces, np.array(labels))
            self.is_trained = True
            
            print(f"✅ Trained with {len(faces)} samples from {len(self.known_faces)} students")
            return True
            
        except Exception as e:
            print(f"Error training: {e}")
            self.is_trained = False
            return False
    
    def recognize_face(self, face_roi):
        """Recognize a face"""
        if not self.is_trained:
            return None, None, 0
        
        processed_face = self.preprocess_face(face_roi)
        if processed_face is None:
            return None, None, 0
        
        try:
            label_id, confidence = self.recognizer.predict(processed_face)
            
            # Convert confidence to similarity (lower confidence = higher similarity)
            # LBPH confidence: lower is better, so we invert it
            similarity = max(0, min(1, (200 - confidence) / 200))
            
            # Very lenient threshold
            if similarity > 0.2 and label_id in self.face_labels:
                student_info = self.face_labels[label_id]
                return student_info['student_id'], student_info['name'], similarity
            
            return None, None, 0
            
        except Exception as e:
            print(f"Recognition error: {e}")
            return None, None, 0
    
    def start_detection(self, camera_index=0):
        """Start camera detection with larger resolution"""
        try:
            if self.is_running:
                return True, "Detection already running"
            
            self.cap = cv2.VideoCapture(camera_index)
            if not self.cap.isOpened():
                return False, "Could not open camera"
            
            # Set larger resolution for bigger camera feed
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            self.is_running = True
            
            # Start capture thread
            self.capture_thread = threading.Thread(target=self._capture_frames)
            self.capture_thread.daemon = True
            self.capture_thread.start()
            
            # Start detection thread
            self.detection_thread = threading.Thread(target=self._detect_and_recognize)
            self.detection_thread.daemon = True
            self.detection_thread.start()
            
            return True, "Camera started successfully"
            
        except Exception as e:
            return False, f"Error starting camera: {str(e)}"
    
    def _capture_frames(self):
        """Capture frames from camera"""
        while self.is_running and self.cap:
            try:
                ret, frame = self.cap.read()
                if ret:
                    with self.thread_lock:
                        self.current_frame = frame.copy()
                time.sleep(0.03)  # ~30 FPS
            except Exception as e:
                print(f"Capture error: {e}")
                time.sleep(0.1)
    
    def _detect_and_recognize(self):
        """Detect and recognize faces"""
        while self.is_running:
            try:
                with self.thread_lock:
                    if self.current_frame is None:
                        time.sleep(0.1)
                        continue
                    frame = self.current_frame.copy()
                
                # Detect faces
                faces = self.detect_faces(frame)
                
                # Process each face
                recognized_faces = []
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                for i, (x, y, w, h) in enumerate(faces):
                    # Extract face region
                    face_roi = gray[y:y+h, x:x+w]
                    
                    # Recognize face
                    student_id, name, confidence = self.recognize_face(face_roi)
                    
                    recognized_faces.append({
                        'student_id': student_id,
                        'name': name if name else "Unknown",
                        'confidence': confidence,
                        'location': (x, y, w, h),
                        'timestamp': datetime.now()
                    })
                
                # Update detected faces
                with self.thread_lock:
                    self.detected_faces = recognized_faces
                
                time.sleep(0.1)  # Process every 100ms
                
            except Exception as e:
                print(f"Detection error: {e}")
                time.sleep(0.5)
    
    def get_current_frame_with_annotations(self):
        """Get annotated frame for display"""
        try:
            with self.thread_lock:
                if self.current_frame is None:
                    return None
                
                frame = self.current_frame.copy()
                detected_faces = self.detected_faces.copy()
            
            # Draw face annotations
            for face in detected_faces:
                x, y, w, h = face['location']
                
                # Choose color based on recognition
                if face['student_id'] and face['confidence'] > 0.2:
                    color = (0, 255, 0)  # Green for recognized
                    confidence_percent = int(face['confidence'] * 100)
                    label = f"{face['name']} ({confidence_percent}%)"
                else:
                    color = (0, 0, 255)  # Red for unknown
                    label = "Unknown Person"
                
                # Draw rectangle around face
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 3)
                
                # Draw label background
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.8
                thickness = 2
                (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, thickness)
                
                # Position label above face
                label_y = y - 15 if y > 40 else y + h + 35
                
                # Draw background rectangle for text
                cv2.rectangle(frame, (x, label_y - text_height - 10), 
                             (x + text_width + 10, label_y + 5), color, -1)
                
                # Draw text
                cv2.putText(frame, label, (x + 5, label_y - 5), 
                           font, font_scale, (255, 255, 255), thickness)
            
            return frame
            
        except Exception as e:
            print(f"Annotation error: {e}")
            return self.current_frame if self.current_frame is not None else None
    
    def stop_detection(self):
        """Stop camera detection"""
        try:
            self.is_running = False
            
            # Wait for threads to finish
            if self.capture_thread:
                self.capture_thread.join(timeout=2)
            if self.detection_thread:
                self.detection_thread.join(timeout=2)
            
            # Release camera
            if self.cap:
                self.cap.release()
                self.cap = None
            
            # Clear data
            with self.thread_lock:
                self.detected_faces = []
                self.current_frame = None
            
            return True, "Camera stopped"
            
        except Exception as e:
            return False, f"Error stopping camera: {str(e)}"
    
    def get_detected_faces(self):
        """Get currently detected faces"""
        with self.thread_lock:
            return self.detected_faces.copy()
    
    def save_face_data(self):
        """Save face data to files"""
        try:
            os.makedirs('face_data', exist_ok=True)
            
            # Save face data
            with open('face_data/enhanced_faces.pkl', 'wb') as f:
                pickle.dump(self.known_faces, f)
            
            with open('face_data/enhanced_labels.pkl', 'wb') as f:
                pickle.dump(self.face_labels, f)
            
            # Save trained model
            if self.is_trained:
                self.recognizer.save('face_data/enhanced_lbph_model.yml')
            
            print(f"💾 Saved face data for {len(self.known_faces)} students")
            
        except Exception as e:
            print(f"Save error: {e}")
    
    def load_face_data(self):
        """Load face data from files"""
        try:
            # Load face data
            if os.path.exists('face_data/enhanced_faces.pkl'):
                with open('face_data/enhanced_faces.pkl', 'rb') as f:
                    self.known_faces = pickle.load(f)
            
            if os.path.exists('face_data/enhanced_labels.pkl'):
                with open('face_data/enhanced_labels.pkl', 'rb') as f:
                    self.face_labels = pickle.load(f)
            
            # Load trained model
            if os.path.exists('face_data/enhanced_lbph_model.yml') and len(self.known_faces) > 0:
                try:
                    self.recognizer.read('face_data/enhanced_lbph_model.yml')
                    self.is_trained = True
                    print(f"📚 Loaded model with {len(self.known_faces)} known faces")
                except Exception as e:
                    print(f"Model load error: {e}")
                    self.is_trained = False
            
        except Exception as e:
            print(f"Load error: {e}")
            self.known_faces = {}
            self.face_labels = {}
            self.is_trained = False
    
    def remove_student_face(self, student_id):
        """Remove student face data"""
        try:
            if student_id in self.known_faces:
                label_id = self.known_faces[student_id]['label_id']
                del self.known_faces[student_id]
                if label_id in self.face_labels:
                    del self.face_labels[label_id]
                
                if len(self.known_faces) > 0:
                    self.train_recognizer()
                else:
                    self.is_trained = False
                
                self.save_face_data()
                return True, f"Removed face data for student {student_id}"
            else:
                return False, f"No face data found for student {student_id}"
                
        except Exception as e:
            return False, f"Error removing face: {str(e)}"
    
    def get_recognition_stats(self):
        """Get system statistics"""
        return {
            'total_students': len(self.known_faces),
            'total_face_samples': sum(len(face_data['images']) for face_data in self.known_faces.values()),
            'is_running': self.is_running,
            'is_trained': self.is_trained,
            'current_detections': len(self.detected_faces),
            'system_type': 'Enhanced Face Recognition v2.0'
        }