#!/usr/bin/env python3
"""
Installation script for Enhanced Face Recognition System
This script will install all required dependencies including optional enhancements
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
    print("🚀 Installing Enhanced Face Recognition System Dependencies...")
    print("=" * 70)
    
    # Core packages (required)
    core_packages = [
        "Flask==2.3.3",
        "Flask-SQLAlchemy==3.0.5", 
        "opencv-python==4.8.1.78",
        "opencv-contrib-python==4.8.1.78",  # For additional face recognizers
        "numpy==1.24.3",
        "Pillow==10.0.1"
    ]
    
    # Enhanced packages (optional but recommended)
    enhanced_packages = [
        "mediapipe==0.10.7",  # For MediaPipe face detection
        "scikit-learn==1.3.2",  # For advanced ML features
        "scipy==1.11.4"  # For scientific computing
    ]
    
    print("📦 Installing Core Packages...")
    print("-" * 40)
    
    failed_core = []
    for package in core_packages:
        print(f"Installing {package}...")
        if install_package(package):
            print(f"✅ {package}")
        else:
            print(f"❌ {package}")
            failed_core.append(package)
    
    print("\n🎯 Installing Enhanced Packages...")
    print("-" * 40)
    
    failed_enhanced = []
    for package in enhanced_packages:
        print(f"Installing {package}...")
        if install_package(package):
            print(f"✅ {package}")
        else:
            print(f"⚠️  {package} (optional)")
            failed_enhanced.append(package)
    
    print(f"\n📊 Installation Summary:")
    print("=" * 40)
    
    if not failed_core:
        print("🎉 All core packages installed successfully!")
        
        if not failed_enhanced:
            print("🌟 All enhanced packages installed successfully!")
            print("   You have access to the full Enhanced Face Recognition System!")
        else:
            print(f"⚠️  Some enhanced packages failed: {len(failed_enhanced)}")
            print("   Core functionality will work, but some advanced features may be unavailable")
        
        print("\n🚀 System Capabilities:")
        print("   ✅ Multiple face detection methods (DNN + Haar)")
        print("   ✅ Ensemble recognition (LBPH + Eigenfaces + Fisherfaces)")
        print("   ✅ Intelligent face tracking")
        print("   ✅ Advanced preprocessing")
        print("   ✅ Professional annotations")
        
        if "mediapipe" not in str(failed_enhanced).lower():
            print("   ✅ MediaPipe face detection (ultra-fast)")
        else:
            print("   ⚠️  MediaPipe not available (will use OpenCV methods)")
        
        print("\n💡 Next Steps:")
        print("   1. Run: python download_models.py  (for DNN models)")
        print("   2. Run: python test_enhanced_system.py  (to test)")
        print("   3. Run: python app_simple.py  (to start application)")
        
    else:
        print(f"❌ Failed to install core packages: {failed_core}")
        print("\n🔧 Troubleshooting:")
        print("   - Ensure you have Python 3.8+ installed")
        print("   - Try upgrading pip: python -m pip install --upgrade pip")
        print("   - On Windows: Install Visual Studio Build Tools")
        print("   - On Linux: sudo apt-get install python3-dev")
        print("   - On macOS: Install Xcode command line tools")

if __name__ == "__main__":
    main()