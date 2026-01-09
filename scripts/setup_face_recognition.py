#!/usr/bin/env python3
"""
Setup script for face recognition functionality
"""

import os
import sys
import subprocess
import platform

def install_package(package_name):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except subprocess.CalledProcessError:
        return False

def check_cmake():
    """Check if CMake is available"""
    try:
        subprocess.check_output(["cmake", "--version"])
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def main():
    """Setup face recognition dependencies"""
    print("=" * 60)
    print("SMART ATTENDANCE SYSTEM - FACE RECOGNITION SETUP")
    print("=" * 60)
    
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.system()} {platform.machine()}")
    print()
    
    # Check CMake (required for dlib)
    print("Checking CMake...")
    if check_cmake():
        print("✅ CMake is available")
    else:
        print("❌ CMake not found")
        print("Please install CMake first:")
        if platform.system() == "Windows":
            print("  - Download from: https://cmake.org/download/")
            print("  - Or use: winget install Kitware.CMake")
        elif platform.system() == "Darwin":  # macOS
            print("  - brew install cmake")
        else:  # Linux
            print("  - sudo apt-get install cmake (Ubuntu/Debian)")
            print("  - sudo yum install cmake (CentOS/RHEL)")
        return False
    
    # Install packages
    packages = [
        "opencv-python",
        "numpy",
        "Pillow",
        "dlib",
        "face-recognition"
    ]
    
    print("\nInstalling required packages...")
    failed_packages = []
    
    for package in packages:
        print(f"Installing {package}...")
        if install_package(package):
            print(f"✅ {package} installed successfully")
        else:
            print(f"❌ Failed to install {package}")
            failed_packages.append(package)
    
    if failed_packages:
        print(f"\n❌ Failed to install: {', '.join(failed_packages)}")
        print("\nTroubleshooting tips:")
        print("1. Make sure you have CMake installed")
        print("2. On Windows, install Visual Studio Build Tools")
        print("3. Try installing dlib separately: pip install dlib")
        print("4. For face-recognition issues, try: pip install --upgrade face-recognition")
        return False
    else:
        print("\n✅ All packages installed successfully!")
        print("\nNext steps:")
        print("1. Run: python test_face_recognition.py")
        print("2. Start the application: python app.py")
        print("3. Register students with photos")
        print("4. Use face recognition for attendance")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)