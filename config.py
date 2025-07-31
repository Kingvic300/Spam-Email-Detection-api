import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    SECRET_KEY = os.getenv(
        'SECRET_KEY',
        'd192f6a9f5b990aec2fbe37582dd8ab21aa1495000db741cccc3530ba53cb57b'
    )
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() in ['true', '1', 'yes']

    EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS', 'oladimejivictor611@gmail.com')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', 'ktakkxlvubrlaiey')

    IMAP_SERVER = os.getenv('IMAP_SERVER', 'imap.gmail.com')
    IMAP_PORT = int(os.getenv('IMAP_PORT', 993))

    SPAM_THRESHOLD = float(os.getenv('SPAM_THRESHOLD', 40.0))
    MAX_EMAILS_PER_SCAN = int(os.getenv('MAX_EMAILS_PER_SCAN', 100))
    DEFAULT_SPAM_ACTION = os.getenv('DEFAULT_SPAM_ACTION', 'log')

    DATABASE_PATH = os.getenv('DATABASE_PATH', 'spam_detection.db')

    DAILY_SCAN_TIME = os.getenv('DAILY_SCAN_TIME', '09:00')
    TIMEZONE = os.getenv('TIMEZONE', 'UTC')

    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)

    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    LOG_FILE = os.getenv('LOG_FILE', 'logs/spam_detector.log')

    @staticmethod
    def init_app(app):
        import logging
        from logging.handlers import RotatingFileHandler

        log_level = getattr(logging, Config.LOG_LEVEL, logging.INFO)

        if not app.debug:
            os.makedirs(os.path.dirname(Config.LOG_FILE), exist_ok=True)
            handler = RotatingFileHandler(Config.LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=10)
            handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            handler.setLevel(log_level)
            app.logger.addHandler(handler)
            app.logger.setLevel(log_level)
            app.logger.info('App startup')


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False

    @classmethod
    def init_app(cls, app):
        super().init_app(app)
        import logging
        from logging.handlers import SysLogHandler

        syslog = SysLogHandler()
        syslog.setLevel(logging.WARNING)
        app.logger.addHandler(syslog)


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
