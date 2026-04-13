# SafetyEye - AI-Powered Workplace Safety Monitor

Real-time safety monitoring using AI to detect PPE violations, send alerts, and generate reports.

## Features

✅ Real-time YOLO detection  
✅ Email alerts  
✅ Professional dashboard  
✅ Violation logging  
✅ Analytics & reports  

## Quick Start

### 1. Setup
```bash
python -m venv venv
venv\Scripts\activate              # Windows
source venv/bin/activate           # macOS/Linux
pip install -r requirements.txt
```

### 2. Configure
```bash
cp .env.example .env
# Edit .env with your Gmail credentials
```

### 3. Run
```bash
streamlit run app.py
```

Dashboard opens at: **http://localhost:8501**

## Dashboard

- **📊 Dashboard** - Metrics, charts, compliance rate
- **📷 Live Feed** - Real-time detection overlay
- **📋 Logs** - Violation history, CSV export
- **⚠️ Alerts** - Test email, simulate violations

## Configuration

Edit `.env`:
```env
SENDER_EMAIL=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
RECEIVER_EMAIL=recipient@gmail.com
CONFIDENCE_THRESHOLD=0.5
IOU_THRESHOLD=0.3
CAMERA_INDEX=0
EMAIL_COOLDOWN=60
```

## File Structure

```
SafetyEye/
├── app.py                    # Main dashboard
├── config.py                 # Configuration
├── requirements.txt          # Dependencies
├── .env.example              # Config template
├── safetyeye/
│   ├── logger.py            # Logging
│   ├── detector.py          # YOLO detection
│   ├── alerts.py            # Email alerts
│   ├── database.py          # CSV logging
│   ├── data/                # Runtime data
│   └── logs/                # App logs
├── models/                  # YOLO weights
└── data/datasets/           # Training data
```

## Setup Gmail for Alerts

1. Enable 2FA: https://myaccount.google.com/security
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Add to `.env`: `EMAIL_PASSWORD=your_app_password`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Camera not found | Check CAMERA_INDEX in .env (try 0, 1, 2...) |
| Email not sending | Verify credentials, use App Password not regular password |
| ModuleNotFoundError | Run: `pip install -r requirements.txt` |
| Port in use | Run: `streamlit run app.py --server.port 8502` |

## Version

**1.0.0** - Clean, professional, production-ready

---

**Keep workplaces safe! 🦺**
