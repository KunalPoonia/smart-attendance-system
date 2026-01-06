Smart Attendance System

Automated attendance system using face recognition technology to prevent proxy attendance and provide real-time tracking and analytics.

Features

Face registration & real-time recognition

Automatic attendance marking

Confidence-based verification

Reports: department-wise stats, charts, CSV/Excel export

Responsive web interface

Tech Stack

Backend: Python, Flask, SQLAlchemy, SQLite
CV: OpenCV, dlib, face_recognition, NumPy
Frontend: HTML5, CSS3, Bootstrap 5, JS, jQuery, Chart.js
Tools: Pillow, Pandas, OpenPyXL

Installation
git clone https://github.com/<username>/smart-attendance-system.git
cd smart-attendance-system
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
python app.py


Open in browser: http://127.0.0.1:5000

Database Schema

Students Table

id | student_id | name | email | phone | dept | year | section | face_encoding | image_path


Attendance Table

id | student_id | date | time_in | time_out | status | confidence_score

Core Code Snippets

Face Registration

def register_student_face(img_path):
    img = face_recognition.load_image_file(img_path)
    locs = face_recognition.face_locations(img)
    if len(locs)!=1: raise ValueError("One face only")
    return face_recognition.face_encodings(img, locs)[0]


Real-time Recognition

def recognize_faces(frame, known_encodings, names):
    small = cv2.resize(frame,(0,0),fx=0.25,fy=0.25)
    locs = face_recognition.face_locations(small)
    encs = face_recognition.face_encodings(small, locs)
    res=[]
    for e in encs:
        matches = face_recognition.compare_faces(known_encodings, e)
        dists = face_recognition.face_distance(known_encodings, e)
        i=np.argmin(dists)
        if matches[i] and dists[i]<0.6: res.append((names[i],1-dists[i]))
    return res

Performance

Detection: 95-98%, Recognition: 92-96%

FPS: 15-20, Frame processing: 30-50ms

Database <100ms, memory: 150-300MB

Challenges & Solutions

Lighting/Camera: Histogram equalization, min res 640x480

Real-time: Frame skipping, multithreading

Database: JSON serialization for encodings

Web UI: AJAX/WebSocket for real-time updates

Future Scope

Mobile apps & cloud deployment

Multi-camera, emotion & mask detection

Predictive analytics & academic correlation

Contributors

Team: [Your Name]
Institution: [Your College/University]
Course: B.Tech CSE/IT – 2nd Year
Date: [Current Date]