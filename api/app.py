import logging
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager


# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass


# create the backend API app
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Load configuration from config.py
app.config.from_pyfile('../config.py')

# Set secret key
app.secret_key = app.config.get('SECRET_KEY')

# Initialize SQLAlchemy with app
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Configure login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

with app.app_context():
    # Import models here to avoid circular imports
    import models
    
    # Create all tables
    db.create_all()
    
    # Setup the login manager loader
    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))
    
    # Import API routes
    from api.routes import auth, internships, tasks, supervisor
    
    # Register blueprints
    app.register_blueprint(auth.bp)
    app.register_blueprint(internships.bp)
    app.register_blueprint(tasks.bp)
    app.register_blueprint(supervisor.bp)