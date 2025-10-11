from flask import Blueprint, jsonify, request
from models import db, Announcement # Import necessary items

# Create a Blueprint to manage the announcement routes
announcement_api = Blueprint('announcement_api', __name__)

# --- API ROUTES for ANNOUNCEMENTS ---

# Route to get all announcements OR post a new one
@announcement_api.route('/', methods=['GET', 'POST'])
def handle_all_announcements():
    if request.method == 'GET':
        # Get all announcements from the database
        all_posts = Announcement.query.all()
        # Convert the posts to the web-friendly format
        return jsonify([post.to_dict() for post in all_posts])

    elif request.method == 'POST':
        # Get the new data from the user
        data = request.get_json()
        
        # Create a new Announcement object
        new_post = Announcement(
            title=data['title'],
            text=data['content']
        )
        
        # Save and apply changes to the database
        db.session.add(new_post)
        db.session.commit()
        
        # Return the new post's data (201 means 'Created')
        return jsonify(new_post.to_dict()), 201


# Route to handle one specific announcement (by its ID)
@announcement_api.route('/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def handle_single_announcement(id):
    # Find the announcement by ID or return a Not Found error
    post = Announcement.query.get_or_404(id)

    if request.method == 'GET':
        return jsonify(post.to_dict())

    elif request.method == 'PUT':
        # Update the existing post's details
        data = request.get_json()
        post.title = data.get('title', post.title)
        post.text = data.get('content', post.text)
        
        db.session.commit()
        return jsonify(post.to_dict())

    elif request.method == 'DELETE':
        # Remove the post from the database
        db.session.delete(post)
        db.session.commit()
        # 204 means 'No Content' (successful delete)
        return '', 204