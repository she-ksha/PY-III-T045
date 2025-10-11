from flask import Blueprint, jsonify, request
# We need to import the password hashing tool
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User # Import necessary items

# Create a Blueprint for authentication
auth_api = Blueprint('auth_api', __name__)

# --- Helper functions for security ---

def set_password(user, password):
    # Hashes the password securely before storing it
    user.password_hash = generate_password_hash(password)

def check_password(user, password):
    # Compares a login attempt to the stored hash
    return check_password_hash(user.password_hash, password)


# --- 1. REGISTRATION Route (Sign-Up) ---
@auth_api.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Missing username or password'}), 400

    # Check if the username is already taken
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 409

    # Create the new user object
    new_user = User(username=username)
    
    # Hash and set the password using the secure helper function
    set_password(new_user, password) 
    
    db.session.add(new_user)
    db.session.commit()

    return jsonify(new_user.to_dict()), 201


# --- 2. LOGIN Route ---
@auth_api.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Find the user in the database
    user = User.query.filter_by(username=username).first()

    # Check if user exists AND if the password is correct
    if user and check_password(user, password):
        # Successful login!
        return jsonify({
            'message': 'Login successful', 
            'user': user.to_dict()
        }), 200
    else:
        # Failed login attempt
        return jsonify({'message': 'Invalid credentials'}), 401