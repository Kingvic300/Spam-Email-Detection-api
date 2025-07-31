from calendar import month

from celery import Celery
from .model import check_email_spam, get_spam_statistics
from datetime import datetime, timedelta
import logging
import sqlite3
from celery.schedules import crontab

logger = logging.getLogger(__name__)

celery = None

def make_celery(app):
    celery_app = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )

    celery_app.conf.update(app.config)

    class ContextTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = ContextTask
    return celery_app


def init_celery(app):
    global celery
    celery = make_celery(app)

    celery.conf.beat_schedule = {
        'daily-spam-check': {
            'task': 'spam_detector.daily_spam_check',
            'schedule': crontab(hour=9, minute=0),
            'args': ('log',)
        },
        'weekly-cleanup': {
            'task': 'spam_detector.cleanup_old_logs',
            'schedule': crontab(hour=2, minute=0, day_of_week=0),
            'args': (30,)
        },
        'weekly-report': {
            'task': 'spam_detector.generate_report',
            'schedule': crontab(hour=8, minute=0, day_of_week=1),
        },
        'monthly-report': {
            'task': 'spam_detector.generate_report',
            'schedule': crontab(hour=9, minute=0, day_of_month=1),
        }
    }

    celery.conf.timezone = 'UTC'
    return celery


@celery.task(name='spam_detector.check_spam_task')
def check_spam_task(action='log'):
    try:
        logger.info(f"Starting background spam check with action: {action}")
        result = check_email_spam(action)
        logger.info(f"Background spam check completed: {result['message']}")

        return result
    except Exception as e:
        logger.error(f"Error in background spam check: {str(e)}")

        return {
            "status": "error",
            "message": f"Daily task failed: {str(e)}"
        }


@celery.task(name='spam_detector.generate_report')
def generate_spam_report_task():
    try:
        logger.info("Generating spam detection report")
        stats = get_spam_statistics()

        report = {
            "report_date": datetime.now().isoformat(),
            "statistics": stats,
            "status": "success"
        }

        logger.info("Spam report generated successfully")
        return report

    except Exception as e:
        logger.error(f"Error generating spam report: {str(e)}")

        return {
            "status": "error",
            "message": f"Report generation failed: {str(e)}"
        }


@celery.task(name='spam_detector.cleanup_old_logs')
def cleanup_old_logs_task(days_to_keep=30):
    try:
        logger.info(f"Cleaning up logs older than {days_to_keep} days")
        conn = sqlite3.connect('spam_detection.db')
        cursor = conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()

        cursor.execute('DELETE FROM spam_emails WHERE created_at < ?', (cutoff_date,))
        deleted_emails = cursor.rowcount

        cursor.execute('DELETE FROM detection_logs WHERE scan_date < ?', (cutoff_date,))
        deleted_logs = cursor.rowcount

        conn.commit()
        conn.close()

        logger.info(f"Cleanup completed: {deleted_emails} emails, {deleted_logs} logs deleted")
        return {
            "status": "success",
            "message": f"Cleaned up {deleted_emails} emails and {deleted_logs} logs",
            "deleted_emails": deleted_emails,
            "deleted_logs": deleted_logs
        }

    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        return {
            "status": "error",
            "message": f"Cleanup failed: {str(e)}"
        }


@celery.task(name='spam_detector.daily_spam_check')
def daily_spam_check_task(action='log'):
    try:
        logger.info("Running daily scheduled spam check")
        result = check_email_spam(action)

        if result['status'] == 'success' and result.get('spam_detected', 0) > 0:
            logger.info(f"Daily scan found {result['spam_detected']} spam emails")

        return result

    except Exception as e:
        logger.error(f"Error in daily spam check: {str(e)}")
        return {
            "status": "error",
            "message": f"Daily spam check failed: {str(e)}"
        }
