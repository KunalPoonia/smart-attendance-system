# 🪟 Windows Setup Guide

This guide provides detailed instructions for setting up the **Smart Attendance System** on Windows. Following these steps will help you avoid common issues with `dlib`, `CMake`, and environment configuration.

---

## 🛠️ Step 1: Install Visual Studio Build Tools

`dlib` (a core dependency) requires a C++ compiler. 

1. Download the **Visual Studio Build Tools 2022** from [visualstudio.microsoft.com](https://visualstudio.microsoft.com/visual-cpp-build-tools/).
2. During installation, select the **"Desktop development with C++"** workload.
3. Ensure the following components are selected (default ones are usually enough):
   - MSVC v143 - VS 2022 C++ x64/x86 build tools
   - Windows 11 SDK (or Windows 10 SDK)
   - C++ CMake tools for Windows
4. Click **Install** and wait for the process to complete.

---

## 🏗️ Step 2: Install CMake

CMake is used to build `dlib`. It's easiest to install it via `pip`.

```powershell
pip install cmake
```

> [!IMPORTANT]
> After installing Build Tools and CMake, **restart your terminal** or VS Code to ensure environment variables are updated.

---

## 🐍 Step 3: Set Up Python Environment

It is highly recommended to use a virtual environment.

1. **Create Virtual Environment**:
   ```powershell
   python -m venv venv
   ```

2. **Activate Virtual Environment**:
   ```powershell
   .\venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

---

## 🔑 Step 4: Configure Environment Variables

The application requires a `SECRET_KEY` for security features.

1. **Generate a Secret Key**:
   Run this command in your terminal:
   ```powershell
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
2. **Create .env File**:
   Copy `.env.example` to `.env`:
   ```powershell
   copy .env.example .env
   ```
3. **Update .env**:
   Open `.env` in your editor and replace `your-secure-secret-key-here` with the key you generated.

---

## 🚀 Step 5: Run the Application

Now you are ready to start the system!

```powershell
python app.py
```

Visit: `http://localhost:5000`

---

## 🔍 Troubleshooting Common Errors

### ❌ `Failed building wheel for dlib`
This usually means:
- **Build Tools are missing**: Re-run the VS installer and ensure "Desktop development with C++" is checked.
- **CMake not in PATH**: Ensure you've run `pip install cmake` and restarted your terminal.

### ❌ Port 5000 is already in use
If you see an error about port 5000:
1. Find the process: `netstat -ano | findstr :5000`
2. Kill the process: `taskkill /PID <PROCESS_ID> /F` (Replace `<PROCESS_ID>` with the actual PID from the previous step).

### ❌ Camera not detected
- Ensure your webcam is connected.
- Check if another application (like Zoom or Teams) is using the camera.
- Try changing `CAMERA_INDEX` in `.env` to `1` or `2`.

---

## 💡 Quick Tips
- **Python Version**: Use Python 3.7 to 3.11 for best compatibility with `dlib` wheels.
- **Admin Rights**: Sometimes, installing Build Tools requires Administrator privileges.

For more general information, refer back to the [main README](../README.md).
