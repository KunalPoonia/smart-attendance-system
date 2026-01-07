#!/usr/bin/env python3
"""
Comprehensive test script for Enhanced Face Recognition System
"""

import sys
import os
import cv2
import numpy as np
import time

def test_core_dependencies():
    """Test core dependencies"""
    print("🔧 Testing Core Dependencies...")
    print("-" * 40)
    
    results = {}
    
    # Test OpenCV
    try:
        import cv2
        print(f"✅ OpenCV: {cv2.__version__}")
        results['opencv'] = True
        
        # Test OpenCV contrib
        try:
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            print("✅ OpenCV Contrib (face recognition)")
            results['opencv_contrib'] = True
        except:
            print("❌ OpenCV Contrib not available")
            results['opencv_contrib'] = False
            
    except ImportError:
        print("❌ OpenCV not available")
        results['opencv'] = False
        results['opencv_contrib'] = False
    
    # Test NumPy
    try:
        import numpy as np
        print(f"✅ NumPy: {np.__version__}")
        results['numpy'] = True
    except ImportError:
        print("❌ NumPy not available")
        results['numpy'] = False
    
    return results

def test_enhanced_dependencies():
    """Test enhanced dependencies"""
    print("\n🎯 Testing Enhanced Dependencies...")
    print("-" * 40)
    
    results = {}
    
    # Test MediaPipe
    try:
        import mediapipe as mp
        print(f"✅ MediaPipe: {mp.__version__}")
        results['mediapipe'] = True
    except ImportError:
        print("⚠️  MediaPipe not available (optional)")
        results['mediapipe'] = False
    
    # Test scikit-learn
    try:
        import sklearn
        print(f"✅ Scikit-learn: {sklearn.__version__}")
        results['sklearn'] = True
    except ImportError:
        print("⚠️  Scikit-learn not available (optional)")
        results['sklearn'] = False
    
    return results

def test_face_detection_methods():
    """Test different face detection methods"""
    print("\n👤 Testing Face Detection Methods...")
    print("-" * 40)
    
    results = {}
    
    # Create test image with a simple face
    test_image = np.zeros((200, 200, 3), dtype=np.uint8)
    cv2.circle(test_image, (100, 100), 80, (200, 200, 200), -1)  # Face
    cv2.circle(test_image, (80, 80), 10, (0, 0, 0), -1)   # Left eye
    cv2.circle(test_image, (120, 80), 10, (0, 0, 0), -1)  # Right eye
    cv2.ellipse(test_image, (100, 120), (20, 10), 0, 0, 180, (0, 0, 0), 2)  # Mouth
    
    # Test Haar Cascade
    try:
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        gray = cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        print(f"✅ Haar Cascade: Detected {len(faces)} faces")
        results['haar'] = True
    except Exception as e:
        print(f"❌ Haar Cascade failed: {e}")
        results['haar'] = False
    
    # Test DNN Detection
    try:
        model_path = "models"
        prototxt_path = os.path.join(model_path, "deploy.prototxt")
        model_weights_path = os.path.join(model_path, "res10_300x300_ssd_iter_140000.caffemodel")
        
        if os.path.exists(prototxt_path) and os.path.exists(model_weights_path):
            net = cv2.dnn.readNetFromCaffe(prototxt_path, model_weights_path)
            blob = cv2.dnn.blobFromImage(test_image, 1.0, (300, 300), [104, 117, 123])
            net.setInput(blob)
            detections = net.forward()
            face_count = sum(1 for i in range(detections.shape[2]) if detections[0, 0, i, 2] > 0.5)
            print(f"✅ DNN Detection: Detected {face_count} faces")
            results['dnn'] = True
        else:
            print("⚠️  DNN models not found (run download_models.py)")
            results['dnn'] = False
    except Exception as e:
        print(f"❌ DNN Detection failed: {e}")
        results['dnn'] = False
    
    # Test MediaPipe
    try:
        import mediapipe as mp
        mp_face_detection = mp.solutions.face_detection.FaceDetection(
            model_selection=0, min_detection_confidence=0.5)
        rgb_image = cv2.cvtColor(test_image, cv2.COLOR_BGR2RGB)
        results_mp = mp_face_detection.process(rgb_image)
        face_count = len(results_mp.detections) if results_mp.detections else 0
        print(f"✅ MediaPipe: Detected {face_count} faces")
        results['mediapipe'] = True
    except Exception as e:
        print(f"⚠️  MediaPipe not available: {e}")
        results['mediapipe'] = False
    
    return results

