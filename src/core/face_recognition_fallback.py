import cv2
import numpy as np
import os
import pickle
from datetime import datetime
import threading
import time

class FallbackFaceRecognition:
    """Fallback face recognition using OpenCV's built-in methods"""
    
    def __init__(self):
        print("Initializing Fallback Face Recognition System...")
        
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
        
        # Load existing face data
        self.load_face_data()
        
        print(f"Fallback Face Recognition System initialized")
    
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
            
            # Detect faces
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) == 0:
                return False, "No face detected in image"
            
            # Use the largest face
            largest_face = max(faces, key=lambda f: f[2] * f[3])
            x, y, w, h = largest_face
            
            # Extract face region
            face_roi = gray[y:y+h, x:x+w]
            face_roi = cv2.resize(face_roi, (200, 200))
            
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
                self.known_faces[student_id]['images'].append(face_roi)
            
            # Retrain recognizer
            self.train_recognizer()
            self.save_face_data()
            
            return True, f"Face registered successfully for {student_name}"
            
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
                print(f"Trained recognizer with {len(faces)} face samples")
                return True
            
            return False
            
        except Exception as e:
            print(f"Error training recognizer: {e}")
            return False
    
    def save_face_data(self):
        """Save face data to files"""
        try:
            os.makedirs('face_data', exist_ok=True)
            
            with open('face_data/fallback_faces.pkl', 'wb') as f:
                pickle.dump(self.known_faces, f)
            
            with open('face_data/fallback_labels.pkl', 'wb') as f:
                pickle.dump(self.face_labels, f)
            
            if self.is_trained:
                self.face_recognizer.save('face_data/fallback_model.yml')
            
        except Exception as e:
            print(f"Error saving face data: {e}")
    
    def load_face_data(self):
        """Load face data from files"""
        try:
            if os.path.exists('face_data/fallback_faces.pkl'):
                with open('face_data/fallback_faces.pkl', 'rb') as f:
                    self.known_faces = pickle.load(f)
            
            if os.path.exists('face_data/fallback_labels.pkl'):
                with open('face_data/fallback_labels.pkl', 'rb') as f:
                    self.face_labels = pickle.load(f)
            
            if os.path.exists('face_data/fallback_model.yml') and len(self.known_faces) > 0:
                try:
                    self.face_recognizer.read('face_data/fallback_model.yml')
                    self.is_trained = True
                except:
                    self.is_trained = False
            
            print(f"Loaded {len(self.known_faces)} known faces")
            
        except Exception as e:
            print(f"Error loading face data: {e}")
    
    def start_detection(self, camera_index=0):
        """Start face detection"""
        try:
            if self.is_running:
                return True, "Detection already running"
            
            self.cap = cv2.VideoCapture(camera_index)
            if not self.cap.isOpened():
                return False, "Could not open camera"
            
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
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
                faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
                
                detected_faces_data = []
                
                for (x, y, w, h) in faces:
                    face_roi = gray[y:y+h, x:x+w]
                    face_roi = cv2.resize(face_roi, (200, 200))
                    
                    student_id = None
                    name = "Unknown"
                    confidence = 0
                    
                    if self.is_trained:
                        try:
                            label_id, conf = self.face_recognizer.predict(face_roi)
                            
                            if conf < 100:  # Lower is better for LBPH
                                confidence = max(0, (100 - conf) / 100)
                                
                                if confidence > 0.4 and label_id in self.face_labels:
                                    student_info = self.face_labels[label_id]
                                    student_id = student_info['student_id']
                                    name = student_info['name']
                        except:
                            pass
                    
                    detected_faces_data.append({
                        'student_id': student_id,
                        'name': name,
                        'confidence': confidence,
                        'location': (x, y, w, h),
                        'timestamp': datetime.now()
                    })
                
                with self.thread_lock:
                    self.detected_faces = detected_faces_data
                
                time.sleep(0.2)
                
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
                
                if face['student_id']:
                    color = (0, 255, 0)  # Green
                    label = f"{face['name']} ({face['confidence']:.1%})"
                else:
                    color = (0, 0, 255)  # Red
                    label = "Unknown"
                
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                cv2.rectangle(frame, (x, y-30), (x+w, y), color, -1)
                cv2.putText(frame, label, (x+5, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
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
            'current_detections': len(self.detected_faces)
        }