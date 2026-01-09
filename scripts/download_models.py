#!/usr/bin/env python3
"""
Download DNN models for enhanced face detection
"""

import os
import urllib.request
import sys

def download_file(url, filename):
    """Download a file with progress indication"""
    def progress_hook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(100, (downloaded * 100) // total_size)
            sys.stdout.write(f"\r{filename}: {percent}% ({downloaded}/{total_size} bytes)")
            sys.stdout.flush()
    
    try:
        urllib.request.urlretrieve(url, filename, progress_hook)
        print(f"\n✅ Downloaded {filename}")
        return True
    except Exception as e:
        print(f"\n❌ Failed to download {filename}: {e}")
        return False

def main():
    print("📦 Downloading DNN models for enhanced face detection...")
    print("=" * 60)
    
    # Create models directory
    models_dir = "models"
    os.makedirs(models_dir, exist_ok=True)
    
    # Model files to download
    files_to_download = [
        {
            'url': 'https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt',
            'filename': os.path.join(models_dir, 'deploy.prototxt'),
            'description': 'DNN model architecture'
        },
        {
            'url': 'https://raw.githubusercontent.com/opencv/opencv_3rdparty/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel',
            'filename': os.path.join(models_dir, 'res10_300x300_ssd_iter_140000.caffemodel'),
            'description': 'DNN model weights (larger file)'
        }
    ]
    
    success_count = 0
    
    for file_info in files_to_download:
        print(f"\n📥 Downloading {file_info['description']}...")
        
        if os.path.exists(file_info['filename']):
            print(f"⚠️  {file_info['filename']} already exists, skipping...")
            success_count += 1
            continue
        
        if download_file(file_info['url'], file_info['filename']):
            success_count += 1
    
    print(f"\n📊 Download Summary:")
    print(f"   ✅ Successfully downloaded: {success_count}/{len(files_to_download)} files")
    
    if success_count == len(files_to_download):
        print("\n🎉 All models downloaded successfully!")
        print("   Enhanced face detection with DNN is now available")
        print("   The system will automatically use DNN for better accuracy")
    else:
        print("\n⚠️  Some models failed to download")
        print("   The system will fall back to Haar cascades")
        print("   Face detection will still work but with reduced accuracy")
    
    print(f"\n💡 Models saved in: {os.path.abspath(models_dir)}")

if __name__ == "__main__":
    main()