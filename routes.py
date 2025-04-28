import logging
from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import check_password_hash
from app import app, db
from models.user import User, UserProfile, AdminUser
from models.internship import Industry, InternshipTrack, Company, Role, Task, Submission, Certificate
from services.supervisor_service import ask_question, generate_feedback, suggest_resources
from services.azure_services import generate_internship, generate_tasks, evaluate_submission, generate_certificate

logger = logging.getLogger(__name__)

# Public routes
@app.route('/')
def index():
    """Landing page"""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        profile = UserProfile(user=user)
        
        db.session.add(user)
        db.session.add(profile)
        db.session.commit()
        
        login_user(user)
        flash('Registration successful! Please complete your profile.', 'success')
        return redirect(url_for('profile'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    return redirect(url_for('index'))

# User routes
@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    internships = InternshipTrack.query.filter_by(user_id=current_user.id).all()
    
    # Split internships into active and completed
    active_internships = []
    completed_internships = []
    
    for internship in internships:
        if internship.status == 'active':
            active_internships.append(internship)
        elif internship.status == 'completed':
            completed_internships.append(internship)
    
    # Get certificates
    certificates = Certificate.query.filter_by(user_id=current_user.id).all()
    
    # Get pending tasks from active internships
    pending_tasks = []
    for internship in active_internships:
        tasks = Task.query.filter(
            Task.internship_id == internship.id,
            Task.status.in_(['pending', 'in_progress'])
        ).all()
        pending_tasks.extend(tasks)
    
    return render_template('dashboard.html', 
                          internships=internships,
                          active_internships=active_internships,
                          completed_internships=completed_internships,
                          certificates=certificates,
                          pending_tasks=pending_tasks)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management"""
    profile = current_user.profile
    
    if request.method == 'POST':
        profile.full_name = request.form.get('full_name')
        profile.major = request.form.get('major')
        profile.university = request.form.get('university')
        profile.career_interests = request.form.get('career_interests')
        profile.graduation_year = request.form.get('graduation_year')
        profile.bio = request.form.get('bio')
        profile.profile_completed = True
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('profile.html', profile=profile)

@app.route('/industries')
@login_required
def industries():
    """Browse available industries"""
    industries = Industry.query.all()
    return render_template('industries.html', industries=industries)

@app.route('/internship/start/<int:industry_id>', methods=['GET', 'POST'])
@login_required
def start_internship(industry_id):
    """Start a new internship"""
    industry = Industry.query.get_or_404(industry_id)
    companies = Company.query.filter_by(industry_id=industry_id).all()
    roles = Role.query.filter_by(industry_id=industry_id).all()
    
    if request.method == 'POST':
        if not current_user.profile or not current_user.profile.profile_completed:
            flash('Please complete your profile before starting an internship', 'warning')
            return redirect(url_for('profile'))
            
        company_id = request.form.get('company_id')
        role_id = request.form.get('role_id')
        
        profile = current_user.profile
        
        # Get the selected company and role
        company = None
        role = None
        
        if company_id:
            company = Company.query.get(company_id)
        
        if role_id:
            role = Role.query.get(role_id)
            
            # If role is company-specific, make sure company matches
            if role and role.company_id and (not company_id or int(company_id) != role.company_id):
                company = Company.query.get(role.company_id)
                company_id = company.id if company else None
        
        # Generate internship details using AI
        internship_details = generate_internship(
            industry=industry.name, 
            major=profile.major or "Undeclared", 
            interests=profile.career_interests or "General"
        )
        
        # Use role information if available
        title = f"{industry.name} Internship"
        description = "Virtual internship experience"
        
        if role:
            title = f"{role.name} at {company.name if company else 'Virtual Company'}"
            description = role.description
        elif internship_details:
            title = internship_details.get('title', title)
            description = internship_details.get('description', description)
        
        internship = InternshipTrack(
            industry_id=industry_id,
            user_id=current_user.id,
            company_id=company_id if company_id else None,
            role_id=role_id if role_id else None,
            title=title,
            description=description,
            duration_weeks=internship_details.get('duration_weeks', 4)
        )
        
        db.session.add(internship)
        db.session.commit()
        
        # Generate initial tasks
        logger.info(f"Generating tasks for internship {internship.id}: {internship.title}")
        
        task_list = generate_tasks(
            internship_title=internship.title,
            industry=industry.name,
            major=profile.major or "Undeclared", 
            week=1
        )
        
        # Log the number of tasks generated
        logger.info(f"Generated {len(task_list)} tasks for internship {internship.id}")
        
        # Ensure we have valid task data
        if not task_list or len(task_list) == 0:
            logger.warning(f"No tasks were generated for internship {internship.id}. Using fallback tasks.")
            # Create fallback tasks if none were generated
            task_list = [
                {
                    "title": f"Week 1: Introduction to {industry.name}",
                    "description": f"Learn about the fundamentals of {industry.name} and get familiar with key concepts in this field.",
                    "instructions": "Research the current trends and challenges in this industry. Write a 500-word summary of your findings.",
                    "difficulty": "easy",
                    "points": 100
                },
                {
                    "title": f"Week 1: {role.name if role else 'Professional'} Skills Assessment",
                    "description": "Evaluate your current skills related to this internship and identify areas for development.",
                    "instructions": "Create a skills matrix that lists your strengths and areas for improvement. Then develop a learning plan for the duration of the internship.",
                    "difficulty": "medium",
                    "points": 120
                },
                {
                    "title": f"Week 1: {company.name if company else 'Company'} Analysis",
                    "description": f"Research and analyze the structure, products, and market position of {company.name if company else 'your chosen company'}.",
                    "instructions": "Prepare a brief report on the company's business model, competitive advantages, and challenges in the current market.",
                    "difficulty": "medium", 
                    "points": 150
                }
            ]
            
        for task_data in task_list:
            task = Task(
                internship_id=internship.id,
                title=task_data.get('title', f"Week 1 Task for {industry.name}"),
                description=task_data.get('description', "Complete this task as part of your virtual internship."),
                instructions=task_data.get('instructions', "Follow the instructions carefully and submit your work."),
                difficulty=task_data.get('difficulty', 'medium'),
                points=task_data.get('points', 100)
            )
            db.session.add(task)
            logger.info(f"Added task: {task.title}")
        
        db.session.commit()
        logger.info(f"Committed {len(task_list)} tasks to the database for internship {internship.id}")
        flash('Internship started successfully!', 'success')
        return redirect(url_for('internship_detail', internship_id=internship.id))
    
    return render_template('start_internship.html', industry=industry, companies=companies, roles=roles)

@app.route('/internship/<int:internship_id>', methods=['GET', 'POST'])
@login_required
def internship_detail(internship_id):
    """View internship details and tasks"""
    internship = InternshipTrack.query.get_or_404(internship_id)
    
    # Ensure user owns this internship
    if internship.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
        
    # Handle delete internship request
    if request.method == 'POST' and 'action' in request.form and request.form['action'] == 'delete_internship':
        try:
            # First delete all associated tasks and submissions
            tasks = Task.query.filter_by(internship_id=internship_id).all()
            for task in tasks:
                submissions = Submission.query.filter_by(task_id=task.id).all()
                for submission in submissions:
                    db.session.delete(submission)
                db.session.delete(task)
                
            # Delete any certificates
            certificates = Certificate.query.filter_by(internship_id=internship_id).all()
            for cert in certificates:
                db.session.delete(cert)
                
            # Finally delete the internship
            db.session.delete(internship)
            db.session.commit()
            
            flash('Internship successfully deleted!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            logger.error(f"Error deleting internship: {e}")
            flash('An error occurred while deleting the internship', 'danger')
            db.session.rollback()
    
    # Get the related industry for the internship
    industry = Industry.query.get(internship.industry_id)
    
    # Get the company if it exists
    company = None
    if internship.company_id:
        company = Company.query.get(internship.company_id)
    
    # Get the role if it exists
    role = None
    if internship.role_id:
        role = Role.query.get(internship.role_id)
    
    tasks = Task.query.filter_by(internship_id=internship_id).all()
    
    # Log task information
    logger.info(f"Found {len(tasks)} tasks for internship {internship_id}")
    if len(tasks) == 0:
        logger.warning(f"No tasks found for internship {internship_id}")
        
        # Create default tasks if none exist
        from services.azure_services import generate_tasks
        
        try:
            # Generate tasks
            task_list = generate_tasks(
                internship_title=internship.title,
                industry=industry.name if industry else "General",
                major=current_user.profile.major if current_user.profile else "Undeclared",
                week=1
            )
            
            logger.info(f"Generated {len(task_list)} tasks for empty internship")
            
            # Create tasks in the database
            for task_data in task_list:
                task = Task(
                    internship_id=internship_id,
                    title=task_data.get('title', "Week 1 Task"),
                    description=task_data.get('description', "Complete this task as part of your virtual internship."),
                    instructions=task_data.get('instructions', "Follow the instructions carefully and submit your work."),
                    difficulty=task_data.get('difficulty', 'medium'),
                    points=task_data.get('points', 100)
                )
                db.session.add(task)
                logger.info(f"Added new task: {task.title}")
            
            db.session.commit()
            
            # Reload tasks
            tasks = Task.query.filter_by(internship_id=internship_id).all()
            logger.info(f"Now have {len(tasks)} tasks for internship {internship_id}")
            
        except Exception as e:
            logger.error(f"Failed to generate tasks for empty internship: {e}")
    
    return render_template('internship.html', internship=internship, tasks=tasks, industry=industry, company=company, role=role)

@app.route('/task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def task_detail(task_id):
    """View and submit a task"""
    task = Task.query.get_or_404(task_id)
    internship = task.internship
    
    # Ensure user owns this task
    if internship.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    submission = Submission.query.filter_by(task_id=task_id, user_id=current_user.id).order_by(Submission.submitted_at.desc()).first()
    
    if request.method == 'POST':
        submission_content = request.form.get('content')
        
        # Handle file uploads
        file_urls = []
        if 'attachments' in request.files:
            files = request.files.getlist('attachments')
            for file in files:
                if file and file.filename:
                    # In a production environment, we would upload to cloud storage
                    # For this demo, we'll just record the filename
                    # You would use Azure Blob Storage or another cloud storage service
                    file_urls.append(f"/uploads/{file.filename}")
                    logger.info(f"File would be uploaded: {file.filename}")
        
        # Join file URLs with commas for storage
        file_urls_str = ','.join(file_urls) if file_urls else ''
        
        new_submission = Submission(
            task_id=task_id,
            user_id=current_user.id,
            content=submission_content,
            file_urls=file_urls_str
        )
        
        task.status = 'submitted'
        
        db.session.add(new_submission)
        db.session.commit()
        
        # Trigger evaluation in background
        try:
            evaluate_submission(new_submission.id)
        except Exception as e:
            logger.error(f"Failed to trigger submission evaluation: {e}")
        
        flash('Task submitted successfully!', 'success')
        return redirect(url_for('task_detail', task_id=task_id))
    
    # Get suggested resources
    resources = []
    if not submission:
        try:
            resources = suggest_resources(
                task_title=task.title,
                task_description=task.description,
                industry=internship.industry.name
            )
        except Exception as e:
            logger.error(f"Failed to get resources: {e}")
    
    return render_template('task_detail.html', task=task, internship=internship, submission=submission, resources=resources)

@app.route('/ask-supervisor', methods=['POST'])
@login_required
def ask_supervisor():
    """Ask the AI supervisor a question"""
    question = request.form.get('question')
    internship_id = request.form.get('internship_id')
    task_id = request.form.get('task_id')
    
    logger.info(f"AI Supervisor: Question received: '{question}'")
    logger.info(f"AI Supervisor: Internship ID: {internship_id}, Task ID: {task_id}")
    
    internship = None
    task = None
    
    if internship_id:
        internship = InternshipTrack.query.get(internship_id)
        logger.info(f"AI Supervisor: Internship found: {internship.title if internship else 'None'}")
    
    if task_id:
        task = Task.query.get(task_id)
        if task:
            internship = task.internship
            logger.info(f"AI Supervisor: Task found: {task.title if task else 'None'}")
    
    try:
        logger.info("AI Supervisor: Calling ask_question service function")
        response = ask_question(
            question=question,
            user_profile=current_user.profile,
            internship=internship,
            task=task
        )
        logger.info(f"AI Supervisor: Response received (first 50 chars): '{response[:50]}...'")
        return jsonify({'response': response})
    except Exception as e:
        logger.error(f"Failed to get supervisor response: {e}")
        return jsonify({'error': 'Failed to get a response from the supervisor'}), 500

@app.route('/certificate/<int:certificate_id>')
@login_required
def view_certificate(certificate_id):
    """View a completed internship certificate"""
    certificate = Certificate.query.get_or_404(certificate_id)
    
    # Ensure user owns this certificate
    if certificate.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('certificate.html', certificate=certificate)

# Admin routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard"""
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    user_count = User.query.count()
    internship_count = InternshipTrack.query.count()
    submission_count = Submission.query.count()
    certificate_count = Certificate.query.count()
    
    return render_template('admin/dashboard.html', 
                           user_count=user_count, 
                           internship_count=internship_count,
                           submission_count=submission_count,
                           certificate_count=certificate_count)

@app.route('/admin/analytics')
@login_required
def admin_analytics():
    """Admin analytics dashboard"""
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('admin/analytics.html')

@app.route('/admin/users')
@login_required
def admin_users():
    """Admin user management"""
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/internships')
@login_required
def admin_internships():
    """Admin internship management"""
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    internships = InternshipTrack.query.all()
    return render_template('admin/internships.html', internships=internships)

# Data initialization route
@app.route('/admin/initialize-data')
@login_required
def initialize_data():
    """Initialize sample data for the application"""
    if not current_user.is_admin:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    # Import the data initialization function
    from api.init_data import initialize_data
    
    try:
        initialize_data(force=True)
        flash('Data initialized successfully!', 'success')
    except Exception as e:
        logger.error(f"Failed to initialize data: {e}")
        flash(f'Failed to initialize data: {str(e)}', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/api/generate_companies_roles/<industry_id>')
@login_required
def generate_companies_roles_for_industry(industry_id):
    """
    Generate AI-powered companies and roles for a specific industry
    
    Args:
        industry_id (int): The ID of the industry to generate companies and roles for
    """
    try:
        industry = Industry.query.get_or_404(industry_id)
        
        # Import the company generation function
        from services.azure_services import generate_companies_and_roles
        
        # Generate companies and roles
        industry_data = generate_companies_and_roles(industry.name)
        
        # Process the generated companies
        created_companies = []
        created_roles = []
        
        # Add generated companies
        if "companies" in industry_data and industry_data["companies"]:
            for company_data in industry_data["companies"]:
                if "name" not in company_data or not company_data["name"]:
                    continue
                    
                company_obj = Company.query.filter_by(name=company_data["name"]).first()
                if not company_obj:
                    company_obj = Company(
                        name=company_data["name"],
                        industry_id=industry.id,
                        description=company_data.get("description", f"A company in the {industry.name} industry"),
                        location=company_data.get("location", "Global"),
                    )
                    db.session.add(company_obj)
                    created_companies.append(company_obj.name)
        
        # Commit to get company IDs
        db.session.commit()
        
        # Get all companies for this industry
        companies = Company.query.filter_by(industry_id=industry.id).all()
        company_dict = {company.name: company for company in companies}
        
        # Add generated roles
        if "roles" in industry_data and industry_data["roles"]:
            for role_data in industry_data["roles"]:
                if "name" not in role_data or not role_data["name"]:
                    continue
                    
                # Find the matching company
                company_obj = None
                if "company_name" in role_data and role_data["company_name"]:
                    company_obj = company_dict.get(role_data["company_name"])
                
                # If no matching company is found, assign to the first company or skip
                if not company_obj and companies:
                    company_obj = companies[0]
                
                if not company_obj:
                    continue
                    
                role_obj = Role.query.filter_by(
                    name=role_data["name"], 
                    industry_id=industry.id,
                    company_id=company_obj.id
                ).first()
                
                if not role_obj:
                    role_obj = Role(
                        name=role_data["name"],
                        industry_id=industry.id,
                        company_id=company_obj.id,
                        description=role_data.get("description", f"A role in the {industry.name} industry"),
                        requirements=role_data.get("requirements", "No specific requirements"),
                        skills_required=role_data.get("skills_required", ""),
                        experience_level=role_data.get("experience_level", "Entry")
                    )
                    db.session.add(role_obj)
                    created_roles.append(role_obj.name)
        
        # Commit all changes
        db.session.commit()
        
        # Success message
        flash(f'Generated {len(created_companies)} new companies and {len(created_roles)} new roles for {industry.name}!', 'success')
        
    except Exception as e:
        logger.error(f"Failed to generate companies and roles: {e}")
        flash(f'Failed to generate companies and roles: {str(e)}', 'danger')
    
    # Redirect back to start internship page
    return redirect(url_for('start_internship', industry_id=industry_id))