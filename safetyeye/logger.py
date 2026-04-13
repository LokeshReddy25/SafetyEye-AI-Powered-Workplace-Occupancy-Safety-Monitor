import logging
import os
from datetime import datetime
import sys
sys.path.insert(0, '..')

from config import LOGS_DIR

logger = logging.getLogger("SafetyEye")
logger.setLevel(logging.INFO)

os.makedirs(LOGS_DIR, exist_ok=True)
log_file = os.path.join(LOGS_DIR, f"app_{datetime.now().strftime('%Y%m%d')}.log")

file_handler = logging.FileHandler(log_file)
console_handler = logging.StreamHandler()

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

def get_logger():
    return logger
