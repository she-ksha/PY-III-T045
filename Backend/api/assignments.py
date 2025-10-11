from flask import Blueprint, jsonify, request
from models import db, Assignment
from datetime import datetime # Needed to parse the date input

# Create a Blueprint for assignments
assignments_api = Blueprint('assignments_api', __name__)

# --- 1. GET ALL, POST NEW ASSIGNMENT ---
@assignments_api.route('/<int:user_id>', methods=['GET', 'POST'])
def manage_assignments(user_id):
    # Filter by user ID as this is personalized data
    if request.method == 'GET':
        # GET: Fetch all assignments for a specific user
        all_tasks = Assignment.query.filter_by(user_id=user_id).all()
        return jsonify([task.to_dict() for task in all_tasks])

    elif request.method == 'POST':
        # POST: Create a new assignment
        data = request.get_json()
        
        # We need to convert the string date from the user into a datetime object
        try:
            due_date = datetime.fromisoformat(data['due_date'])
        except (KeyError, ValueError):
            return jsonify({'message': 'Invalid or missing due_date format. Use YYYY-MM-DDTHH:MM:SS format.'}), 400

        new_task = Assignment(
            user_id=user_id,
            course_code=data['course_code'],
            title=data['title'],
            description=data.get('description', ''),
            due_date=due_date
        )
        
        db.session.add(new_task)
        db.session.commit()
        return jsonify(new_task.to_dict()), 201

# --- 2. UPDATE/DELETE & MARK STATUS ---
@assignments_api.route('/<int:user_id>/<int:task_id>', methods=['PUT', 'DELETE'])
def manage_single_assignment(user_id, task_id):
    # Fetch the task, ensuring it belongs to the correct user
    task = Assignment.query.filter_by(id=task_id, user_id=user_id).first_or_404()

    if request.method == 'PUT':
        # PUT: Update details OR mark as completed/done
        data = request.get_json()
        
        # Check if they are updating the status (Track Status (to-do/done))
        if 'is_completed' in data:
            task.is_completed = data['is_completed']
        
        # Check if they are updating the deadline or other details
        if 'due_date' in data:
            try:
                task.due_date = datetime.fromisoformat(data['due_date'])
            except ValueError:
                return jsonify({'message': 'Invalid due_date format.'}), 400
                
        task.title = data.get('title', task.title)
        task.description = data.get('description', task.description)

        db.session.commit()
        return jsonify(task.to_dict())

    elif request.method == 'DELETE':
        # DELETE: Remove the task
        db.session.delete(task)
        db.session.commit()
        return '', 204