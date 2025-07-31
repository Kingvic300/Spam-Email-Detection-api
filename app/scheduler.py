import schedule
import time
import threading
import json
import os
from datetime import datetime, timedelta
from .model import check_email_spam
import logging

logger = logging.getLogger(__name__)


class SpamScheduler:
    def __init__(self):
        self.schedule_config = None
        self.scheduler_thread = None
        self.is_running = False
        self.schedule_file = 'schedule_config.json'
        self.load_schedule()

    def load_schedule(self):
        try:
            if os.path.exists(self.schedule_file):
                with open(self.schedule_file, 'r') as f:
                    self.schedule_config = json.load(f)
            else:
                self.schedule_config = {
                    "enabled": False,
                    "time": "09:00",
                    "action": "log",
                    "last_run": None
                }
                self.save_schedule()
        except Exception as e:
            logger.error(f"Error loading schedule: {str(e)}")
            self.schedule_config = {
                "enabled": False,
                "time": "09:00",
                "action": "log",
                "last_run": None
            }

    def save_schedule(self):
        try:
            with open(self.schedule_file, 'w') as f:
                json.dump(self.schedule_config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving schedule: {str(e)}")

    def run_scheduled_scan(self):
        logger.info("Running scheduled spam scan...")
        try:
            result = check_email_spam(self.schedule_config['action'])
            self.schedule_config['last_run'] = datetime.now().isoformat()
            self.save_schedule()

            logger.info(f"Scheduled scan completed: {result['message']}")
            return result
        except Exception as e:
            logger.error(f"Error in scheduled scan: {str(e)}")
            return {"status": "error", "message": str(e)}

    def start_scheduler(self):
        if self.is_running:
            return

        self.is_running = True

        def run_scheduler():
            while self.is_running:
                if self.schedule_config['enabled']:
                    schedule.run_pending()
                time.sleep(60)

        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("Scheduler started")

    def stop_scheduler(self):
        self.is_running = False
        schedule.clear()
        logger.info("Scheduler stopped")

    def schedule_daily_scan(self, time_str, action):
        try:
            datetime.strptime(time_str, '%H:%M')

            schedule.clear()

            schedule.every().day.at(time_str).do(self.run_scheduled_scan)

            self.schedule_config.update({
                "enabled": True,
                "time": time_str,
                "action": action
            })
            self.save_schedule()

            if not self.is_running:
                self.start_scheduler()

            logger.info(f"Scheduled daily scan at {time_str} with action '{action}'")

            return {
                "status": "success",
                "message": f"Daily spam scan scheduled for {time_str}",
                "next_run": self.get_next_run_time()
            }

        except ValueError:
            return {
                "status": "error",
                "message": "Invalid time format. Use HH:MM (24-hour format)"
            }
        except Exception as e:
            logger.error(f"Error scheduling scan: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to schedule scan: {str(e)}"
            }

    def get_next_run_time(self):
        if not self.schedule_config['enabled']:
            return None

        try:
            next_run = schedule.next_run()
            return next_run.isoformat() if next_run else None
        except:
            return None

    def get_schedule_status(self):
        return {
            "enabled": self.schedule_config['enabled'],
            "time": self.schedule_config['time'],
            "action": self.schedule_config['action'],
            "last_run": self.schedule_config['last_run'],
            "next_run": self.get_next_run_time(),
            "is_running": self.is_running
        }


spam_scheduler = SpamScheduler()


def schedule_daily_scan(time_str, action='log'):
    return spam_scheduler.schedule_daily_scan(time_str, action)


def get_next_scheduled_scan():
    return spam_scheduler.get_schedule_status()


def start_scheduler():
    spam_scheduler.start_scheduler()


def stop_scheduler():
    spam_scheduler.stop_scheduler()


start_scheduler()