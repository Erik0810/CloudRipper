from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize SQLAlchemy
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # Configure the app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-for-cloudripper')

    # Database configuration
    if os.environ.get('DATABASE_URL'):
        # Handle Render's PostgreSQL URL format
        database_url = os.environ.get('DATABASE_URL')
        if database_url is not None:
            if database_url.startswith("postgres://"):
                database_url = database_url.replace("postgres://", "postgresql://", 1)
            if '?' not in database_url:
                database_url += "?sslmode=require"
            app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Local SQLite database
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cloudripper.db'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')

    # Ensure download directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Set up logging
    if not app.debug:
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        os.makedirs(logs_dir, exist_ok=True)

        # Set up file handler
        file_handler = RotatingFileHandler(
            os.path.join(logs_dir, 'cloudripper.log'),
            maxBytes=10240,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)

        # Set up console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s'
        ))

        # Add handlers to app logger
        app.logger.addHandler(file_handler)
        app.logger.addHandler(console_handler)
        app.logger.setLevel(logging.INFO)

        app.logger.info('CloudRipper startup')

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    # Create database tables
    with app.app_context():
        db.create_all()

    return app
