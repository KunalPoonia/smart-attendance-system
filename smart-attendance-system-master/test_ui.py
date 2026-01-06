from flask import Flask, render_template
from datetime import datetime

app = Flask(__name__)

# Mock data for testing UI
class MockStudent:
    def __init__(self, student_id, name):
        self.student_id = student_id
        self.name = name

class MockRecord:
    def __init__(self, student, date, time_in, status, confidence_score):
        self.student = student
        self.date = date
        self.time_in = time_in
        self.status = status
        self.confidence_score = confidence_score

@app.route('/')
def index():
    # Mock data
    total_students = 150
    today_attendance = 128
    
    # Create mock recent records
    recent_records = [
        MockRecord(
            MockStudent("STU001", "John Doe"),
            datetime.now().date(),
            datetime.now().time(),
            "Present",
            95.5
        ),
        MockRecord(
            MockStudent("STU002", "Jane Smith"),
            datetime.now().date(),
            datetime.now().time(),
            "Present",
            87.2
        ),
        MockRecord(
            MockStudent("STU003", "Bob Johnson"),
            datetime.now().date(),
            datetime.now().time(),
            "Late",
            92.1
        )
    ]
    
    return render_template('index.html', 
                         total_students=total_students,
                         today_attendance=today_attendance,
                         recent_records=recent_records,
                         datetime=datetime)

@app.route('/api/attendance_summary')
def attendance_summary():
    return {'present_percentage': 85}

@app.route('/register_student')
def register_student():
    return "Register Student Page"

@app.route('/mark_attendance')
def mark_attendance():
    return "Mark Attendance Page"

@app.route('/attendance')
def attendance():
    return "Attendance Records Page"

@app.route('/reports')
def reports():
    return "Reports Page"

@app.route('/students')
def students():
    return "Students Page"

@app.route('/settings')
def settings():
    return "Settings Page"

if __name__ == '__main__':
    app.run(debug=True, port=5000)