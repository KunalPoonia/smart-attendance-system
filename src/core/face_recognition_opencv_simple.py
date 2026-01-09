import cv2
import numpy as np
import os
import pickle
from datetime import datetime
import threading
import time

class OpenCVSimpleFaceRecognition:
    """Simple and reliable face recognition using only OpenCV"""
    
    def __init__(self):
        print("Initializing OpenCV Simple Face Recognition System...")
        
        # Load face cascade
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Initialize LBPH face recognizer
        self.face_recognizer = cv2.face.LBPHFaceRecognizer_create()
        
        # Camera and detection state
        self.cap = None
        self.is_running = False
        self.current_frame = None
        self.detected_faces = []
        
        # Face data storage
        self.known_faces = {}  # {student_id: {'name': name, 'images': [face_images]}}
        self.face_labels = {}  # {label_id: {'student_id': id, 'name': name}}
        self.is_trained = False
        
        # Threading
        self.capture_thread = None
        self.detection_thread = None
        self.thread_lock = threading.Lock()
        
        # Detection settings
        self.confidence_threshold = 80  # LBPH confidence threshold (lower is better)
        
        # Load existing face data
        self.load_face_data()
        
        print(f"OpenCV Simple Face Recognition System initialized with {len(self.known_faces)} known faces")
    
    def add_student_face(self, student_id, student_name, image_path):
        """Add a new student's face to the recognition system"""
        try:
            print(f"Adding face for {student_name} (ID: {student_id}) from {image_path}")
            
            # Check if image exists
            if not os.path.exists(image_path):
                return False, f"Image file not found: {image_path}"
            
            # Load and process image
            image = cv2.imread(image_path)
            if image is None:
                return False, "Could not load image"
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces with more lenient parameters
            faces = self.face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1, 
                minNeighbors=3,
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            if len(faces) == 0:
                return False, "No face detected in image. Please use a clear photo with a visible face."
            
            # Use the largest face
            largest_face = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = largest_face
            
            # Extract and preprocess face region
            face_roi = gray[y:y+h, x:x+w]
            face_roi = cv2.resize(face_roi, (200, 200))
            
            # Apply histogram equalization for better recognition
            face_roi = cv2.equalizeHist(face_roi)
            
            # Store face data
            if student_id not in self.known_faces:
                label_id = len(self.face_labels)
                self.known_faces[student_id] = {
                    'name': student_name,
                    'label_id': label_id,
                    'images': [face_roi]
                }
                self.face_labels[label_id] = {
                    'student_id': student_id,
                    'name': student_name
                }
            else:
                # Update existing entry
                self.known_faces[student_id]['name'] = student_name
                self.known_faces[student_id]['images'].append(face_roi)
                # Keep only the most recent 5 images
                self.known_faces[student_id]['images'] = self.known_faces[student_id]['images'][-5:]
            
            # Retrain recognizer
            success = self.train_recognizer()
            if success:
                self.save_face_data()
                return True, f"Face registered successfully for {student_name}"
            else:
                return False, "Failed to train face recognizer"
            
        except Exception as e:
            print(f"Error adding face: {e}")
            return False, f"Error processing image: {str(e)}"
    
    def remove_student_face(self, student_id):
        """Remove a student's face from the system"""
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
            
            if len(faces) > 0:
                self.face_recognizer.train(faces, np.array(labels))
                self.is_trained = True
                print(f"Trained recognizer with {len(faces)} face samples from {len(self.known_faces)} students")
                return True
            
            return False
            
        except Exception as e:
            print(f"Error training recognizer: {e}")
            return False
    
    def save_face_data(self):
        """Save face data to files"""
        try:
            os.makedirs('face_data', exist_ok=True)
            
            with open('face_data/opencv_faces.pkl', 'wb') as f:
                pickle.dump(self.known_faces, f)
            
            with open('face_data/opencv_labels.pkl', 'wb') as f:
                pickle.dump(self.face_labels, f)
            
            if self.is_trained:
                self.face_recognizer.save('face_data/opencv_model.yml')
            
            print(f"Saved face data for {len(self.known_faces)} students")
            
        except Exception as e:
            print(f"Error saving face data: {e}")
    
    def load_face_data(self):
        """Load face data from files"""
        try:
            if os.path.exists('face_data/opencv_faces.pkl'):
                with open('face_data/opencv_faces.pkl', 'rb') as f:
                    self.known_faces = pickle.load(f)
            
            if os.path.exists('face_data/opencv_labels.pkl'):
                with open('face_data/opencv_labels.pkl', 'rb') as f:
                    self.face_labels = pickle.load(f)
            
            if os.path.exists('face_data/opencv_model.yml') and len(self.known_faces) > 0:
                try:
                    self.face_recognizer.read('face_data/opencv_model.yml')
                    self.is_trained = True
                    print(f"Loaded face model with {len(self.known_faces)} known faces")
                except Exception as e:
                    print(f"Error loading face model: {e}")
                    self.is_trained = False
            
        except Exception as e:
            print(f"Error loading face data: {e}")
            self.known_faces = {}
            self.face_labels = {}
            self.is_trained = False
    
    def start_detection(self, camera_index=0):
        """Start face detection"""
        try:
            if self.is_running:
                return True, "Detection already running"
            
            self.cap = cv2.VideoCapture(camera_index)
            if not self.cap.isOpened():
                return False, "Could not open camera"
            
            # Set camera properties for better performance
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            self.is_running = True
            
            self.capture_thread = threading.Thread(target=self._capture_frames)
            self.capture_thread.daemon = True
            self.capture_thread.start()
            
            self.detection_thread = threading.Thread(target=self._detect_faces)
            self.detection_thread.daemon = True
            self.detection_thread.start()
            
            return True, "Face detection started successfully"
            
        except Exception as e:
            return False, f"Error starting detection: {str(e)}"
    
    def stop_detection(self):
        """Stop face detection"""
        try:
            self.is_running = False
            
            if self.capture_thread:
                self.capture_thread.join(timeout=2)
            if self.detection_thread:
                self.detection_thread.join(timeout=2)
            
            if self.cap:
                self.cap.release()
                self.cap = None
            
            with self.thread_lock:
                self.detected_faces = []
                self.current_frame = None
            
            return True, "Face detection stopped"
            
        except Exception as e:
            return False, f"Error stopping detection: {str(e)}"
    
    def _capture_frames(self):
        """Capture frames from camera"""
        while self.is_running and self.cap:
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
        """Detect and recognize faces"""
        while self.is_running:
            try:
                with self.thread_lock:
                    if self.current_frame is None:
                        time.sleep(0.1)
                        continue
                    frame = self.current_frame.copy()
                
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Detect faces
                faces = self.face_cascade.detectMultiScale(
                    gray, 
                    scaleFactor=1.1, 
                    minNeighbors=5,
                    minSize=(50, 50),
                    flags=cv2.CASCADE_SCALE_IMAGE
                )
                
                detected_faces_data = []
                
                for (x, y, w, h) in faces:
                    # Extract and preprocess face
                    face_roi = gray[y:y+h, x:x+w]
                    face_roi = cv2.resize(face_roi, (200, 200))
                    face_roi = cv2.equalizeHist(face_roi)
                    
                    student_id = None
                    name = "Unknown"
                    confidence = 0
                    
                    if self.is_trained and len(self.known_faces) > 0:
                        try:
                            label_id, conf = self.face_recognizer.predict(face_roi)
                            
                            # LBPH confidence: lower is better, typically 0-100+
                            if conf < self.confidence_threshold and label_id in self.face_labels:
                                student_info = self.face_labels[label_id]
                                student_id = student_info['student_id']
                                name = student_info['name']
                                # Convert LBPH confidence to percentage (lower conf = higher confidence)
                                confidence = max(0, (self.confidence_threshold - conf) / self.confidence_threshold)
                        except Exception as e:
                            print(f"Recognition error: {e}")
                    
                    detected_faces_data.append({
                        'student_id': student_id,
                        'name': name,
                        'confidence': confidence,
                        'location': (x, y, w, h),
                        'timestamp': datetime.now()
                    })
                
                with self.thread_lock:
                    self.detected_faces = detected_faces_data
                
                time.sleep(0.2)  # Reasonable detection interval
                
            except Exception as e:
                print(f"Error in face detection: {e}")
                time.sleep(0.5)
    
    def get_current_frame_with_annotations(self):
        """Get current frame with face detection annotations"""
        try:
            with self.thread_lock:
                if self.current_frame is None:
                    return None
                
                frame = self.current_frame.copy()
                detected_faces = self.detected_faces.copy()
            
            for face in detected_faces:
                x, y, w, h = face['location']
                
                if face['student_id'] and face['confidence'] > 0.3:
                    color = (0, 255, 0)  # Green for recognized
                    confidence_percent = int(face['confidence'] * 100)
                    label = f"{face['name']} ({confidence_percent}%)"
                else:
                    color = (0, 0, 255)  # Red for unknown
                    label = "Unknown"
                
                # Draw rectangle around face
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 3)
                
                # Calculate text size for background
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.7
                thickness = 2
                (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, thickness)
                
                # Draw label background
                cv2.rectangle(frame, (x, y-text_height-10), (x+text_width+10, y), color, -1)
                
                # Draw label text
                cv2.putText(frame, label, (x+5, y-5), font, font_scale, (255, 255, 255), thickness)
                
                # Add center dot
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
    
    def get_recognition_stats(self):
        """Get statistics about the face recognition system"""
        return {
            'total_students': len(self.known_faces),
            'is_running': self.is_running,
            'is_trained': self.is_trained,
            'confidence_threshold': self.confidence_threshold,
            'current_detections': len(self.detected_faces)
        }