from flask import Flask
from models import db  # Import the database object
# Import the logic for each module
from api.announcements import announcement_api 
from api.courses import course_api
from api.auth import auth_api # Import the Auth Blueprint
from api.attendance import attendance_api # Import the Attendance Blueprint
from api.assignments import assignments_api


# --- 1. SETUP ---

# Create the main server app
app = Flask(__name__)

# Tell the app where the database file is
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///campus_data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Connect the database object to the app
db.init_app(app)


# --- 2. LOAD MODULES ---

# Load the announcements logic and set its base URL
app.register_blueprint(announcement_api, url_prefix='/api/announcements')

# Load the courses logic and set its base URL
app.register_blueprint(course_api, url_prefix='/api/courses')

#Load the authentication logic and set its base URL
app.register_blueprint(auth_api, url_prefix='/api/auth') # <---THIS LINE IS CRITICAL

#Load the attendance tracking logic
app.register_blueprint(attendance_api, url_prefix='/api/attendance')

#Load the assignments and exams tracking logic
app.register_blueprint(assignments_api, url_prefix='/api/assignments')

# --- 3. CREATE DATABASE TABLES ---

# This runs once to make sure all tables (Announcement, Course) exist
with app.app_context():
    db.create_all()


# --- 4. START THE SERVER ---

if __name__ == '__main__':
    print("Starting Campus Companion server...")
    app.run(debug=True)