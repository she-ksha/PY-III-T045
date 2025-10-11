from flask import Blueprint, jsonify, request
from models import db, Course # Import necessary items

# Create a Blueprint to manage the course routes
course_api = Blueprint('course_api', __name__)

# --- API ROUTES for COURSES ---

# Route to get all courses OR post a new one
@course_api.route('/', methods=['GET', 'POST'])
def handle_all_courses():
    if request.method == 'GET':
        all_courses = Course.query.all()
        return jsonify([c.to_dict() for c in all_courses])

    elif request.method == 'POST':
        data = request.get_json()
        
        new_course = Course(
            code=data['code'],
            name=data['name'],
            prof=data.get('professor'), 
            room=data.get('room'),
            time=data.get('time')
        )
        
        db.session.add(new_course)
        db.session.commit()
        return jsonify(new_course.to_dict()), 201


# Route to handle one specific course (by its ID)
@course_api.route('/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def handle_single_course(id):
    course = Course.query.get_or_404(id)

    if request.method == 'GET':
        return jsonify(course.to_dict())

    elif request.method == 'PUT':
        # Update the existing course details
        data = request.get_json()
        course.name = data.get('name', course.name)
        course.prof = data.get('professor', course.prof)
        course.room = data.get('room', course.room)
        
        db.session.commit()
        return jsonify(course.to_dict())

    elif request.method == 'DELETE':
        db.session.delete(course)
        db.session.commit()
        return '', 204