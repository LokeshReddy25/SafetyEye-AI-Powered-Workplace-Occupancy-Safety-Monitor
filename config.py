import os
from dotenv import load_dotenv

load_dotenv()

# Email
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "your_email@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your_app_password")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", "recipient@gmail.com")
EMAIL_COOLDOWN = int(os.getenv("EMAIL_COOLDOWN", "60"))

# Detection
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
IOU_THRESHOLD = float(os.getenv("IOU_THRESHOLD", "0.3"))
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "safetyeye", "data")
LOGS_DIR = os.path.join(BASE_DIR, "safetyeye", "logs")
VIOLATIONS_LOG = os.path.join(DATA_DIR, "violations.csv")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# Model
MODEL_PATH = "best.pt"
VIOLATION_TYPES = ["Helmet Missing", "Vest Missing"]

print("✅ Configuration loaded")
