from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from api.app import db
import models
import azure_services
from datetime import datetime, timedelta

bp = Blueprint('internships', __name__, url_prefix='/api/internships')

@bp.route('/industries', methods=['GET'])
@login_required
def get_industries():
    """
    Get all available industries.
    
    Returns:
        JSON response with all industries
    """
    industries = models.Industry.query.all()
    
    result = []
    for industry in industries:
        result.append({
            "id": industry.id,
            "name": industry.name,
            "description": industry.description,
            "icon": industry.icon
        })
    
    return jsonify(result), 200

@bp.route('/companies', methods=['GET'])
@login_required
def get_companies():
    """
    Get all available companies, optionally filtered by industry.
    
    Query Parameters:
        industry_id: Optional - Filter companies by industry ID
    
    Returns:
        JSON response with companies matching the filter
    """
    industry_id = request.args.get('industry_id', type=int)
    
    query = models.Company.query
    if industry_id:
        query = query.filter_by(industry_id=industry_id)
        
    companies = query.all()
    
    result = []
    for company in companies:
        result.append({
            "id": company.id,
            "name": company.name,
            "industry_id": company.industry_id,
            "industry_name": company.industry.name,
            "description": company.description,
            "logo": company.logo,
            "website": company.website,
            "location": company.location
        })
    
    return jsonify(result), 200

@bp.route('/start', methods=['POST'])
@login_required
def start_internship():
    """
    Start a new internship for the current user.
    
    Returns:
        JSON response with the new internship details
    """
    # Check if profile is complete
    if not current_user.profile.profile_completed:
        return jsonify({"error": "Please complete your profile first"}), 400
    
    if not request.is_json:
        return jsonify({"error": "Invalid request format. Expected JSON."}), 400
    
    data = request.get_json()
    
    # Validate required fields
    if 'industry_id' not in data:
        return jsonify({"error": "Missing required field: industry_id"}), 400
    
    industry_id = data['industry_id']
    company_id = data.get('company_id')
    
    # Get industry
    industry = models.Industry.query.get(industry_id)
    if not industry:
        return jsonify({"error": f"Industry with ID {industry_id} not found"}), 404
    
    # Get company if specified
    company = None
    if company_id:
        company = models.Company.query.get(company_id)
        if not company:
            return jsonify({"error": f"Company with ID {company_id} not found"}), 404
    
    # Generate internship details using Azure OpenAI
    internship_details = azure_services.generate_internship(
        industry.name, 
        current_user.profile.major,
        current_user.profile.career_interests
    )
    
    # Create new internship track
    internship = models.InternshipTrack(
        industry_id=industry.id,
        user_id=current_user.id,
        company_id=company.id if company else None,
        title=internship_details['title'],
        description=internship_details['description'],
        duration_weeks=internship_details['duration_weeks'],
        status='active',
        progress=0.0,
        started_at=datetime.utcnow()
    )
    
    db.session.add(internship)
    db.session.flush()  # To get the internship ID
    
    # Generate initial tasks
    tasks = azure_services.generate_tasks(
        internship_details['title'],
        industry.name,
        current_user.profile.major,
        1  # Initial week
    )
    
    # Create tasks in database
    for task_data in tasks:
        task = models.Task(
            internship_id=internship.id,
            title=task_data['title'],
            description=task_data['description'],
            instructions=task_data['instructions'],
            difficulty=task_data['difficulty'],
            points=task_data['points'],
            status='pending',
            deadline=datetime.utcnow() + timedelta(days=7)
        )
        db.session.add(task)
    
    db.session.commit()
    
    return jsonify({
        "message": f"Started new internship: {internship.title}",
        "internship_id": internship.id,
        "title": internship.title,
        "description": internship.description,
        "industry": industry.name,
        "company": company.name if company else None,
        "duration_weeks": internship.duration_weeks
    }), 201

@bp.route('/', methods=['GET'])
@login_required
def get_internships():
    """
    Get all internships for the current user.
    
    Query Parameters:
        status: Optional - Filter internships by status (active, completed, abandoned)
    
    Returns:
        JSON response with the user's internships
    """
    status = request.args.get('status')
    
    query = models.InternshipTrack.query.filter_by(user_id=current_user.id)
    if status:
        query = query.filter_by(status=status)
        
    internships = query.order_by(models.InternshipTrack.started_at.desc()).all()
    
    result = []
    for internship in internships:
        # Get the associated industry and company
        industry = models.Industry.query.get(internship.industry_id)
        company = models.Company.query.get(internship.company_id) if internship.company_id else None
        
        # Get the completion certificate if available
        certificate = models.Certificate.query.filter_by(internship_id=internship.id).first()
        
        result.append({
            "id": internship.id,
            "title": internship.title,
            "description": internship.description,
            "industry_id": internship.industry_id,
            "industry_name": industry.name if industry else None,
            "company_id": internship.company_id,
            "company_name": company.name if company else None,
            "duration_weeks": internship.duration_weeks,
            "status": internship.status,
            "progress": internship.progress,
            "started_at": internship.started_at.isoformat(),
            "completed_at": internship.completed_at.isoformat() if internship.completed_at else None,
            "certificate_id": certificate.id if certificate else None
        })
    
    return jsonify(result), 200

