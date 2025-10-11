from flask_sqlalchemy import SQLAlchemy

# Create a variable to manage the database connection
db = SQLAlchemy()

# --- 1. Announcement Data Structure ---
class Announcement(db.Model):
    # This is the unique number for each post
    id = db.Column(db.Integer, primary_key=True)
    # The short heading for the announcement
    title = db.Column(db.String(100), nullable=False)
    # The full text of the announcement
    text = db.Column(db.Text, nullable=False)
    # When it was posted
    date = db.Column(db.String(50), default='Today')

    # Function to turn this data into a simple format for the web
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.text,
            'posted_on': self.date
        }

# --- 2. Course Data Structure ---
class Course(db.Model):
    # Unique ID for the course
    id = db.Column(db.Integer, primary_key=True)
    # Course code, must be unique (e.g., "CS101")
    code = db.Column(db.String(10), unique=True, nullable=False) 
    # Full name of the course
    name = db.Column(db.String(150), nullable=False)
    # Teacher's name
    prof = db.Column(db.String(100))
    # Where the class is held
    room = db.Column(db.String(20))
    # When the class is held
    time = db.Column(db.String(50))
    
    # Function to turn this data into a simple format for the web
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'professor': self.prof,
            'room_num': self.room,
            'time_slot': self.time
        }
# --- 3. User Data Structure (for login/signup) ---
class User(db.Model):
    # Unique ID for the user
    id = db.Column(db.Integer, primary_key=True)
    # The username or email, must be unique
    username = db.Column(db.String(80), unique=True, nullable=False)
    # The secure hash of the password (NEVER the raw password)
    password_hash = db.Column(db.String(128), nullable=False)
    # The user's role (e.g., 'Student', 'Admin')
    role = db.Column(db.String(20), default='Student') 
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role
        }

# Import the date/time library for recording attendance time
from datetime import datetime

# (The existing User class ends here)

# --- 4. Attendance Data Structure ---
class Attendance(db.Model):
    # This is the unique attendance record ID
    id = db.Column(db.Integer, primary_key=True)
    # The ID of the student (who is logging the attendance)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # The code of the course this attendance is for (e.g., 'CS101')
    course_code = db.Column(db.String(10), nullable=False)
    # The date/time the attendance was marked
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    # Status: True for Present, False for Absent
    is_present = db.Column(db.Boolean, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_code': self.course_code,
            'date': self.timestamp.isoformat(), # Format date clearly
            'status': 'Present' if self.is_present else 'Absent'
        }
# Import the date/time library for recording deadlines
from datetime import datetime

# (The existing Attendance class ends here)

# --- 5. Assignment/Exam Data Structure ---
class Assignment(db.Model):
    # This is the unique assignment ID
    id = db.Column(db.Integer, primary_key=True)
    # The ID of the student the assignment belongs to (could be shared, but simplest is one-to-one)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # The course this assignment is for (e.g., 'CS101')
    course_code = db.Column(db.String(10), nullable=False)
    # The title/name of the assignment
    title = db.Column(db.String(150), nullable=False)
    # The full description/details
    description = db.Column(db.Text)
    # The deadline for submission
    due_date = db.Column(db.DateTime, nullable=False)
    # Status: True for Done, False for Pending/Incomplete
    is_completed = db.Column(db.Boolean, default=False)

    def to_dict(self):
        # Calculate if the assignment is overdue for the dashboard view
        is_overdue = self.due_date < datetime.utcnow() and not self.is_completed

        return {
            'id': self.id,
            'user_id': self.user_id,
            'course_code': self.course_code,
            'title': self.title,
            'description': self.description,
            'due_date': self.due_date.isoformat(),
            'completed': self.is_completed,
            'overdue': is_overdue
        }