import imaplib
import email
import re
import sqlite3
import os
from datetime import datetime
from email.header import decode_header
from flask import current_app
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_database():
    conn = sqlite3.connect('spam_detection.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS spam_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT,
            sender TEXT,
            date_received TEXT,
            spam_score REAL,
            is_spam BOOLEAN,
            action_taken TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detection_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_emails INTEGER,
            spam_detected INTEGER,
            emails_processed INTEGER
        )
    ''')

    conn.commit()
    conn.close()


class SpamDetector:
    def __init__(self):
        self.spam_keywords = [
            'winner', 'congratulations', 'free money', 'click here', 'urgent',
            'limited time', 'act now', 'special offer', 'guarantee', 'risk-free',
            'viagra', 'cialis', 'pharmacy', 'casino', 'lottery', 'inheritance',
            'nigerian prince', 'wire transfer', 'paypal', 'suspended account',
            'verify account', 'update payment', 'claim reward', 'tax refund'
        ]

        self.suspicious_domains = [
            'tempmail.org', '10minutemail.com', 'guerrillamail.com',
            'mailinator.com', 'yopmail.com'
        ]

        init_database()

    def calculate_spam_score(self, subject, sender, body):
        score = 0.0
        money_pattern = r'\$\d+|\d+\s*dollars?|\d+\s*euros?|money|cash|prize'
        url_pattern = r'bit\.ly|tinyurl|goo\.gl|t\.co|short\.link'
        keyword_matches = 0
        uppercase_count = 0

        text_to_check = f"{subject} {body}".lower()

        for keyword in self.spam_keywords:
            if keyword in text_to_check:
                keyword_matches += 1
        score += keyword_matches * 15

        if subject and len(subject) > 0:
            total_length = len(subject)

            for c in subject:
                if c.isupper():
                    uppercase_count += 1

            caps_ratio = uppercase_count / total_length
            if caps_ratio > 0.5:
                score += 20

        sender_domain = sender.split('@')[-1].lower() if '@' in sender else ''
        if sender_domain in self.suspicious_domains:
            score += 30

        exclamation_count = text_to_check.count('!')
        score += min(exclamation_count * 5, 25)

        if re.search(money_pattern, text_to_check):
            score += 15

        if re.search(url_pattern, text_to_check):
            score += 20

        return min(score, 100)

    def is_spam(self, spam_score):
        return spam_score >= 40


def decode_mime_words(s):
    decoded_parts = []
    for part, encoding in decode_header(s):
        if isinstance(part, bytes):
            try:
                decoded_parts.append(part.decode(encoding or 'utf-8'))
            except:
                decoded_parts.append(part.decode('utf-8', errors='ignore'))
        else:
            decoded_parts.append(part)
    return ''.join(decoded_parts)


def get_email_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    break
                except:
                    continue
    else:
        try:
            body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
        except:
            body = ""

    return body[:1000]


def log_spam_detection(subject, sender, spam_score, is_spam, action):
    conn = sqlite3.connect('spam_detection.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO spam_emails (subject, sender, date_received, spam_score, is_spam, action_taken)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (subject, sender, datetime.now().isoformat(), spam_score, is_spam, action))

    conn.commit()
    conn.close()


class EmailManager:
    def __init__(self):
        self.detector = SpamDetector()
        self.imap_server = None

    def connect_to_email(self):
        try:
            email_address = current_app.config['EMAIL_ADDRESS']
            email_password = current_app.config['EMAIL_PASSWORD']
            imap_server_url = current_app.config.get('IMAP_SERVER', 'imap.gmail.com')

            self.imap_server = imaplib.IMAP4_SSL(imap_server_url)
            self.imap_server.login(email_address, email_password)
            logger.info(f"Successfully connected to {email_address}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to email: {str(e)}")
            return False

    def move_to_spam_folder(self, email_id):
        try:
            self.imap_server.copy(email_id, 'INBOX.Spam')
            self.imap_server.store(email_id, '+FLAGS', '\\Deleted')

            return True
        except Exception as e:

            logger.error(f"Failed to move email to spam: {str(e)}")
            return False

    def delete_email(self, email_id):
        try:
            self.imap_server.store(email_id, '+FLAGS', '\\Deleted')
            return True
        except Exception as e:
            logger.error(f"Failed to delete email: {str(e)}")
            return False

    def check_email_spam(self, action='log'):
        if not self.connect_to_email():
            return {
                "status": "error",
                "message": "Failed to connect to email server"
            }

        try:
            self.imap_server.select('INBOX')

            status, message_ids = self.imap_server.search(None, 'UNSEEN')

            if status != 'OK':
                return {
                    "status": "error",
                    "message": "Failed to search emails"
                }

            email_ids = message_ids[0].split()
            spam_emails = []
            processed_count = 0
            spam_count = 0

            for email_id in email_ids:
                try:
                    status, msg_data = self.imap_server.fetch(email_id, '(RFC822)')

                    if status != 'OK':
                        continue

                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    subject = decode_mime_words(msg.get('Subject', ''))
                    sender = decode_mime_words(msg.get('From', ''))
                    body = get_email_body(msg)

                    spam_score = self.detector.calculate_spam_score(subject, sender, body)
                    is_spam = self.detector.is_spam(spam_score)

                    processed_count += 1

                    if is_spam:
                        spam_count += 1
                        action_taken = "logged"

                        if action == 'move_to_spam':
                            if self.move_to_spam_folder(email_id):
                                action_taken = "moved_to_spam"

                        elif action == 'delete':
                            if self.delete_email(email_id):
                                action_taken = "deleted"

                        spam_emails.append({
                            "subject": subject,
                            "from": sender,
                            "spam_score": spam_score,
                            "action": action_taken
                        })

                        log_spam_detection(subject, sender, spam_score, is_spam, action_taken)

                except Exception as e:
                    logger.error(f"Error processing email {email_id}: {str(e)}")
                    continue

            conn = sqlite3.connect('spam_detection.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO detection_logs (total_emails, spam_detected, emails_processed)
                VALUES (?, ?, ?)
            ''', (len(email_ids), spam_count, processed_count))
            conn.commit()
            conn.close()

            if action in ['move_to_spam', 'delete']:
                self.imap_server.expunge()

            return {
                "status": "success",
                "message": f"Processed {processed_count} emails, found {spam_count} spam emails",
                "total_emails": len(email_ids),
                "spam_detected": spam_count,
                "spam_emails": spam_emails
            }

        except Exception as e:
            logger.error(f"Error during spam check: {str(e)}")
            return {
                "status": "error",
                "message": f"Error during spam check: {str(e)}"
            }

        finally:
            if self.imap_server:
                try:
                    self.imap_server.close()
                    self.imap_server.logout()
                except:
                    pass


def check_email_spam(action='log'):
    email_manager = EmailManager()
    return email_manager.check_email_spam(action)


def get_spam_statistics():
    conn = sqlite3.connect('spam_detection.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT COUNT(*) as total_spam, 
               AVG(spam_score) as avg_score,
               COUNT(CASE WHEN created_at >= date('now', '-7 days') THEN 1 END) as week_spam
        FROM spam_emails WHERE is_spam = 1
    ''')

    stats = cursor.fetchone()

    cursor.execute('''
        SELECT scan_date, total_emails, spam_detected 
        FROM detection_logs 
        ORDER BY scan_date DESC LIMIT 10
    ''')

    recent_scans = cursor.fetchall()

    conn.close()

    return {
        "total_spam_detected": stats[0] if stats[0] else 0,
        "average_spam_score": round(stats[1], 2) if stats[1] else 0,
        "spam_this_week": stats[2] if stats[2] else 0,
        "recent_scans": [
            {
                "date": scan[0],
                "total_emails": scan[1],
                "spam_detected": scan[2]
            } for scan in recent_scans
        ]
    }