def test_face_recognizers():
    """Test face recognition methods"""
    print("\n🧠 Testing Face Recognition Methods...")
    print("-" * 40)
    
    results = {}
    
    # Create sample face data
    sample_faces = []
    sample_labels = []
    
    for i in range(5):
        face = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        sample_faces.append(face)
        sample_labels.append(i % 2)  # Two different labels
    
    sample_labels = np.array(sample_labels)
    
    # Test LBPH
    try:
        lbph = cv2.face.LBPHFaceRecognizer_create()
        lbph.train(sample_faces, sample_labels)
        label, confidence = lbph.predict(sample_faces[0])
        print(f"✅ LBPH Recognizer: Prediction confidence {confidence:.2f}")
        results['lbph'] = True
    except Exception as e:
        print(f"❌ LBPH Recognizer failed: {e}")
        results['lbph'] = False
    
    # Test Eigenfaces
    try:
        eigen = cv2.face.EigenFaceRecognizer_create()
        eigen.train(sample_faces, sample_labels)
        label, confidence = eigen.predict(sample_faces[0])
        print(f"✅ Eigenfaces: Prediction confidence {confidence:.2f}")
        results['eigenfaces'] = True
    except Exception as e:
        print(f"⚠️  Eigenfaces not available: {e}")
        results['eigenfaces'] = False
    
    # Test Fisherfaces
    try:
        fisher = cv2.face.FisherFaceRecognizer_create()
        fisher.train(sample_faces, sample_labels)
        label, confidence = fisher.predict(sample_faces[0])
        print(f"✅ Fisherfaces: Prediction confidence {confidence:.2f}")
        results['fisherfaces'] = True
    except Exception as e:
        print(f"⚠️  Fisherfaces not available: {e}")
        results['fisherfaces'] = False
    
    return results

def test_enhanced_system():
    """Test the enhanced face recognition system"""
    print("\n🚀 Testing Enhanced Face Recognition System...")
    print("-" * 50)
    
    try:
        from face_recognition_enhanced import EnhancedFaceRecognition
        
        # Initialize system
        face_system = EnhancedFaceRecognition()
        print("✅ Enhanced system initialized successfully")
        
        # Test system stats
        stats = face_system.get_recognition_stats()
        print(f"📊 System Stats:")
        print(f"   - Detection methods: {stats['detection_methods']}")
        print(f"   - Recognition methods: {stats['recognition_methods']}")
        print(f"   - DNN available: {stats['has_dnn']}")
        print(f"   - MediaPipe available: {stats['has_mediapipe']}")
        print(f"   - Known students: {stats['total_students']}")
        
        # Test detection start/stop
        success, message = face_system.start_detection()
        if success:
            print(f"✅ Detection started: {message}")
            
            # Let it run briefly
            time.sleep(2)
            
            # Get detected faces
            detected_faces = face_system.get_detected_faces()
            print(f"🔍 Currently detected faces: {len(detected_faces)}")
            
            # Stop detection
            success, message = face_system.stop_detection()
            if success:
                print(f"✅ Detection stopped: {message}")
            else:
                print(f"❌ Failed to stop: {message}")
        else:
            print(f"❌ Failed to start detection: {message}")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Enhanced system not available: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing enhanced system: {e}")
        return False

def test_camera_access():
    """Test camera access"""
    print("\n📹 Testing Camera Access...")
    print("-" * 30)
    
    try:
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Could not open camera")
            return False
        
        ret, frame = cap.read()
        if not ret:
            print("❌ Could not read frame from camera")
            cap.release()
            return False
        
        print(f"✅ Camera access successful")
        print(f"📐 Frame size: {frame.shape}")
        
        cap.release()
        return True
        
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        return False

def main():
    print("🚀 Enhanced Face Recognition System - Comprehensive Test")
    print("=" * 70)
    
    # Test all components
    core_results = test_core_dependencies()
    enhanced_results = test_enhanced_dependencies()
    detection_results = test_face_detection_methods()
    recognition_results = test_face_recognizers()
    camera_result = test_camera_access()
    enhanced_system_result = test_enhanced_system()
    
    # Final summary
    print("\n📋 Final Test Summary")
    print("=" * 50)
    
    # Core functionality
    core_working = all([core_results.get('opencv', False), 
                       core_results.get('opencv_contrib', False),
                       core_results.get('numpy', False)])
    
    if core_working:
        print("✅ Core System: READY")
    else:
        print("❌ Core System: NOT READY")
    
    # Detection methods
    detection_count = sum([detection_results.get('haar', False),
                          detection_results.get('dnn', False),
                          detection_results.get('mediapipe', False)])
    print(f"🔍 Detection Methods: {detection_count}/3 available")
    
    # Recognition methods
    recognition_count = sum([recognition_results.get('lbph', False),
                           recognition_results.get('eigenfaces', False),
                           recognition_results.get('fisherfaces', False)])
    print(f"🧠 Recognition Methods: {recognition_count}/3 available")
    
    # Camera
    if camera_result:
        print("📹 Camera: WORKING")
    else:
        print("📹 Camera: NOT WORKING")
    
    # Enhanced system
    if enhanced_system_result:
        print("🚀 Enhanced System: FULLY OPERATIONAL")
    else:
        print("⚠️  Enhanced System: LIMITED FUNCTIONALITY")
    
    # Overall status
    print("\n🎯 Overall Status:")
    if core_working and camera_result and enhanced_system_result:
        print("🎉 ENHANCED FACE RECOGNITION SYSTEM IS READY!")
        print("\n💡 Next Steps:")
        print("   1. Run: python app_simple.py")
        print("   2. Register students with photos")
        print("   3. Test face recognition in Mark Attendance")
        print("   4. Enjoy state-of-the-art face recognition!")
    elif core_working and camera_result:
        print("✅ BASIC FACE RECOGNITION SYSTEM IS READY")
        print("   Some advanced features may not be available")
    else:
        print("❌ SYSTEM NOT READY - Please fix the issues above")

if __name__ == "__main__":
    main()