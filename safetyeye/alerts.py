import smtplib
import time
from email.mime.text import MIMEText
import sys
sys.path.insert(0, '..')

from config import SENDER_EMAIL, EMAIL_PASSWORD, RECEIVER_EMAIL, EMAIL_COOLDOWN
from safetyeye.logger import get_logger

logger = get_logger()

class AlertSystem:
    def __init__(self):
        self.last_email_time = 0

    def send_email(self, subject, body):
        current_time = time.time()
        if current_time - self.last_email_time < EMAIL_COOLDOWN:
            return False

        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = SENDER_EMAIL
            msg["To"] = RECEIVER_EMAIL

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(SENDER_EMAIL, EMAIL_PASSWORD)
                server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())

            self.last_email_time = current_time
            logger.info(f"✅ Email sent: {subject}")
            return True
        except Exception as e:
            logger.error(f"Email failed: {e}")
            return False

alert_system = AlertSystem()
