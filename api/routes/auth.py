from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from api.app import db
import models
from datetime import datetime

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user.
    
    Returns:
        JSON response with the result of the registration attempt
    """
    if not request.is_json:
        return jsonify({"error": "Invalid request format. Expected JSON."}), 400
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['username', 'email', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    # Check if user already exists
    username = data['username']
    email = data['email']
    password = data['password']
    
    user_exists = models.User.query.filter_by(username=username).first() or models.User.query.filter_by(email=email).first()
    if user_exists:
        return jsonify({"error": "Username or email already exists"}), 409
    
    # Create new user
    user = models.User(username=username, email=email)
    user.set_password(password)
    
    # Create user profile
    profile = models.UserProfile(user=user)
    
    db.session.add(user)
    db.session.add(profile)
    db.session.commit()
    
    return jsonify({
        "message": "User registered successfully",
        "user_id": user.id
    }), 201

@bp.route('/login', methods=['POST'])
def login():
    """
    Login a user.
    
    Returns:
        JSON response with the result of the login attempt
    """
    if not request.is_json:
        return jsonify({"error": "Invalid request format. Expected JSON."}), 400
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['email', 'password']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    email = data['email']
    password = data['password']
    
    # Check user credentials
    user = models.User.query.filter_by(email=email).first()
    
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401
    
    # Log in the user
    login_user(user)
    
    return jsonify({
        "message": "Login successful",
        "user_id": user.id,
        "username": user.username,
        "is_admin": user.is_admin,
        "profile_completed": user.profile.profile_completed if user.profile else False
    }), 200

@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """
    Logout the current user.
    
    Returns:
        JSON response confirming successful logout
    """
    logout_user()
    return jsonify({"message": "Logout successful"}), 200

@bp.route('/profile', methods=['GET', 'PUT'])
@login_required
def profile():
    """
    Get or update the user's profile.
    
    Returns:
        JSON response with the user's profile or the result of the update
    """
    profile = current_user.profile
    
    if request.method == 'GET':
        # Return the profile data
        return jsonify({
            "full_name": profile.full_name,
            "major": profile.major,
            "university": profile.university,
            "career_interests": profile.career_interests,
            "graduation_year": profile.graduation_year,
            "bio": profile.bio,
            "profile_completed": profile.profile_completed
        }), 200
    
    elif request.method == 'PUT':
        if not request.is_json:
            return jsonify({"error": "Invalid request format. Expected JSON."}), 400
        
        data = request.get_json()
        
        # Update profile fields
        profile.full_name = data.get('full_name', profile.full_name)
        profile.major = data.get('major', profile.major)
        profile.university = data.get('university', profile.university)
        profile.career_interests = data.get('career_interests', profile.career_interests)
        profile.graduation_year = data.get('graduation_year', profile.graduation_year)
        profile.bio = data.get('bio', profile.bio)
        profile.profile_completed = True
        profile.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "message": "Profile updated successfully",
            "profile_completed": profile.profile_completed
        }), 200