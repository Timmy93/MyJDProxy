#!/usr/bin/env python3
"""
MyJDownloader API Application
Main entry point for the Flask application.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from app import create_app
from app.utils.exceptions import MyJDConnectionError, ConfigurationError

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def setup_logging(app):
    """Setup logging configuration."""
    if not app.debug:
        # Ensure logs directory exists
        if not os.path.exists('logs'):
            os.mkdir('logs')

        # Setup file handler
        file_handler = RotatingFileHandler(
            'logs/myjdownloader_api.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('MyJDownloader API startup')


def initialize_myjd_connection(app):
    """Initialize MyJDownloader connection on startup."""
    try:
        with app.app_context():
            client = app.myjd_client
            if not client.is_connected():
                app.logger.info("Attempting to connect to MyJDownloader...")
                client.connect()
                app.logger.info("Successfully connected to MyJDownloader")
            else:
                app.logger.info("MyJDownloader client already connected")

    except MyJDConnectionError as e:
        app.logger.warning(f"Could not connect to MyJDownloader on startup: {str(e)}")
        app.logger.info("Connection will be attempted when first API call is made")

    except Exception as e:
        app.logger.error(f"Unexpected error during MyJDownloader initialization: {str(e)}")


def create_application():
    """Create and configure the Flask application."""
    try:
        app = create_app()
        setup_logging(app)

        # Try to connect to MyJDownloader on startup
        initialize_myjd_connection(app)

        return app

    except ConfigurationError as e:
        print(f"Configuration error: {str(e)}")
        print("Please check your config/config.toml file")
        sys.exit(1)

    except Exception as e:
        print(f"Failed to create application: {str(e)}")
        sys.exit(1)


# Create the Flask application
app = create_application()


@app.route('/')
def index():
    """Root endpoint with API information."""
    return {
        'name': 'MyJDownloader API',
        'version': '1.0.0',
        'description': 'REST API for MyJDownloader management',
        'endpoints': {
            'health': '/api/health',
            'connect': '/api/connect',
            'disconnect': '/api/disconnect',
            'downloads': '/api/downloads',
            'start_downloads': '/api/downloads/start',
            'pause_downloads': '/api/downloads/pause',
            'linkgrabber': '/api/linkgrabber',
            'config': '/api/config'
        },
        'documentation': {
            'add_download': {
                'method': 'POST',
                'url': '/api/downloads',
                'body': {
                    'name': 'Package name',
                    'links': ['http://example.com/file1', 'http://example.com/file2'],
                    'category': 'tv_show|movie|other',
                    'auto_start': True
                }
            },
            'get_downloads': {
                'method': 'GET',
                'url': '/api/downloads'
            },
            'start_downloads': {
                'method': 'POST',
                'url': '/api/downloads/start',
                'body': {
                    'package_ids': ['optional', 'list', 'of', 'package', 'ids']
                }
            }
        }
    }


@app.teardown_appcontext
def cleanup(error):
    """Cleanup resources on app context teardown."""
    if error:
        app.logger.error(f'App context teardown with error: {str(error)}')


def run_development_server():
    """Run the development server."""
    print("=" * 50)
    print("MyJDownloader API - Development Server")
    print("=" * 50)
    print(f"Server starting on http://localhost:5000")
    print(f"API endpoints available at http://localhost:5000/api/")
    print(f"Health check: http://localhost:5000/api/health")
    print("=" * 50)

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )


def run_production_server():
    """Run the production server using Waitress."""
    try:
        from waitress import serve

        print("=" * 50)
        print("MyJDownloader API - Production Server")
        print("=" * 50)
        print(f"Server starting on http://localhost:8080")
        print(f"API endpoints available at http://localhost:8080/api/")
        print("=" * 50)

        serve(
            app,
            host='0.0.0.0',
            port=8080,
            threads=4,
            max_request_body_size=1073741824,  # 1GB
            cleanup_interval=30,
            channel_timeout=120
        )

    except ImportError:
        print("Waitress not installed. Install with: pip install waitress")
        print("Falling back to development server...")
        run_development_server()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='MyJDownloader API Server')
    parser.add_argument(
        '--mode',
        choices=['development', 'production'],
        default='development',
        help='Server mode (default: development)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=None,
        help='Port to run the server on'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Host to bind the server to (default: 0.0.0.0)'
    )

    args = parser.parse_args()

    if args.mode == 'production':
        if args.port:
            # Override default production port
            from waitress import serve

            print(f"Starting production server on {args.host}:{args.port}")
            serve(app, host=args.host, port=args.port, threads=4)
        else:
            run_production_server()
    else:
        if args.port:
            # Override default development port
            app.run(host=args.host, port=args.port, debug=True, threaded=True)
        else:
            run_development_server()
