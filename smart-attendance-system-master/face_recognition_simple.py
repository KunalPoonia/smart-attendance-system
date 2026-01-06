import cv2
import numpy as np
import os
import pickle
from datetime import datetime
import threading
import time
try:
    import face_recognition
except ImportError:
    raise ImportError("face_recognition library not available. Install with: pip install face-recognition")

class SimpleFaceRecognition:
    """Simple and reliable face recognition system using face_recognition library"""
    
    def __init__(self):
        print("Initializing Simple Face Recognition System...")
        
        # Camera and detection state
        self.cap = None
        self.is_running = False
        self.current_frame = None
        self.detected_faces = []
        
        # Face data storage
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        
        # Threading
        self.capture_thread = None
        self.detection_thread = None
        self.thread_lock = threading.Lock()
        
        # Detection settings
        self.confidence_threshold = 0.6
        self.face_locations = []
        self.face_encodings = []
        self.face_names = []
        
        # Load existing face data
        self.load_face_data()
        
        print(f"Face Recognition System initialized with {len(self.known_face_names)} known faces")
    
    def add_student_face(self, student_id, student_name, image_path):
        """Add a new student's face to the recognition system"""
        try:
            print(f"Adding face for {student_name} (ID: {student_id}) from {image_path}")
            
            # Check if image exists
            if not os.path.exists(image_path):
                return False, f"Image file not found: {image_path}"
            
            # Load image
            image = face_recognition.load_image_file(image_path)
            
            # Find face encodings
            face_encodings = face_recognition.face_encodings(image)
            
            if len(face_encodings) == 0:
                return False, "No face found in the image. Please use a clear photo with a visible face."
            
            if len(face_encodings) > 1:
                print(f"Warning: Multiple faces found, using the first one")
            
            # Use the first face encoding
            face_encoding = face_encodings[0]
            
            # Remove existing entry for this student if it exists
            self.remove_student_face(student_id)
            
            # Add new face data
            self.known_face_encodings.append(face_encoding)
            self.known_face_names.append(student_name)
            self.known_face_ids.append(student_id)
            
            # Save the updated data
            self.save_face_data()
            
            print(f"Successfully added face for {student_name}")
            return True, f"Face registered successfully for {student_name}"
            
        except Exception as e:
            print(f"Error adding face: {e}")
            return False, f"Error processing image: {str(e)}"
    
    def remove_student_face(self, student_id):
        """Remove a student's face from the system"""
        try:
            # Find and remove the student's data
            indices_to_remove = []
            for i, face_id in enumerate(self.known_face_ids):
                if face_id == student_id:
                    indices_to_remove.append(i)
            
            # Remove in reverse order to maintain indices
            for i in reversed(indices_to_remove):
                del self.known_face_encodings[i]
                del self.known_face_names[i]
                del self.known_face_ids[i]
            
            if indices_to_remove:
                self.save_face_data()
                return True, f"Removed face data for student {student_id}"
            else:
                return False, f"No face data found for student {student_id}"
                
        except Exception as e:
            print(f"Error removing face: {e}")
            return False, f"Error removing face: {str(e)}"
    
    def save_face_data(self):
        """Save face data to files"""
        try:
            os.makedirs('face_data', exist_ok=True)
            
            face_data = {
                'encodings': self.known_face_encodings,
                'names': self.known_face_names,
                'ids': self.known_face_ids
            }
            
            with open('face_data/face_data.pkl', 'wb') as f:
                pickle.dump(face_data, f)
            
            print(f"Saved face data for {len(self.known_face_names)} students")
            
        except Exception as e:
            print(f"Error saving face data: {e}")
    
    def load_face_data(self):
        """Load face data from files"""
        try:
            if os.path.exists('face_data/face_data.pkl'):
                with open('face_data/face_data.pkl', 'rb') as f:
                    face_data = pickle.load(f)
                
                self.known_face_encodings = face_data.get('encodings', [])
                self.known_face_names = face_data.get('names', [])
                self.known_face_ids = face_data.get('ids', [])
                
                print(f"Loaded face data for {len(self.known_face_names)} students")
            else:
                print("No existing face data found")
                
        except Exception as e:
            print(f"Error loading face data: {e}")
            self.known_face_encodings = []
            self.known_face_names = []
            self.known_face_ids = []
    
    def start_detection(self, camera_index=0):
        """Start face detection"""
        try:
            if self.is_running:
                return True, "Detection already running"
            
            # Initialize camera
            self.cap = cv2.VideoCapture(camera_index)
            if not self.cap.isOpened():
                return False, "Could not open camera"
            
            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            self.is_running = True
            
            # Start threads
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
            
            # Wait for threads to finish
            if self.capture_thread:
                self.capture_thread.join(timeout=2)
            if self.detection_thread:
                self.detection_thread.join(timeout=2)
            
            # Release camera
            if self.cap:
                self.cap.release()
                self.cap = None
            
            # Clear detection data
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
        process_this_frame = True
        
        while self.is_running:
            try:
                with self.thread_lock:
                    if self.current_frame is None:
                        time.sleep(0.1)
                        continue
                    frame = self.current_frame.copy()
                
                # Process every other frame for better performance
                if process_this_frame:
                    # Resize frame for faster processing
                    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                    rgb_small_frame = small_frame[:, :, ::-1]  # Convert BGR to RGB
                    
                    # Find faces
                    self.face_locations = face_recognition.face_locations(rgb_small_frame)
                    self.face_encodings = face_recognition.face_encodings(rgb_small_frame, self.face_locations)
                    
                    self.face_names = []
                    detected_faces_data = []
                    
                    for face_encoding in self.face_encodings:
                        # Compare with known faces
                        matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                        name = "Unknown"
                        student_id = None
                        confidence = 0
                        
                        # Calculate face distances
                        face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                        
                        if len(face_distances) > 0:
                            best_match_index = np.argmin(face_distances)
                            
                            if matches[best_match_index] and face_distances[best_match_index] < 0.6:
                                name = self.known_face_names[best_match_index]
                                student_id = self.known_face_ids[best_match_index]
                                confidence = 1 - face_distances[best_match_index]  # Convert distance to confidence
                        
                        self.face_names.append(name)
                        
                        # Add to detected faces data
                        detected_faces_data.append({
                            'student_id': student_id,
                            'name': name,
                            'confidence': confidence,
                            'timestamp': datetime.now()
                        })
                    
                    # Update detected faces
                    with self.thread_lock:
                        self.detected_faces = detected_faces_data
                
                process_this_frame = not process_this_frame
                time.sleep(0.1)  # Small delay to prevent excessive CPU usage
                
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
            
            # Draw face rectangles and labels
            for (top, right, bottom, left), name in zip(self.face_locations, self.face_names):
                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                
                # Choose color based on recognition
                if name != "Unknown":
                    color = (0, 255, 0)  # Green for recognized
                    # Find confidence for this face
                    confidence = 0
                    for face_data in self.detected_faces:
                        if face_data['name'] == name:
                            confidence = face_data['confidence']
                            break
                    label = f"{name} ({confidence:.1%})"
                else:
                    color = (0, 0, 255)  # Red for unknown
                    label = "Unknown"
                
                # Draw rectangle around face
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                
                # Draw label
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, label, (left + 6, bottom - 6), font, 0.6, (255, 255, 255), 1)
            
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
            'total_students': len(self.known_face_names),
            'is_running': self.is_running,
            'confidence_threshold': self.confidence_threshold,
            'current_detections': len(self.detected_faces)
        }