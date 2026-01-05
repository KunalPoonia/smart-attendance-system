# 🎓 Smart Attendance System  
### Face Recognition–Based Automated Attendance (B.Tech Project)

An intelligent **Smart Attendance System** that uses **real-time face recognition** to automatically mark student attendance, eliminate proxy attendance, and simplify attendance management for educational institutions.

This project demonstrates the real-world application of **Computer Vision and AI** in academic environments.

---

## 🚀 Project Highlights

- 📸 Real-time face recognition using webcam
- 🧠 AI-powered identity verification
- ⏱️ Automatic attendance marking with timestamps
- 📊 Export attendance reports (CSV / Excel)
- 🧑‍🏫 Admin dashboard for teachers
- ⚠️ Unknown face detection alerts
- 🔁 Manual attendance backup mode

---

## 🧰 Tech Stack

- **Backend**: Flask (Python)  
- **Computer Vision**: OpenCV, `face_recognition` (dlib)  
- **Database**: SQLite  
- **Frontend**: HTML, CSS, JavaScript  
- **Libraries**: NumPy, Pandas, Pillow  

---

## 🧠 How It Works

1. Students register using facial images  
2. System encodes and stores face features  
3. Webcam captures live video feed  
4. Faces are detected and matched in real time  
5. Attendance is marked automatically with date & time  
6. Admin can export reports anytime  

---

## ✨ Features

- ✅ Face registration for new students  
- ✅ Real-time face recognition via webcam  
- ✅ Automatic attendance marking with timestamp  
- ✅ Proxy attendance prevention  
- ✅ Admin dashboard for teachers  
- ✅ Unknown face detection alerts  
- ✅ Export attendance as CSV / Excel  
- ✅ Manual attendance mode (backup)  

---

## 📂 Project Structure


smart_attendance_system/
├── app.py # Main Flask application
├── config.py # Configuration settings
├── requirements.txt # Python dependencies
├── database/
│ ├── init.py
│ ├── models.py # Database models
│ └── attendance.db # SQLite database
├── face_recognition/
│ ├── init.py
│ ├── face_encoder.py # Face encoding utilities
│ └── face_detector.py # Real-time face detection
├── static/
│ ├── css/
│ ├── js/
│ └── uploads/ # Student photos
├── templates/ # HTML templates
├── utils/
│ ├── init.py
│ └── helpers.py # Utility functions
└── student_images/ # Training images


---

## ⚙️ Installation & Setup

### 🔹 Quick Start

➡️ Open browser: http://localhost:5000

🔹 Face Recognition Setup (Recommended)

Required for full face recognition functionality

1️⃣ Install CMake (for dlib)

Windows: https://cmake.org/download/

macOS:

brew install cmake


Linux:

sudo apt-get install cmake

2️⃣ Run setup script
python setup_face_recognition.py

3️⃣ Test face recognition
python test_face_recognition.py

4️⃣ Start the application
python app.py

💻 System Requirements

Python 3.7 or higher

Webcam / Camera device

CMake (for dlib compilation)

Minimum 4GB RAM recommended

🧑‍🏫 Usage Guide
📸 Automatic Face Recognition Mode

Register students via admin panel

Upload clear student photos

Start camera from attendance page

Enable face recognition

System detects faces automatically

Attendance is marked in real time

✍️ Manual Mode (Backup)

Enter student ID manually

Useful when camera is unavailable

Ensures attendance continuity

📊 Admin Features

👥 Student management

📅 Attendance monitoring

📈 Attendance reports

📤 CSV / Excel export

⚙️ System configuration

🎯 Applications

Schools & colleges

Universities

Training institutes

AI-based academic systems

🔮 Future Enhancements

Improve recognition accuracy

Cloud database integration

Mobile application support

Role-based access control

Multi-camera support

👨‍💻 Author

[Chirag Tankan]
B.Tech 1st Year Student
Computer Vision / AI Project

📜 License

This project is developed for academic and learning purposes.
Feel free to use and modify with proper attribution.
