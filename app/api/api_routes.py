import logging
from flask import Blueprint, request, jsonify, current_app
import re
from app.models.download_models import DownloadRequest
from app.utils.exceptions import (
    MyJDConnectionError, 
    MyJDOperationError, 
    ValidationError
)

api_bp = Blueprint('api', __name__)
logger = logging.getLogger(__name__)


def get_myjd_client():
    """Get MyJDownloader client from Flask app."""
    return current_app.myjd_client


@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        client = get_myjd_client()
        is_connected = client.is_connected()
        
        return jsonify({
            'status': 'healthy' if is_connected else 'disconnected',
            'connected': is_connected,
            'message': 'MyJDownloader API is running'
        }), 200 if is_connected else 503
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'connected': False,
            'message': str(e)
        }), 500


@api_bp.route('/connect', methods=['POST'])
def connect():
    """Connect to MyJDownloader service."""
    try:
        client = get_myjd_client()
        
        if client.is_connected():
            return jsonify({
                'success': True,
                'message': 'Already connected to MyJDownloader'
            }), 200
        
        client.connect()
        
        return jsonify({
            'success': True,
            'message': 'Successfully connected to MyJDownloader'
        }), 200
        
    except MyJDConnectionError as e:
        logger.error(f"Connection error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'connection_error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error during connection: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Internal server error'
        }), 500


@api_bp.route('/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from MyJDownloader service."""
    try:
        client = get_myjd_client()
        client.disconnect()
        
        return jsonify({
            'success': True,
            'message': 'Disconnected from MyJDownloader'
        }), 200
        
    except Exception as e:
        logger.error(f"Error during disconnection: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': str(e)
        }), 500


def clean_name(name: str) -> str:
    """Clean and standardize the download package name."""
    # TODO: utilizzare un json/toml di config per definire le sostituzioni
    def _repl(m):
        num = m.group(1)
        return 'S' + num.zfill(2)
    # match case-insensitive 'Stagione' seguito da separatori opzionali e da un numero
    name = re.sub(r'(?i)\bStagione[\s\-_:]*([0-9]+)\b', _repl, name)
    return name

@api_bp.route('/downloads', methods=['POST'])
def add_download():
    """Add a new download package."""
    try:
        data = request.get_json()
        
        if not data:
            raise ValidationError("No JSON data provided")
        
        # Extract request data
        name = data.get('name', 'Unnamed Package')
        links = data.get('links', [])
        category = data.get('category', 'other')
        auto_start = data.get('auto_start', True)
        print(f"Aggiungo: {name}: {len(links)} link. Categoria: {category}. {"Autostart" if auto_start else "No autostart"}")
        # Create and validate download request
        category = extract_correct_category(category)
        name = clean_name(name)
        download_request = DownloadRequest(name=name, links=links, category=category, auto_start=auto_start)
        client = get_myjd_client()

        valid_request = download_request.validate(
            client.config.allowed_categories,
        )
        if not valid_request:
            raise ValidationError("Invalid download request data")
        
        # Add download package
        success = client.add_download_package(
            name=download_request.name,
            download_links=download_request.links,
            category=download_request.category,
            auto_start=download_request.auto_start
        )
        
        return jsonify({
            'success': success,
            'message': f'Successfully added download package: {name}',
            'package_name': name,
            'links_count': len(links),
            'category': category
        }), 201
        
    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': str(e)
        }), 400
        
    except MyJDConnectionError as e:
        logger.error(f"Connection error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'connection_error',
            'message': str(e)
        }), 503
        
    except MyJDOperationError as e:
        logger.error(f"Operation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'operation_error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Internal server error'
        }), 500


def extract_correct_category(category: str) -> str:
    category_map = current_app.config.get('mapping_categories', {})
    for key, mapped_categories in category_map.items():
        if category.lower() in mapped_categories:
            print("Mapping categoria", category, "corrisponde a", key)
            category = key
            break
    return category


@api_bp.route('/downloads', methods=['GET'])
def get_downloads():
    """Get all download packages with their status."""
    try:
        client = get_myjd_client()
        packages = client.get_download_packages()
        
        # Convert packages to dictionaries
        packages_data = [pkg.to_dict() for pkg in packages]
        
        return jsonify({
            'success': True,
            'count': len(packages_data),
            'packages': packages_data
        }), 200
        
    except MyJDConnectionError as e:
        logger.error(f"Connection error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'connection_error',
            'message': str(e)
        }), 503
        
    except MyJDOperationError as e:
        logger.error(f"Operation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'operation_error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Internal server error'
        }), 500


@api_bp.route('/downloads/start', methods=['POST'])
def start_downloads():
    """Start downloads."""
    try:
        data = request.get_json() or {}
        package_ids = data.get('package_ids', [])
        
        client = get_myjd_client()
        success = client.start_downloads(package_ids)
        
        message = "Started all downloads" if not package_ids else f"Started {len(package_ids)} packages"
        
        return jsonify({
            'success': success,
            'message': message
        }), 200
        
    except MyJDConnectionError as e:
        logger.error(f"Connection error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'connection_error',
            'message': str(e)
        }), 503
        
    except MyJDOperationError as e:
        logger.error(f"Operation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'operation_error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Internal server error'
        }), 500


@api_bp.route('/downloads/pause', methods=['POST'])
def pause_downloads():
    """Pause downloads."""
    try:
        data = request.get_json() or {}
        package_ids = data.get('package_ids', [])
        
        client = get_myjd_client()
        success = client.pause_downloads(package_ids)
        
        message = "Paused all downloads" if not package_ids else f"Paused {len(package_ids)} packages"
        
        return jsonify({
            'success': success,
            'message': message
        }), 200
        
    except MyJDConnectionError as e:
        logger.error(f"Connection error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'connection_error',
            'message': str(e)
        }), 503
        
    except MyJDOperationError as e:
        logger.error(f"Operation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'operation_error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Internal server error'
        }), 500


@api_bp.route('/linkgrabber', methods=['GET'])
def get_linkgrabber():
    """Get packages in linkgrabber (pending downloads)."""
    try:
        client = get_myjd_client()
        packages = client.get_linkgrabber_packages()
        
        return jsonify({
            'success': True,
            'count': len(packages),
            'packages': packages
        }), 200
        
    except MyJDConnectionError as e:
        logger.error(f"Connection error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'connection_error',
            'message': str(e)
        }), 503
        
    except MyJDOperationError as e:
        logger.error(f"Operation error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'operation_error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Internal server error'
        }), 500


@api_bp.route('/config', methods=['GET'])
def get_config_info():
    """Get configuration information (without sensitive data)."""
    try:
        client = get_myjd_client()
        config = client.config
        
        return jsonify({
            'success': True,
            'config': {
                'base_path': config.base_path,
                'allowed_categories': config.allowed_categories,
                'device_id': config.myjd_deviceid,
                'username': config.myjd_username  # You might want to mask this
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting config info: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Internal server error'
        }), 500


@api_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'not_found',
        'message': 'Endpoint not found'
    }), 404


@api_bp.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({
        'success': False,
        'error': 'method_not_allowed',
        'message': 'Method not allowed'
    }), 405
