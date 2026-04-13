import os
import csv
import time
from datetime import datetime
import sys
sys.path.insert(0, '..')

from config import VIOLATIONS_LOG, DATA_DIR
from safetyeye.logger import get_logger

logger = get_logger()

class Database:
    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(VIOLATIONS_LOG):
            with open(VIOLATIONS_LOG, 'w', newline='') as f:
                csv.writer(f).writerow(['Timestamp', 'Violation Type', 'X1', 'Y1', 'X2', 'Y2'])
            logger.info(f"Created: {VIOLATIONS_LOG}")

    def log_violation(self, violation_type, box=None):
        try:
            x1, y1, x2, y2 = map(int, box) if box else (0, 0, 0, 0)
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            with open(VIOLATIONS_LOG, 'a', newline='') as f:
                csv.writer(f).writerow([timestamp, violation_type, x1, y1, x2, y2])

            logger.info(f"Logged: {violation_type}")
            return True
        except Exception as e:
            logger.error(f"Log failed: {e}")
            return False

    def get_violations(self):
        try:
            if not os.path.exists(VIOLATIONS_LOG):
                return []
            with open(VIOLATIONS_LOG, 'r') as f:
                reader = csv.DictReader(f)
                return list(reader) if reader else []
        except Exception as e:
            logger.error(f"Read failed: {e}")
            return []

    def get_summary(self):
        violations = self.get_violations()
        if not violations:
            return {"total": 0, "helmet": 0, "vest": 0}

        helmet_count = sum(1 for v in violations if v.get('Violation Type') == 'Helmet Missing')
        vest_count = sum(1 for v in violations if v.get('Violation Type') == 'Vest Missing')

        return {
            "total": len(violations),
            "helmet": helmet_count,
            "vest": vest_count
        }

db = Database()
