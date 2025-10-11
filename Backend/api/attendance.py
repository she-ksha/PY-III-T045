from flask import Blueprint, jsonify, request
from models import db, Attendance, Course # We need Course to calculate attendance later
from sqlalchemy import func # For database functions like counting
import json # Used to handle data correctly

# Create a Blueprint for attendance
attendance_api = Blueprint('attendance_api', __name__)

# --- 1. MARK ATTENDANCE (POST) ---
@attendance_api.route('/mark', methods=['POST'])
def mark_attendance():
    data = request.get_json()
    
    # We need the user ID, course code, and status (True/False)
    user_id = data.get('user_id')
    course_code = data.get('course_code')
    is_present = data.get('is_present', True) # Default to Present if not specified

    if not user_id or not course_code:
        return jsonify({'message': 'Missing user_id or course_code'}), 400

    # Create a new attendance record
    new_record = Attendance(
        user_id=user_id,
        course_code=course_code,
        is_present=is_present
    )
    
    db.session.add(new_record)
    db.session.commit()

    return jsonify(new_record.to_dict()), 201

# --- 2. GET ATTENDANCE SUMMARY (GET) ---
@attendance_api.route('/summary/<int:user_id>', methods=['GET'])
def get_attendance_summary(user_id):
    # Find all unique courses this user has attendance records for
    course_codes = db.session.query(Attendance.course_code).filter_by(user_id=user_id).distinct().all()
    
    summary = []
    
    for (code,) in course_codes:
        # Total number of classes attended (is_present = True)
        present_count = db.session.query(func.count(Attendance.id)).filter_by(user_id=user_id, course_code=code, is_present=True).scalar()
        
        # Total number of classes marked (Present + Absent)
        total_count = db.session.query(func.count(Attendance.id)).filter_by(user_id=user_id, course_code=code).scalar()
        
        # Calculate percentage (handle division by zero if no records)
        percentage = round((present_count / total_count) * 100, 2) if total_count > 0 else 0

        summary.append({
            'course_code': code,
            'present': present_count,
            'total_classes': total_count,
            'percentage': percentage
        })

    return jsonify(summary)