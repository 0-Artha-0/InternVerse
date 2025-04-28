from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import models
import ai_supervisor

bp = Blueprint('supervisor', __name__, url_prefix='/api/supervisor')

@bp.route('/ask', methods=['POST'])
@login_required
def ask_supervisor():
    """
    Ask a question to the AI supervisor.
    
    Returns:
        JSON response with the AI supervisor's answer
    """
    if not request.is_json:
        return jsonify({"error": "Invalid request format. Expected JSON."}), 400
    
    data = request.get_json()
    
    # Validate required fields
    if 'question' not in data:
        return jsonify({"error": "Missing required field: question"}), 400
    
    question = data['question']
    internship_id = data.get('internship_id')
    task_id = data.get('task_id')
    
    # Get context information
    internship = None
    task = None
    
    if internship_id:
        internship = models.InternshipTrack.query.get(internship_id)
        
        # Ensure the internship belongs to the current user
        if internship and internship.user_id != current_user.id:
            return jsonify({"error": "You do not have access to this internship"}), 403
    
    if task_id:
        task = models.Task.query.get(task_id)
        
        # Ensure the task belongs to the current user
        if task and task.internship.user_id != current_user.id:
            return jsonify({"error": "You do not have access to this task"}), 403
        
        # If task is provided but internship is not, get the internship from the task
        if task and not internship:
            internship = task.internship
    
    # Generate response using AI supervisor
    response = ai_supervisor.ask_question(
        question, 
        current_user.profile,
        internship,
        task
    )
    
    return jsonify({"response": response}), 200

@bp.route('/resources', methods=['POST'])
@login_required
def get_resources():
    """
    Get learning resources related to a task.
    
    Returns:
        JSON response with suggested resources
    """
    if not request.is_json:
        return jsonify({"error": "Invalid request format. Expected JSON."}), 400
    
    data = request.get_json()
    
    # Validate required fields
    if 'task_id' not in data:
        return jsonify({"error": "Missing required field: task_id"}), 400
    
    task_id = data['task_id']
    
    # Get task
    task = models.Task.query.get_or_404(task_id)
    
    # Ensure the task belongs to the current user
    if task.internship.user_id != current_user.id:
        return jsonify({"error": "You do not have access to this task"}), 403
    
    # Get industry
    industry = models.Industry.query.get(task.internship.industry_id)
    
    # Generate resources using AI supervisor
    resources = ai_supervisor.suggest_resources(
        task.title,
        task.description,
        industry.name if industry else "general"
    )
    
    return jsonify({"resources": resources}), 200

@bp.route('/certificates/<int:certificate_id>', methods=['GET'])
@login_required
def get_certificate(certificate_id):
    """
    Get details of a specific certificate.
    
    Returns:
        JSON response with the certificate details
    """
    certificate = models.Certificate.query.get_or_404(certificate_id)
    
    # Ensure the certificate belongs to the current user
    if certificate.user_id != current_user.id:
        return jsonify({"error": "You do not have access to this certificate"}), 403
    
    internship = models.InternshipTrack.query.get(certificate.internship_id)
    industry = models.Industry.query.get(internship.industry_id) if internship else None
    
    result = {
        "id": certificate.id,
        "title": certificate.title,
        "description": certificate.description,
        "internship_id": certificate.internship_id,
        "internship_title": internship.title if internship else None,
        "industry": industry.name if industry else None,
        "score": certificate.score,
        "skills_acquired": certificate.skills_acquired,
        "issued_at": certificate.issued_at.isoformat(),
        "certificate_url": certificate.certificate_url
    }
    
    return jsonify(result), 200