@bp.route('/<int:internship_id>', methods=['GET'])
@login_required
def get_internship(internship_id):
    """
    Get details of a specific internship.
    
    Returns:
        JSON response with the internship details
    """
    internship = models.InternshipTrack.query.get_or_404(internship_id)
    
    # Ensure the internship belongs to the current user
    if internship.user_id != current_user.id:
        return jsonify({"error": "You do not have access to this internship"}), 403
    
    # Get the associated industry and company
    industry = models.Industry.query.get(internship.industry_id)
    company = models.Company.query.get(internship.company_id) if internship.company_id else None
    
    # Get tasks for this internship
    tasks = models.Task.query.filter_by(internship_id=internship.id).order_by(models.Task.created_at).all()
    
    task_list = []
    for task in tasks:
        # Get the latest submission for this task
        submission = models.Submission.query.filter_by(
            task_id=task.id,
            user_id=current_user.id
        ).order_by(models.Submission.submitted_at.desc()).first()
        
        task_list.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "instructions": task.instructions,
            "difficulty": task.difficulty,
            "points": task.points,
            "status": task.status,
            "deadline": task.deadline.isoformat() if task.deadline else None,
            "created_at": task.created_at.isoformat(),
            "has_submission": submission is not None,
            "submission_score": submission.score if submission else None
        })
    
    # Get the completion certificate if available
    certificate = models.Certificate.query.filter_by(internship_id=internship.id).first()
    
    result = {
        "id": internship.id,
        "title": internship.title,
        "description": internship.description,
        "industry_id": internship.industry_id,
        "industry_name": industry.name if industry else None,
        "industry_icon": industry.icon if industry else None,
        "company_id": internship.company_id,
        "company_name": company.name if company else None,
        "company_logo": company.logo if company else None,
        "duration_weeks": internship.duration_weeks,
        "status": internship.status,
        "progress": internship.progress,
        "started_at": internship.started_at.isoformat(),
        "completed_at": internship.completed_at.isoformat() if internship.completed_at else None,
        "tasks": task_list,
        "certificate_id": certificate.id if certificate else None
    }
    
    return jsonify(result), 200

@bp.route('/<int:internship_id>/complete', methods=['POST'])
@login_required
def complete_internship(internship_id):
    """
    Mark an internship as completed and generate a certificate.
    
    Returns:
        JSON response with completion and certificate details
    """
    internship = models.InternshipTrack.query.get_or_404(internship_id)
    
    # Ensure the internship belongs to the current user
    if internship.user_id != current_user.id:
        return jsonify({"error": "You do not have access to this internship"}), 403
    
    # Check if already completed
    if internship.status == 'completed':
        return jsonify({"error": "This internship is already completed"}), 400
    
    # Check if certificate already exists
    existing_certificate = models.Certificate.query.filter_by(internship_id=internship.id).first()
    if existing_certificate:
        return jsonify({
            "message": "Internship already has a certificate",
            "certificate_id": existing_certificate.id
        }), 200
    
    # Get industry
    industry = models.Industry.query.get(internship.industry_id)
    
    # Get completed tasks count and average score
    tasks_count = models.Task.query.filter_by(internship_id=internship.id).count()
    completed_submissions = models.Submission.query.join(
        models.Task, models.Submission.task_id == models.Task.id
    ).filter(
        models.Task.internship_id == internship.id,
        models.Submission.user_id == current_user.id,
        models.Submission.score.isnot(None)
    ).all()
    
    completed_count = len(completed_submissions)
    avg_score = sum(s.score for s in completed_submissions) / completed_count if completed_count > 0 else 0
    
    # Generate certificate using Azure OpenAI
    certificate_data = azure_services.generate_certificate(
        current_user.profile.full_name,
        internship.title,
        industry.name,
        completed_count,
        avg_score
    )
    
    # Create certificate in database
    certificate = models.Certificate(
        internship_id=internship.id,
        user_id=current_user.id,
        title=certificate_data['title'],
        description=certificate_data['description'],
        score=avg_score,
        skills_acquired=certificate_data['skills'],
        issued_at=datetime.utcnow()
    )
    
    # Update internship status
    internship.status = 'completed'
    internship.completed_at = datetime.utcnow()
    internship.progress = 100.0
    
    db.session.add(certificate)
    db.session.commit()
    
    return jsonify({
        "message": "Internship completed successfully",
        "certificate_id": certificate.id,
        "certificate_title": certificate.title,
        "score": certificate.score,
        "skills": certificate.skills_acquired
    }), 200