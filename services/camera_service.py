import cv2
import threading
import time
import logging
from datetime import datetime

class CameraService:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(CameraService, cls).__new__(cls)
                    cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if self.initialized:
            return
        
        self.camera_index = 0
        self.cap = None
        self.is_running = False
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.capture_thread = None
        self.logger = logging.getLogger(__name__)
        self.initialized = True

    def start_camera(self, camera_index=None):
        """Start camera capture"""
        if camera_index is not None:
            self.camera_index = camera_index

        with self._lock:  # Ensure single thread access for start
            try:
                if self.is_running:
                    self.logger.info("Camera already running")
                    return True
                
                # Try to initialize camera
                self.cap = cv2.VideoCapture(self.camera_index)
                
                if not self.cap.isOpened():
                    self.logger.error(f"Failed to open camera {self.camera_index}")
                    # Try fallback
                    for alt_index in [1, 2, 0]:
                        if alt_index != self.camera_index:
                            self.cap = cv2.VideoCapture(alt_index)
                            if self.cap.isOpened():
                                self.camera_index = alt_index
                                break
                    else:
                        self.logger.error("No working camera found")
                        return False
                
                # Set camera properties
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                
                self.is_running = True
                
                # Start capture thread
                self.capture_thread = threading.Thread(target=self._capture_frames)
                self.capture_thread.daemon = True
                self.capture_thread.start()
                
                self.logger.info(f"Camera {self.camera_index} started successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Error starting camera: {str(e)}")
                if self.cap:
                    self.cap.release()
                return False

    def stop_camera(self):
        """Stop camera capture"""
        with self._lock:
            try:
                self.is_running = False
                
                if self.capture_thread:
                    self.capture_thread.join(timeout=2)
                
                if self.cap:
                    self.cap.release()
                    self.cap = None
                
                with self.frame_lock:
                    self.current_frame = None
                
                self.logger.info("Camera stopped")
                return True
                
            except Exception as e:
                self.logger.error(f"Error stopping camera: {str(e)}")
                return False

    def _capture_frames(self):
        """Capture frames in background thread"""
        while self.is_running and self.cap:
            try:
                ret, frame = self.cap.read()
                
                if ret:
                    with self.frame_lock:
                        self.current_frame = frame.copy()
                else:
                    self.logger.warning("Failed to read frame")
                    time.sleep(0.1)
                    
                time.sleep(0.015)  # ~60 FPS cap
                
            except Exception as e:
                self.logger.error(f"Error in capture thread: {str(e)}")
                break

    def get_frame(self):
        """Get current frame"""
        with self.frame_lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
            return None

    def get_frame_with_overlay(self):
        """Get frame with debug overlay"""
        frame = self.get_frame()
        if frame is not None:
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(frame, timestamp, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                cv2.putText(frame, "Active", (10, frame.shape[0] - 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            except Exception:
                pass
        return frame

# Singleton instance
camera_service = CameraService()
