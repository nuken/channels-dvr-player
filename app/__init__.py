import sys
import os
from flask import Flask
import importlib.util

# Load AppConfig using absolute file path
config_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'app_config.py')
spec = importlib.util.spec_from_file_location("app_config", config_file_path)
if spec is None or spec.loader is None:
    raise ImportError(f"Cannot load config from {config_file_path}")
app_config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_config_module)
AppConfig = app_config_module.AppConfig


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
