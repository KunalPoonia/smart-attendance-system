import cv2
import numpy as np
import os
import pickle
from datetime import datetime
import threading
import time
import logging

class AdvancedFaceDetection:
    """Advanced face detection system with multiple detection methods and improved accuracy"""
    
    def __init__(self):
        print("Initializing Advanced Face Detection System...")
        
        # Initialize multiple face detection methods for better accuracy
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.profile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_profileface.xml')
        
        # Try to load DNN face detector for better accuracy
        self.dnn_net = None
        try:
            # Load DNN model for face detection (more accurate than Haar cascades)
            model_path = os.path.join(os.path.dirname(__file__), 'models')
            prototxt_path = os.path.join(model_path, 'deploy.prototxt')
            model_weights_path = os.path.join(model_path, 'res10_300x300_ssd_iter_140000.caffemodel')
            
            if os.path.exists(prototxt_path) and os.path.exists(model_weights_path):
                self.dnn_net = cv2.dnn.readNetFromCaffe(prototxt_path, model_weights_path)
                print("✅ DNN face detector loaded for enhanced accuracy")
            else:
                print("⚠️  DNN models not found, using Haar cascades")
        except Exception as e:
            print(f"⚠️  Could not load DNN face detector: {e}")
        
        # Initialize LBPH face recognizer with optimized parameters
        self.face_recognizer = cv2.face.LBPHFaceRecognizer_create(
            radius=2,           # Increased radius for better feature extraction
            neighbors=8,        # Standard neighbors
            grid_x=8,          # Grid size
            grid_y=8,
            threshold=80.0      # Confidence threshold
        )
        
        # Camera and detection state
        self.cap = None
        self.is_running = False
        self.current_frame = None
        self.detected_faces = []
        
        # Face data storage with enhanced structure
        self.known_faces = {}  # {student_id: {'name': name, 'encodings': [face_encodings], 'images': [preprocessed_images]}}
        self.face_labels = {}  # {label_id: {'student_id': id, 'name': name}}
        self.is_trained = False
        
        # Threading
        self.capture_thread = None
        self.detection_thread = None
        self.thread_lock = threading.Lock()
        
        # Enhanced detection parameters
        self.detection_params = {
            'confidence_threshold': 70,      # LBPH confidence threshold
            'min_face_size': (60, 60),      # Minimum face size
            'max_face_size': (400, 400),    # Maximum face size
            'scale_factor': 1.1,            # Scale factor for detection
            'min_neighbors': 4,             # Minimum neighbors for detection
            'detection_interval': 0.15,     # Detection interval in seconds
            'nms_threshold': 0.4,           # Non-maximum suppression threshold
        }
        
        # Face tracking for stability
        self.face_tracker = {}
        self.next_face_id = 0
        
        # Load existing face data
        self.load_face_data()
        
        print(f"Advanced Face Detection System initialized with {len(self.known_faces)} known faces")
    
    def detect_faces_haar(self, gray_frame):
        """Detect faces using Haar cascades"""
        faces = []
        
        # Frontal face detection
        frontal_faces = self.face_cascade.detectMultiScale(
            gray_frame,
            scaleFactor=self.detection_params['scale_factor'],
            minNeighbors=self.detection_params['min_neighbors'],
            minSize=self.detection_params['min_face_size'],
            maxSize=self.detection_params['max_face_size'],
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        for (x, y, w, h) in frontal_faces:
            faces.append((x, y, w, h, 'frontal'))
        
        # Profile face detection (optional, for side faces)
        try:
            profile_faces = self.profile_cascade.detectMultiScale(
                gray_frame,
                scaleFactor=1.2,
                minNeighbors=3,
                minSize=(50, 50),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            for (x, y, w, h) in profile_faces:
                faces.append((x, y, w, h, 'profile'))
        except:
            pass  # Profile detection is optional
        
        return faces
    
    def detect_faces_dnn(self, frame):
        """Detect faces using DNN (more accurate)"""
        if self.dnn_net is None:
            return []
        
        faces = []
        h, w = frame.shape[:2]
        
        # Create blob from image
        blob = cv2.dnn.blobFromImage(frame, 1.0, (300, 300), [104, 117, 123])
        self.dnn_net.setInput(blob)
        detections = self.dnn_net.forward()
        
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            
            if confidence > 0.5:  # Confidence threshold for DNN
                x1 = int(detections[0, 0, i, 3] * w)
                y1 = int(detections[0, 0, i, 4] * h)
                x2 = int(detections[0, 0, i, 5] * w)
                y2 = int(detections[0, 0, i, 6] * h)
                
                # Convert to (x, y, w, h) format
                x, y, w, h = x1, y1, x2 - x1, y2 - y1
                
                # Filter by size
                if (w >= self.detection_params['min_face_size'][0] and 
                    h >= self.detection_params['min_face_size'][1] and
                    w <= self.detection_params['max_face_size'][0] and 
                    h <= self.detection_params['max_face_size'][1]):
                    faces.append((x, y, w, h, 'dnn', confidence))
        
        return faces
    
    def apply_nms(self, faces):
        """Apply Non-Maximum Suppression to remove overlapping detections"""
        if len(faces) <= 1:
            return faces
        
        boxes = []
        confidences = []
        
        for face in faces:
            x, y, w, h = face[:4]
            boxes.append([x, y, w, h])
            # Use confidence if available, otherwise use a default value
            conf = face[5] if len(face) > 5 else 0.8
            confidences.append(float(conf))
        
        # Apply NMS
        indices = cv2.dnn.NMSBoxes(
            boxes, 
            confidences, 
            0.5,  # Score threshold
            self.detection_params['nms_threshold']
        )
        
        filtered_faces = []
        if len(indices) > 0:
            for i in indices.flatten():
                filtered_faces.append(faces[i])
        
        return filtered_faces
    
    def preprocess_face(self, gray_face):
        """Enhanced face preprocessing for better recognition"""
        # Resize to standard size
        face_resized = cv2.resize(gray_face, (200, 200))
        
        # Apply histogram equalization
        face_equalized = cv2.equalizeHist(face_resized)
        
        # Apply Gaussian blur to reduce noise
        face_blurred = cv2.GaussianBlur(face_equalized, (3, 3), 0)
        
        # Normalize pixel values
        face_normalized = cv2.normalize(face_blurred, None, 0, 255, cv2.NORM_MINMAX)
        
        return face_normalized
    
    def add_student_face(self, student_id, student_name, image_path):
        """Add a new student's face with enhanced preprocessing"""
        try:
            print(f"Adding face for {student_name} (ID: {student_id}) from {image_path}")
            
            if not os.path.exists(image_path):
                return False, f"Image file not found: {image_path}"
            
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return False, "Could not load image"
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Try DNN detection first, then Haar cascades
            faces = self.detect_faces_dnn(image)
            if not faces:
                faces = self.detect_faces_haar(gray)
            
            if len(faces) == 0:
                return False, "No face detected in image. Please use a clear photo with a visible face."
            
            # Use the largest/most confident face
            if len(faces[0]) > 5:  # DNN detection with confidence
                best_face = max(faces, key=lambda f: f[5])  # Highest confidence
            else:  # Haar detection
                best_face = max(faces, key=lambda f: f[2] * f[3])  # Largest area
            
            x, y, w, h = best_face[:4]
            
            # Extract face region with padding
            padding = int(0.1 * min(w, h))
            x_pad = max(0, x - padding)
            y_pad = max(0, y - padding)
            w_pad = min(gray.shape[1] - x_pad, w + 2 * padding)
            h_pad = min(gray.shape[0] - y_pad, h + 2 * padding)
            
            face_roi = gray[y_pad:y_pad+h_pad, x_pad:x_pad+w_pad]
            
            # Preprocess face
            processed_face = self.preprocess_face(face_roi)
            
            # Create multiple variations for better training
            face_variations = [processed_face]
            
            # Add slight variations
            # Brightness variation
            bright_face = cv2.convertScaleAbs(processed_face, alpha=1.1, beta=10)
            face_variations.append(bright_face)
            
            # Contrast variation
            contrast_face = cv2.convertScaleAbs(processed_face, alpha=1.2, beta=0)
            face_variations.append(contrast_face)
            
            # Store face data
            if student_id not in self.known_faces:
                label_id = len(self.face_labels)
                self.known_faces[student_id] = {
                    'name': student_name,
                    'label_id': label_id,
                    'images': face_variations,
                    'original_image': image_path
                }
                self.face_labels[label_id] = {
                    'student_id': student_id,
                    'name': student_name
                }
            else:
                # Update existing entry
                self.known_faces[student_id]['name'] = student_name
                self.known_faces[student_id]['images'].extend(face_variations)
                # Keep only the most recent 10 images
                self.known_faces[student_id]['images'] = self.known_faces[student_id]['images'][-10:]
            
            # Retrain recognizer
            success = self.train_recognizer()
            if success:
                self.save_face_data()
                return True, f"Face registered successfully for {student_name} with {len(face_variations)} training samples"
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
        """Train the face recognizer with enhanced data"""
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
            
            with open('face_data/advanced_faces.pkl', 'wb') as f:
                pickle.dump(self.known_faces, f)
            
            with open('face_data/advanced_labels.pkl', 'wb') as f:
                pickle.dump(self.face_labels, f)
            
            if self.is_trained:
                self.face_recognizer.save('face_data/advanced_model.yml')
            
            print(f"Saved face data for {len(self.known_faces)} students")
            
        except Exception as e:
            print(f"Error saving face data: {e}")
    
    def load_face_data(self):
        """Load face data from files"""
        try:
            if os.path.exists('face_data/advanced_faces.pkl'):
                with open('face_data/advanced_faces.pkl', 'rb') as f:
                    self.known_faces = pickle.load(f)
            
            if os.path.exists('face_data/advanced_labels.pkl'):
                with open('face_data/advanced_labels.pkl', 'rb') as f:
                    self.face_labels = pickle.load(f)
            
            if os.path.exists('face_data/advanced_model.yml') and len(self.known_faces) > 0:
                try:
                    self.face_recognizer.read('face_data/advanced_model.yml')
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
        """Start enhanced face detection"""
        try:
            if self.is_running:
                return True, "Detection already running"
            
            self.cap = cv2.VideoCapture(camera_index)
            if not self.cap.isOpened():
                return False, "Could not open camera"
            
            # Set optimal camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Reduce buffer lag
            
            self.is_running = True
            
            # Reset face tracker
            self.face_tracker = {}
            self.next_face_id = 0
            
            self.capture_thread = threading.Thread(target=self._capture_frames)
            self.capture_thread.daemon = True
            self.capture_thread.start()
            
            self.detection_thread = threading.Thread(target=self._detect_faces)
            self.detection_thread.daemon = True
            self.detection_thread.start()
            
            return True, "Enhanced face detection started successfully"
            
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
                self.face_tracker = {}
            
            return True, "Face detection stopped"
            
        except Exception as e:
            return False, f"Error stopping detection: {str(e)}"
    
    def _capture_frames(self):
        """Capture frames from camera with optimization"""
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
        """Enhanced face detection and recognition"""
        while self.is_running:
            try:
                with self.thread_lock:
                    if self.current_frame is None:
                        time.sleep(0.1)
                        continue
                    frame = self.current_frame.copy()
                
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Use DNN detection if available, otherwise Haar cascades
                if self.dnn_net is not None:
                    faces = self.detect_faces_dnn(frame)
                else:
                    faces = self.detect_faces_haar(gray)
                
                # Apply Non-Maximum Suppression
                faces = self.apply_nms(faces)
                
                detected_faces_data = []
                
                for face in faces:
                    x, y, w, h = face[:4]
                    
                    # Extract and preprocess face
                    face_roi = gray[y:y+h, x:x+w]
                    processed_face = self.preprocess_face(face_roi)
                    
                    student_id = None
                    name = "Unknown"
                    confidence = 0
                    
                    if self.is_trained and len(self.known_faces) > 0:
                        try:
                            label_id, conf = self.face_recognizer.predict(processed_face)
                            
                            # LBPH confidence: lower is better
                            if conf < self.detection_params['confidence_threshold'] and label_id in self.face_labels:
                                student_info = self.face_labels[label_id]
                                student_id = student_info['student_id']
                                name = student_info['name']
                                # Convert LBPH confidence to percentage
                                confidence = max(0, (self.detection_params['confidence_threshold'] - conf) / self.detection_params['confidence_threshold'])
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
                
                time.sleep(self.detection_params['detection_interval'])
                
            except Exception as e:
                print(f"Error in face detection: {e}")
                time.sleep(0.5)
    
    def get_current_frame_with_annotations(self):
        """Get current frame with enhanced annotations"""
        try:
            with self.thread_lock:
                if self.current_frame is None:
                    return None
                
                frame = self.current_frame.copy()
                detected_faces = self.detected_faces.copy()
            
            for face in detected_faces:
                x, y, w, h = face['location']
                
                # Choose color and style based on recognition
                if face['student_id'] and face['confidence'] > 0.4:
                    color = (0, 255, 0)  # Green for recognized
                    confidence_percent = int(face['confidence'] * 100)
                    label = f"{face['name']} ({confidence_percent}%)"
                    thickness = 3
                else:
                    color = (0, 0, 255)  # Red for unknown
                    label = "Unknown Person"
                    thickness = 2
                
                # Draw main rectangle
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, thickness)
                
                # Draw corner markers for better visibility
                corner_length = 20
                corner_thickness = 3
                
                # Top-left corner
                cv2.line(frame, (x, y), (x + corner_length, y), color, corner_thickness)
                cv2.line(frame, (x, y), (x, y + corner_length), color, corner_thickness)
                
                # Top-right corner
                cv2.line(frame, (x + w, y), (x + w - corner_length, y), color, corner_thickness)
                cv2.line(frame, (x + w, y), (x + w, y + corner_length), color, corner_thickness)
                
                # Bottom-left corner
                cv2.line(frame, (x, y + h), (x + corner_length, y + h), color, corner_thickness)
                cv2.line(frame, (x, y + h), (x, y + h - corner_length), color, corner_thickness)
                
                # Bottom-right corner
                cv2.line(frame, (x + w, y + h), (x + w - corner_length, y + h), color, corner_thickness)
                cv2.line(frame, (x + w, y + h), (x + w, y + h - corner_length), color, corner_thickness)
                
                # Calculate text size and position
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.7
                text_thickness = 2
                (text_width, text_height), baseline = cv2.getTextSize(label, font, font_scale, text_thickness)
                
                # Draw label background with rounded corners effect
                label_y = y - 10 if y > 30 else y + h + 30
                cv2.rectangle(frame, (x, label_y - text_height - 10), (x + text_width + 10, label_y + 5), color, -1)
                
                # Draw label text
                cv2.putText(frame, label, (x + 5, label_y - 5), font, font_scale, (255, 255, 255), text_thickness)
                
                # Add center dot for precise location
                center_x = x + w // 2
                center_y = y + h // 2
                cv2.circle(frame, (center_x, center_y), 4, color, -1)
                cv2.circle(frame, (center_x, center_y), 6, (255, 255, 255), 1)
            
            # Add system info overlay
            info_text = f"Faces: {len(detected_faces)} | System: Advanced Detection"
            cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
            
            return frame
            
        except Exception as e:
            print(f"Error annotating frame: {e}")
            return self.current_frame if self.current_frame is not None else None
    
    def get_detected_faces(self):
        """Get currently detected faces"""
        with self.thread_lock:
            return self.detected_faces.copy()
    
    def get_recognition_stats(self):
        """Get detailed statistics about the face recognition system"""
        return {
            'total_students': len(self.known_faces),
            'total_face_samples': sum(len(face_data['images']) for face_data in self.known_faces.values()),
            'is_running': self.is_running,
            'is_trained': self.is_trained,
            'confidence_threshold': self.detection_params['confidence_threshold'],
            'current_detections': len(self.detected_faces),
            'detection_method': 'DNN + Haar' if self.dnn_net else 'Haar Cascades',
            'has_dnn': self.dnn_net is not None
        }