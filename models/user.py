from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    profile = db.relationship('UserProfile', backref='user', uselist=False)
    internships = db.relationship('InternshipTrack', backref='user', lazy=True)
    submissions = db.relationship('Submission', backref='user', lazy=True)
    certificates = db.relationship('Certificate', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    full_name = db.Column(db.String(100), nullable=True)
    major = db.Column(db.String(100), nullable=True)
    university = db.Column(db.String(100), nullable=True)
    career_interests = db.Column(db.String(200), nullable=True)
    graduation_year = db.Column(db.Integer, nullable=True)
    bio = db.Column(db.Text, nullable=True)
    profile_completed = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserProfile {self.full_name}>'


class AdminUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    organization = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    access_level = db.Column(db.String(20), default='standard')  # standard, advanced, super
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='admin_profile')
    
    def __repr__(self):
        return f'<AdminUser {self.role}>'