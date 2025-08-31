# app/__init__.py
"""
MyJDownloader API Application Package
"""

from flask import Flask

from app.api.api_routes import api_bp
from app.core.config_manager import Config
from app.core.myjd_client import MyJDClient

__version__ = '1.0.0'


def create_app():
    """Application factory function."""
    app = Flask(__name__)

    # Load configuration
    try:
        config = Config()
        app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
        app.config['JSON_SORT_KEYS'] = False

        # Initialize MyJD client
        myjd_client = MyJDClient(config)
        app.myjd_client = myjd_client

        # Register blueprints
        app.register_blueprint(api_bp, url_prefix='/api')

        return app

    except Exception as e:
        from app.utils.exceptions import ConfigurationError
        raise ConfigurationError(f"Failed to create application: {str(e)}")


# app/core/__init__.py
"""
Core application components
"""

# app/models/__init__.py  
"""
Data models for the application
"""

# app/utils/__init__.py
"""
Utility functions and classes
"""

# app/api/__init__.py
"""
API routes and endpoints
"""