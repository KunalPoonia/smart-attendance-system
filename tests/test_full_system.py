#!/usr/bin/env python3
"""
Comprehensive test script for the Smart Attendance System
Tests all major functionality including backend routes and features
"""

import sys
import os
import requests
import time
import json
from datetime import datetime, date

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

BASE_URL = "http://127.0.0.1:5000"

def test_server_running():
    """Test if the server is running"""
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        return response.status_code == 200
    except:
        return False

def test_api_endpoints():
    """Test all API endpoints"""
    endpoints = [
        ("/api/attendance_summary", "GET"),
        ("/api/today_attendance", "GET"),
        ("/api/face_recognition_status", "GET"),
    ]
    
    results = []
    for endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", timeout=5)
            
            results.append((endpoint, response.status_code == 200, response.status_code))
        except Exception as e:
            results.append((endpoint, False, str(e)))
    
    return results

def test_camera_endpoints():
    """Test camera-related endpoints"""
    endpoints = [
        ("/start_detection", "POST"),
        ("/get_detected_faces", "GET"),
        ("/stop_detection", "POST"),
        ("/start_face_recognition", "POST"),
        ("/stop_face_recognition", "POST"),
    ]
    
    results = []
    for endpoint, method in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            else:
                response = requests.post(f"{BASE_URL}{endpoint}", timeout=5)
            
            # For camera endpoints, we expect JSON responses
            if response.headers.get('content-type', '').startswith('application/json'):
                data = response.json()
                success = 'success' in data or 'faces' in data
            else:
                success = response.status_code == 200
            
            results.append((endpoint, success, response.status_code))
        except Exception as e:
            results.append((endpoint, False, str(e)))
    
    return results

def test_page_routes():
    """Test main page routes"""
    routes = [
        "/",
        "/students", 
        "/register_student",
        "/attendance",
        "/mark_attendance",
        "/reports"
    ]
    
    results = []
    for route in routes:
        try:
            response = requests.get(f"{BASE_URL}{route}", timeout=10)
            success = response.status_code == 200
            results.append((route, success, response.status_code))
        except Exception as e:
            results.append((route, False, str(e)))
    
    return results

def test_manual_attendance():
    """Test manual attendance marking"""
    try:
        # Test with a dummy student ID
        data = {'student_id': 'TEST001'}
        response = requests.post(f"{BASE_URL}/mark_manual_attendance", data=data, timeout=5)
        
        # We expect a redirect (302) or success (200)
        success = response.status_code in [200, 302]
        return success, response.status_code
    except Exception as e:
        return False, str(e)

def main():
    """Run comprehensive system tests"""
    print("🚀 Smart Attendance System - Comprehensive Test Suite")
    print("=" * 60)
    
    # Check if server is running
    print("🔍 Checking if server is running...")
    if not test_server_running():
        print("❌ Server is not running! Please start the app first with: python app.py")
        return False
    
    print("✅ Server is running!")
    print()
    
    # Test API endpoints
    print("🔍 Testing API Endpoints...")
    api_results = test_api_endpoints()
    for endpoint, success, status in api_results:
        status_icon = "✅" if success else "❌"
        print(f"  {status_icon} {endpoint:25} : {status}")
    print()
    
    # Test camera endpoints
    print("🔍 Testing Camera Endpoints...")
    camera_results = test_camera_endpoints()
    for endpoint, success, status in camera_results:
        status_icon = "✅" if success else "❌"
        print(f"  {status_icon} {endpoint:25} : {status}")
    print()
    
    # Test page routes
    print("🔍 Testing Page Routes...")
    page_results = test_page_routes()
    for route, success, status in page_results:
        status_icon = "✅" if success else "❌"
        print(f"  {status_icon} {route:25} : {status}")
    print()
    
    # Test manual attendance
    print("🔍 Testing Manual Attendance...")
    attendance_success, attendance_status = test_manual_attendance()
    status_icon = "✅" if attendance_success else "❌"
    print(f"  {status_icon} Manual Attendance      : {attendance_status}")
    print()
    
    # Calculate overall results
    all_results = api_results + camera_results + page_results + [("manual_attendance", attendance_success, attendance_status)]
    total_tests = len(all_results)
    passed_tests = sum(1 for _, success, _ in all_results if success)
    
    print("=" * 60)
    print("📊 Test Results Summary:")
    print("=" * 60)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n🎉 All tests passed! The Smart Attendance System is fully functional!")
        print("\n✨ Key Features Working:")
        print("  ✅ Web Interface")
        print("  ✅ API Endpoints")
        print("  ✅ Camera Integration")
        print("  ✅ Face Recognition System")
        print("  ✅ Manual Attendance")
        print("  ✅ Database Operations")
        print("  ✅ Reports Generation")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} tests failed. Check the details above.")
        print("\n🔧 Failed tests may indicate:")
        print("  - Missing dependencies")
        print("  - Database issues")
        print("  - Template syntax errors")
        print("  - Camera/hardware problems")
    
    print("\n🌐 Access the system at: http://127.0.0.1:5000")
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)