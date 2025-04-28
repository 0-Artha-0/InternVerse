from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from api.app import db
import models
import azure_services
from datetime import datetime

bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')

@bp.route('/<int:task_id>', methods=['GET'])
@login_required
def get_task(task_id):
    """
    Get details of a specific task.
    
    Returns:
        JSON response with the task details
    """
    task = models.Task.query.get_or_404(task_id)
    internship = task.internship
    
    # Ensure the task belongs to the current user
    if internship.user_id != current_user.id:
        return jsonify({"error": "You do not have access to this task"}), 403
    
    # Get submissions for this task
    submissions = models.Submission.query.filter_by(
        task_id=task.id,
        user_id=current_user.id
    ).order_by(models.Submission.submitted_at.desc()).all()
    
    submission_list = []
    for submission in submissions:
        submission_list.append({
            "id": submission.id,
            "content": submission.content,
            "file_urls": submission.file_urls,
            "score": submission.score,
            "feedback": submission.feedback,
            "submitted_at": submission.submitted_at.isoformat(),
            "evaluated_at": submission.evaluated_at.isoformat() if submission.evaluated_at else None
        })
    
    # Get industry
    industry = models.Industry.query.get(internship.industry_id)
    
    result = {
        "id": task.id,
        "internship_id": task.internship_id,
        "internship_title": internship.title,
        "industry": industry.name if industry else None,
        "title": task.title,
        "description": task.description,
        "instructions": task.instructions,
        "difficulty": task.difficulty,
        "points": task.points,
        "status": task.status,
        "deadline": task.deadline.isoformat() if task.deadline else None,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
        "submissions": submission_list
    }
    
    return jsonify(result), 200

@bp.route('/<int:task_id>/submissions', methods=['POST'])
@login_required
def submit_task(task_id):
    """
    Submit a response for a task.
    
    Returns:
        JSON response with the submission details
    """
    task = models.Task.query.get_or_404(task_id)
    internship = task.internship
    
    # Ensure the task belongs to the current user
    if internship.user_id != current_user.id:
        return jsonify({"error": "You do not have access to this task"}), 403
    
    if not request.is_json:
        return jsonify({"error": "Invalid request format. Expected JSON."}), 400
    
    data = request.get_json()
    
    # Validate required fields
    if 'content' not in data:
        return jsonify({"error": "Missing required field: content"}), 400
    
    content = data['content']
    file_urls = data.get('file_urls')
    
    # Create submission
    submission = models.Submission(
        task_id=task.id,
        user_id=current_user.id,
        content=content,
        file_urls=file_urls,
        submitted_at=datetime.utcnow()
    )
    
    # Update task status
    task.status = 'submitted'
    
    db.session.add(submission)
    db.session.commit()
    
    # Trigger asynchronous evaluation via Azure Function
    azure_services.evaluate_submission(submission.id)
    
    return jsonify({
        "message": "Submission received",
        "submission_id": submission.id,
        "task_id": task.id
    }), 201

@bp.route('/submissions/<int:submission_id>', methods=['GET'])
@login_required
def get_submission(submission_id):
    """
    Get details of a specific submission.
    
    Returns:
        JSON response with the submission details
    """
    submission = models.Submission.query.get_or_404(submission_id)
    
    # Ensure the submission belongs to the current user
    if submission.user_id != current_user.id:
        return jsonify({"error": "You do not have access to this submission"}), 403
    
    task = models.Task.query.get(submission.task_id)
    
    result = {
        "id": submission.id,
        "task_id": submission.task_id,
        "task_title": task.title if task else None,
        "content": submission.content,
        "file_urls": submission.file_urls,
        "score": submission.score,
        "feedback": submission.feedback,
        "submitted_at": submission.submitted_at.isoformat(),
        "evaluated_at": submission.evaluated_at.isoformat() if submission.evaluated_at else None,
        "is_evaluated": submission.evaluated_at is not None
    }
    
    return jsonify(result), 200