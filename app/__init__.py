from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from urllib.parse import urlparse, urlunparse

# Load environment variables
load_dotenv()

# Initialize SQLAlchemy
db = SQLAlchemy()

def get_database_url():
    """Configure database URL with proper SSL settings"""
    database_url = os.environ.get('DATABASE_URL')

    if not database_url:
        return 'sqlite:///cloudripper.db'

    # Handle Render's PostgreSQL URL format
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    # Parse the URL
    parsed = urlparse(database_url)

    # Only use sslmode parameter
    ssl_params = ["sslmode=require"]

    # Combine existing query parameters with SSL parameters
    existing_params = parsed.query.split('&') if parsed.query else []
    all_params = existing_params + ssl_params
    query = '&'.join(param for param in all_params if param)

    # Reconstruct the URL with SSL parameters
    modified_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        query,
        parsed.fragment
    ))

    return modified_url

def create_app():
    app = Flask(__name__)

    # Configure the app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-cloudripper')

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = get_database_url()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "connect_args": {
            "sslmode": "require",
            "connect_timeout": 30
        }
    }

    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')

    # Ensure download directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Rest of your logging setup...

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # Create database tables
    with app.app_context():
        try:
            db.create_all()
            app.logger.info('Database tables created successfully')
        except Exception as e:
            app.logger.error(f'Error creating database tables: {str(e)}')
            raise

    return app
