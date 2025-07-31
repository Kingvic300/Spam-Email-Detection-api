from flask import Blueprint, jsonify, request, current_app
from .model import check_email_spam, get_spam_statistics
from .scheduler import schedule_daily_scan, get_next_scheduled_scan
import logging

bp = Blueprint('routes', __name__)
logger = logging.getLogger(__name__)


@bp.route('/check-spam', methods=['GET'])
def check_spam():
    try:
        action = request.args.get('action', current_app.config['DEFAULT_SPAM_ACTION'])

        if action not in ['log', 'move_to_spam', 'delete']:
            return jsonify({
                "status": "error",
                "message": "Invalid action. Use: log, move_to_spam, or delete"
            }), 400

        result = check_email_spam(action)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in check_spam endpoint: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Internal server error: {str(e)}"
        }), 500


@bp.route('/stats', methods=['GET'])
def get_stats():
    try:
        stats = get_spam_statistics()
        return jsonify({
            "status": "success",
            "data": stats
        })
    except Exception as e:
        logger.error(f"Error in get_stats endpoint: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to get statistics: {str(e)}"
        }), 500


@bp.route('/schedule', methods=['POST'])
def schedule_scan():
    try:
        data = request.get_json() or {}
        time_str = data.get('time', current_app.config['DAILY_SCAN_TIME'])
        action = data.get('action', current_app.config['DEFAULT_SPAM_ACTION'])

        result = schedule_daily_scan(time_str, action)
        return jsonify(result)

    except Exception as e:
        logger.error(f"Error in schedule_scan endpoint: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to schedule scan: {str(e)}"
        }), 500


@bp.route('/schedule', methods=['GET'])
def get_schedule():
    try:
        next_scan = get_next_scheduled_scan()
        return jsonify({
            "status": "success",
            "next_scan": next_scan
        })
    except Exception as e:
        logger.error(f"Error in get_schedule endpoint: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to get schedule: {str(e)}"
        }), 500


@bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "Spam Email Detector",
        "version": "1.0.0"
    })


@bp.route('/config', methods=['GET'])
def get_config():
    try:
        return jsonify({
            "status": "success",
            "config": {
                "spam_threshold": current_app.config['SPAM_THRESHOLD'],
                "max_emails_per_scan": current_app.config['MAX_EMAILS_PER_SCAN'],
                "default_action": current_app.config['DEFAULT_SPAM_ACTION'],
                "daily_scan_time": current_app.config['DAILY_SCAN_TIME'],
                "timezone": current_app.config['TIMEZONE'],
                "debug_mode": current_app.config['DEBUG']
            }
        })
    except Exception as e:
        logger.error(f"Error in get_config endpoint: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Failed to get configuration: {str(e)}"
        }), 500


@bp.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "message": "Endpoint not found"
    }), 404


@bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        "status": "error",
        "message": "Internal server error"
    }), 500