from flask import Flask
from config import config
import os
import logging
from logging.handlers import RotatingFileHandler


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    config[config_name].init_app(app)

    setup_logging(app)

    from .routes import bp as routes_bp
    app.register_blueprint(routes_bp)

    try:
        from .celery_tasks import init_celery
        init_celery(app)
        app.logger.info("Celery initialized successfully")

    except ImportError:
        app.logger.warning("Celery not available, background tasks disabled")

    except Exception as e:
        app.logger.error(f"Failed to initialize Celery: {str(e)}")

    try:
        from .scheduler import start_scheduler
        start_scheduler()
        app.logger.info("Scheduler initialized successfully")

    except Exception as e:
        app.logger.error(f"Failed to initialize scheduler: {str(e)}")

    try:
        from .model import SpamDetector
        SpamDetector()
        app.logger.info("Database initialized successfully")

    except Exception as e:
        app.logger.error(f"Failed to initialize database: {str(e)}")

    import atexit

    def cleanup():
        try:
            from .scheduler import stop_scheduler
            stop_scheduler()
        except:
            pass

    atexit.register(cleanup)

    app.logger.info("Spam Email Detector application started")

    return app


def setup_logging(app):
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')

        file_handler = RotatingFileHandler(
            'logs/spam_detector.log',
            maxBytes=10240000,
            backupCount=10
        )

        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))

        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s'
        ))
        console_handler.setLevel(logging.INFO)
        app.logger.addHandler(console_handler)