from datetime import datetime
from app import db

class Industry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(100), nullable=True)
    tracks = db.relationship('InternshipTrack', backref='industry', lazy=True)
    companies = db.relationship('Company', backref='industry', lazy=True)
    roles = db.relationship('Role', backref='industry', lazy=True)
    
    def __repr__(self):
        return f'<Industry {self.name}>'


class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    industry_id = db.Column(db.Integer, db.ForeignKey('industry.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    logo = db.Column(db.String(100), nullable=True)
    website = db.Column(db.String(200), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    internships = db.relationship('InternshipTrack', backref='company', lazy=True)
    roles = db.relationship('Role', backref='company', lazy=True)
    
    def __repr__(self):
        return f'<Company {self.name}>'


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    industry_id = db.Column(db.Integer, db.ForeignKey('industry.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.Text, nullable=True)
    skills_required = db.Column(db.String(255), nullable=True)  # Comma-separated list of skills
    experience_level = db.Column(db.String(50), nullable=True)  # Entry, Mid, Senior
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    internships = db.relationship('InternshipTrack', backref='role', lazy=True)
    
    def __repr__(self):
        return f'<Role {self.name}>'


class InternshipTrack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    industry_id = db.Column(db.Integer, db.ForeignKey('industry.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=True)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    duration_weeks = db.Column(db.Integer, default=4)
    status = db.Column(db.String(20), default='active')  # active, completed, abandoned
    progress = db.Column(db.Float, default=0.0)  # 0-100%
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    tasks = db.relationship('Task', backref='internship', lazy=True)
    certificate = db.relationship('Certificate', backref='internship', uselist=False)
    
    def __repr__(self):
        return f'<InternshipTrack {self.title}>'


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    internship_id = db.Column(db.Integer, db.ForeignKey('internship_track.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(20), default='medium')  # easy, medium, hard
    points = db.Column(db.Integer, default=100)
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, submitted, evaluated
    deadline = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submissions = db.relationship('Submission', backref='task', lazy=True)
    
    def __repr__(self):
        return f'<Task {self.title}>'


class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    file_urls = db.Column(db.Text, nullable=True)  # Comma-separated URLs
    score = db.Column(db.Float, nullable=True)  # 0-100
    feedback = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    evaluated_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Submission {self.id}>'


class Certificate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    internship_id = db.Column(db.Integer, db.ForeignKey('internship_track.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    score = db.Column(db.Float, nullable=False)
    skills_acquired = db.Column(db.Text, nullable=False)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    certificate_url = db.Column(db.String(200), nullable=True)
    
    def __repr__(self):
        return f'<Certificate {self.title}>'