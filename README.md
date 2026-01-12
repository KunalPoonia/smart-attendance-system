# 🤖📋 Smart Attendance System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An open‑source, production‑ready **Face Recognition–based Attendance System** built as a **B.Tech final/major project**. Designed to prevent proxy attendance, ensure accountability, and keep things clean, simple, and scalable.

> Built the old-school way (solid fundamentals) with a future-facing mindset.

---

## 📌 TABLE OF CONTENTS

*  Overview
*  Features
*  Tech Stack
*  Project Architecture
*  Installation
*  Usage
*  Configuration
*  Security & Privacy
*  Roadmap
*  Contributing
*  Code of Conduct
*  License
*  Authors & Credits

---

## 🚀 PROJECT OVERVIEW

This system uses **computer vision + facial recognition** to automatically mark student attendance in real time. It replaces fragile manual systems and shuts the door on proxy attendance—for good.

Core goals:

* Accuracy over shortcuts
* Transparency over confusion
* Open-source over gatekeeping

---

## ✨ FEATURES

* 🎓 Student face registration 🆔
* 📷 Real-time face recognition via webcam 🤖
* ⏱️ Automatic attendance with timestamp 📝
* 🚫 Proxy attendance prevention 👥
* ⚠️ Unknown face detection & alerts 🕵️‍♂️
* 🧑‍🏫 Admin dashboard for teachers 📊
* 📊 CSV / Excel attendance export 📁
* 📋 Manual attendance fallback ✍️

---

## 🧠 TECH STACK

1. **Backend**

* Python (Flask)
* Flask‑SQLAlchemy

2. **Computer Vision**

* OpenCV
* face_recognition (dlib)

3. **Frontend**

* HTML5 / CSS3 / JavaScript

4. **Database**

* SQLite (simple, reliable, portable)

5. **Libraries**

* NumPy
* Pandas
* Pillow

---

## 🏗️ PROJECT STRUCTURE

```
smart_attendance_system/
├── app.py
├── config.py
├── requirements.txt
├── database/
│   ├── models.py
│   └── attendance.db
├── face_recognition/
│   ├── face_encoder.py
│   └── face_detector.py
├── static/
│   ├── css/
│   ├── js/
│   └── uploads/
├── templates/
├── utils/
│   └── helpers.py
├── student_images/
├── tests/
├── docs/
└── README.md
```

---

## ⚙️ INSTALLATION

### ⭐Prerequisites

* Python **3.7+**
* Webcam
* 4GB RAM (minimum)

### ⭐Clone Repository

```bash
git clone https://github.com/your-username/smart-attendance-system.git
cd smart-attendance-system
```

### ⭐Install Dependencies

```bash
pip install -r requirements.txt
```

### ⭐Run Application

```bash
python app.py
```

Visit: `http://localhost:5000`

---

## 🧩 Dlib Installation (Critical)

Face recognition depends on **dlib**. Follow this verified guide:

🔗 [https://github.com/z-mahmud22/Dlib_Windows_Python3.x](https://github.com/z-mahmud22/Dlib_Windows_Python3.x)

### Common Fix (Windows)

* Install **Visual Studio C++ Build Tools**
* Install CMake
* Restart terminal (yes, really)

---

## 🛠️ Troubleshooting & Common Issues

The most common installation failure is related to **`dlib`** and **`CMake`**. If you encounter errors like
`Failed building wheel for dlib`, follow the steps below based on your operating system.

### 🪟 Windows

1. **Install Visual Studio Build Tools**
   Download from: [https://visualstudio.microsoft.com/visual-cpp-build-tools/](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
   During installation, select **“Desktop development with C++”**.
2. **Install CMake**

   ```bash
   pip install cmake
   ```
3. **Verify Environment Variables**
   Ensure **Python** and **Python/Scripts** are added to your *System Environment Variables*.

---

### 🍎 macOS

1. **Install Xcode Command Line Tools**

   ```bash
   xcode-select --install
   ```
2. **Install CMake using Homebrew**

   ```bash
   brew install cmake
   ```

---

### 🐧 Linux (Ubuntu / Debian)

Install the required build tools and X11 development libraries:

```bash
sudo apt-get update
sudo apt-get install build-essential cmake libgtk-3-dev libboost-python-dev libx11-dev
```

---

## 🧪 USAGE

### ⭐Automatic Mode

1. Register students (clear photos only)
2. Start camera
3. Enable face recognition
4. System auto-detects
5. Attendance marked

### ⭐Manual Mode

1. Enter student ID
2. Mark attendance manually
3. Used as fallback

---

## 🔐 Security & Privacy

* Face encodings stored securely
* No raw biometric sharing
* Local‑only processing
* No cloud dependency

⚠️ **Ethical Note**: Deploy only with user consent.

---

## 🛣️ ROADMAP

* 🔄 Multi‑camera support
* ☁️ Cloud database option
* 📱 Mobile app integration
* 🧠 Deep learning face models
* 🧾 Audit logs

---

## 🤝 CONTRIBUTING

⭐We welcome contributors.⭐

### How to Contribute

1. Fork the repo
2. Create a feature branch
3. Commit with clarity
4. Open a Pull Request

Read: `CONTRIBUTING.md`

---

## 📜 CODE OF CONDUCT

This project follows the **Contributor Covenant**.

* Be respectful
* No harassment
* Build, don’t break people

Read: `CODE_OF_CONDUCT.md`

---

## 🛡️ SECURITY POLICY

If you find a vulnerability:

* Do **not** open a public issue
* Email the maintainer

Read: `SECURITY.md`

---

## 📄 LICENSE

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

You are free to:

* Use
* Modify
* Distribute

Just give credit where it’s due.

---

## 👨‍💻 AUTHOR

## Kunal Poonia
B.Tech – 2nd Year
Open‑source contributor & builder

---

## 🌟 FINAL NOTE

This repo isn’t just a project.

It’s proof that fundamentals still matter.
That open source wins.
That clean code ages well.

Build it. Break it. Improve it. 🚀
