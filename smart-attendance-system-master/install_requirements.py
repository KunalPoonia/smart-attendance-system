#!/usr/bin/env python3
"""
Installation script for Smart Attendance System
This script will install all required dependencies
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print("🚀 Installing Smart Attendance System Dependencies...")
    print("=" * 50)
    
    # Required packages
    packages = [
        "Flask==2.3.3",
        "Flask-SQLAlchemy==3.0.5", 
        "opencv-python==4.8.1.78",
        "numpy==1.24.3",
        "Pillow==10.0.1",
        "cmake",  # Required for dlib
        "dlib==19.24.2",
        "face-recognition==1.3.0"
    ]
    
    failed_packages = []
    
    for package in packages:
        print(f"📦 Installing {package}...")
        if install_package(package):
            print(f"✅ Successfully installed {package}")
        else:
            print(f"❌ Failed to install {package}")
            failed_packages.append(package)
        print("-" * 30)
    
    if failed_packages:
        print(f"\n❌ Failed to install: {', '.join(failed_packages)}")
        print("\n💡 Try installing manually:")
        for package in failed_packages:
            print(f"   pip install {package}")
        
        if "dlib" in str(failed_packages) or "face-recognition" in str(failed_packages):
            print("\n🔧 For dlib/face-recognition issues:")
            print("   - On Windows: Install Visual Studio Build Tools")
            print("   - On Linux: sudo apt-get install cmake libopenblas-dev liblapack-dev")
            print("   - On macOS: brew install cmake")
    else:
        print("\n🎉 All packages installed successfully!")
        print("\n🚀 You can now run the application:")
        print("   python app_simple.py")

if __name__ == "__main__":
    main()