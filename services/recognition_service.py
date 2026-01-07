import logging
import os
try:
    from face_recognition.face_encoder import FaceEncoder
    from face_recognition.face_detector import FaceDetector
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    FaceEncoder = None
    FaceDetector = None

class RecognitionService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RecognitionService, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
            
        self.logger = logging.getLogger(__name__)
        self.encoder = None
        self.detector = None
        self.is_active = False
        self.known_faces = []
        
        if FACE_RECOGNITION_AVAILABLE:
            try:
                # Tolerance might be loaded from config later, using default 0.6
                self.encoder = FaceEncoder(tolerance=0.6)
                self.detector = FaceDetector(camera_index=0, tolerance=0.6)
            except Exception as e:
                self.logger.error(f"Failed to init face recognition modules: {e}")
                self.encoder = None
                self.detector = None
        
        self.initialized = True

    def is_available(self):
        return FACE_RECOGNITION_AVAILABLE and self.encoder is not None and self.detector is not None

    def encode_from_image(self, image_path):
        if not self.is_available():
            return None
        return self.encoder.encode_face_from_image(image_path)

    def start_detection(self, known_students_data):
        if not self.is_available():
            return False, "Face recognition libraries not installed or initialized."
        
        if self.is_active:
            return True, "Already active"

        if not known_students_data:
            return False, "No student data provided"

        try:
            self.detector.load_known_faces(known_students_data)
            # detector.start_detection() logic might overlap with camera service if it opens its own camera.
            # Ideally FaceDetector should use the frame from CameraService, but for now we follow existing pattern
            # assuming FaceDetector might manage its own stream or we pass frames to it.
            # Looking at original code, FaceDetector acts like a camera wrapper too. 
            # We will use it as is for now to avoid breaking deep logic, but we should eventually unify.
            
            if self.detector.start_detection():
                self.is_active = True
                return True, f"Started with {len(known_students_data)} faces"
            else:
                return False, "Failed to start detector"
        except Exception as e:
            self.logger.error(f"Error starting detection: {e}")
            return False, str(e)

    def stop_detection(self):
        if self.detector and self.is_active:
            self.detector.stop_detection()
            self.is_active = False
            return True
        return False

    def get_frame(self):
        if self.is_active and self.detector:
            return self.detector.get_current_frame_with_annotations()
        return None

    def get_detected_faces(self):
        if self.is_active and self.detector:
            return self.detector.get_detected_faces()
        return []

# Singleton
recognition_service = RecognitionService()
