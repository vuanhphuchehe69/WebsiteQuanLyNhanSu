"""Routes package initialization: exports all blueprints."""
from .auth import auth_bp
from .main import main_bp
from .modules import modules_bp

def register_blueprints(app):
    """Register all modular blueprints to the Flask application."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(modules_bp)

