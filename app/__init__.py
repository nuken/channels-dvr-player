import sys
import os
from flask import Flask

# Add the parent directory to Python path to ensure config imports work
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config.app_config import AppConfig


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(AppConfig)
    
    # Register blueprints
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    # Make config available in templates
    @app.context_processor
    def inject_config():
        return {'config': AppConfig}
    
    return app
