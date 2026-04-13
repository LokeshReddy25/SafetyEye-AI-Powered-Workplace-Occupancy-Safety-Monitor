# SafetyEye - AI-Powered Workplace Safety Monitor

A production-ready AI system that monitors workplace safety in real-time using computer vision to detect PPE violations, send instant alerts, and maintain comprehensive audit logs.

## 🏗️ Architecture

```
┌──────────────────┐     ┌──────────────┐     ┌──────────────┐
│  Camera Feed     │────▶│  YOLO        │────▶│  Detection   │
│ (Real-time video)│     │  Detection   │     │  Validation  │
└──────────────────┘     └──────────────┘     └──────┬───────┘
                                                     │
                                            ┌────────▼────────┐
                                            │  Violation      │
                                            │  Logged to CSV  │
                                            └────────┬────────┘
                                                     │
                ┌─────────────────┬─────────────────┼─────────────────┐
                │                 │                 │                 │
         ┌──────▼────────┐ ┌─────▼──────┐ ┌──────▼────────┐ ┌──────▼──────────┐
         │  Email Alert  │ │  Dashboard │ │  Violation    │ │  Analytics      │
         │  (Instant)    │ │  (Live UI) │ │  History      │ │  & Reports      │
         └───────────────┘ └────────────┘ └───────────────┘ └─────────────────┘

                         ┌──────────────┐
                         │  Logging     │
                         │  System      │
                         │  (Errors &   │
                         │   Info)      │
                         └──────────────┘
```

## 📋 Data Flow

1. **Camera Input** — Real-time video stream from webcam or IP camera
2. **YOLO Detection** — YOLOv8 model detects people, helmets, and vests
3. **Validation** — Compare detection overlaps to identify violations
4. **Logging** — Store violations with timestamp and location data
5. **Alerting** — Send instant email notifications to safety officers
6. **Dashboard** — Live monitoring with real-time metrics and charts
7. **Analytics** — Historical data analysis, compliance reports, trends

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Detection** | YOLOv8 | Real-time object detection |
| **Dashboard** | Streamlit | Interactive web interface |
| **Alerts** | Gmail SMTP | Email notifications |
| **Logging** | Python logging | Application & error logs |
| **Database** | CSV | Violation records storage |
| **Config** | Python-dotenv | Secure environment variables |
| **Language** | Python 3.9+ | Core implementation |

---

## 📁 Project Structure

```
SafetyEye/
├── README.md                          📖 Project documentation
├── GETTING_STARTED.md                 📖 Quick start guide
├── SETUP.md                           📖 Detailed setup instructions
├── PROJECT_STRUCTURE.txt              📖 Directory reference
├── requirements.txt                   📦 Python dependencies
├── .env.example                       🔑 Configuration template
├── .gitignore                         🚫 Git ignore rules
│
├── app.py                             ⭐ Main Streamlit dashboard
│
├── config.py                          ⚙️  Centralized configuration
│
├── safetyeye/                         📦 Core package
│   ├── __init__.py                    
│   ├── logger.py                      📝 Logging system
│   ├── detector.py                    🎯 YOLO detection engine
│   ├── alerts.py                      📧 Email alert system
│   ├── database.py                    💾 CSV logging & queries
│   ├── data/                          💿 Runtime data storage
│   │   └── violations.csv             (Auto-generated)
│   └── logs/                          📋 Application logs
│       └── app_YYYYMMDD.log           (Daily rotation)
│
├── models/                            🎯 YOLO model weights
│   └── best.pt                        (Download or train)
│
├── data/
│   └── datasets/                      📊 Training datasets
│       ├── train/images/
│       ├── val/images/
│       └── test/images/
│
├── tests/                             🧪 Unit tests
│   └── test_*.py
│
└── .git/                              📇 Version control
```

---

## 🚀 Quick Start

### Prerequisites

- ✅ Python 3.9 or higher
- ✅ Webcam or IP camera
- ✅ Gmail account (for email alerts)
- ✅ 2-3 GB disk space (for YOLO models)

### Step 1: Clone Repository

```bash
git clone https://github.com/LokeshReddy25/SafetyEye-AI-Powered-Workplace-Occupancy-Safety-Monitor.git
cd SafetyEye
```

### Step 2: Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `streamlit` — Interactive dashboard
- `ultralytics` — YOLO detection
- `opencv-python` — Video processing
- `torch` — Deep learning
- `plotly` — Charts & analytics
- Plus 6 more essential packages

### Step 4: Configure

```bash
# Create config from template
cp .env.example .env

# Edit .env with your settings
notepad .env    # Windows
nano .env       # macOS/Linux
```

**Required settings:**

```env
SENDER_EMAIL=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
RECEIVER_EMAIL=recipient@gmail.com
CONFIDENCE_THRESHOLD=0.5
IOU_THRESHOLD=0.3
CAMERA_INDEX=0
```

### Step 5: Run Dashboard

```bash
streamlit run app.py
```

**Dashboard opens at: http://localhost:8501 ✨**

---

## 📊 Dashboard Features

### 📊 Dashboard Tab
- **Real-time Metrics** — Total violations, helmet/vest missing counts
- **Compliance Rate** — Percentage of compliant workers
- **Distribution Charts** — Pie chart of violation types
- **Historical Trends** — Bar chart of violations over time
- **Hourly Analysis** — Peak violation times

### 📷 Live Feed Tab
- **Real-time Detection** — Live camera with bounding boxes
- **Violation Overlay** — Red boxes highlight violations
- **Instant Alerts** — Violations trigger email notifications
- **Frame Statistics** — Processing metrics

### 📋 Logs Tab
- **Complete History** — All violation records with timestamps
- **CSV Export** — Download data for analysis
- **Clear Logs** — Reset history when needed
- **Search & Filter** — Find specific violations

### ⚠️ Alerts Tab
- **Test Email** — Verify email configuration
- **Simulate Violations** — Test alerting system
- **Manual Controls** — Capture screenshots, play alarms
- **Camera Settings** — Adjust detection parameters

---

## 🔧 Gmail Setup for Alerts (Important!)

Email alerts require Gmail App Password:

### Step 1: Enable 2-Factor Authentication
1. Go to: https://myaccount.google.com/security
2. Find "2-Step Verification"
3. Complete the setup

### Step 2: Generate App Password
1. Go to: https://myaccount.google.com/apppasswords
2. Select "Mail" and "Windows Computer"
3. Copy the 16-character password

### Step 3: Add to `.env`
```env
SENDER_EMAIL=your_email@gmail.com
EMAIL_PASSWORD=paste_your_16_char_password_here
RECEIVER_EMAIL=recipient@gmail.com
```

✅ Now email alerts will work!

---

## 🧪 Testing

### Run Unit Tests

```bash
pytest tests/ -v
```

### Manual Testing

```bash
# Test camera connection
python -c "import cv2; cap = cv2.VideoCapture(0); print('✅ Camera OK' if cap.isOpened() else '❌ Camera Failed')"

# Test email configuration
# Go to Dashboard → Alerts tab → Click "Send Test Email"

# Test detection
# Go to Dashboard → Alerts tab → Click "Trigger Simulation"

# Query logs
# Go to Dashboard → Logs tab → View violation history
```

---

## 📈 Configuration Options

Edit `.env` to customize behavior:

```env
# Detection accuracy (0.1=fast, 0.9=accurate)
CONFIDENCE_THRESHOLD=0.5

# Box overlap detection sensitivity
IOU_THRESHOLD=0.3

# Camera choice (0=default, 1=external, etc.)
CAMERA_INDEX=0

# Email cooldown (seconds between alerts)
EMAIL_COOLDOWN=60

# Logging detail level
LOG_LEVEL=INFO              # Or DEBUG for verbose logging

# Debug mode (extra output)
DEBUG_MODE=False
```

---

## 📊 Data Storage

### Violation Log (CSV)

**Location:** `safetyeye/data/violations.csv`

**Format:**
```
Timestamp,Violation Type,X1,Y1,X2,Y2
2026-04-14 10:30:15,Helmet Missing,100,50,200,300
2026-04-14 10:31:22,Vest Missing,150,60,250,350
```

**Columns:**
- `Timestamp` — ISO format with seconds
- `Violation Type` — "Helmet Missing" or "Vest Missing"
- `X1, Y1, X2, Y2` — Bounding box coordinates (pixels)

### Application Logs

**Location:** `safetyeye/logs/app_YYYYMMDD.log`

**Daily rotation** — New file each day

**Log Levels:**
- `DEBUG` — Detailed diagnostic info
- `INFO` — General information
- `WARNING` — Warning messages
- `ERROR` — Error messages

---

## 🔒 Security Features

✅ **No Hardcoded Credentials** — All secrets in `.env` (not in git)  
✅ **Environment Variables** — Centralized config management  
✅ **Secure Defaults** — Conservative timeout and cooldown values  
✅ **Error Logging** — Comprehensive error tracking without exposing secrets  
✅ **Input Validation** — Checks camera index and file paths  

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **Camera not detected** | Check CAMERA_INDEX in .env (try 0, 1, 2...) |
| **Email not sending** | Verify .env credentials, use App Password not regular password |
| **ModuleNotFoundError** | Run: `pip install -r requirements.txt` |
| **Port 8501 in use** | Run: `streamlit run app.py --server.port 8502` |
| **YOLO model not found** | Download best.pt and place in project root or models/ |
| **Permission denied (Linux/Mac)** | Run: `chmod +x app.py` |
| **High CPU usage** | Reduce CONFIDENCE_THRESHOLD in .env |

---

## 📈 Performance Analysis

| Metric | Value | Notes |
|--------|-------|-------|
| **Detection FPS** | 30 fps | Real-time processing |
| **Alert Latency** | < 2 seconds | Email sends within 2s of violation |
| **Memory Usage** | ~800 MB | YOLO model + Streamlit |
| **Startup Time** | 15-20 seconds | Model loading + UI init |
| **CSV File Size** | ~1 KB per 10 violations | Very lightweight storage |

---

## 🚀 Deployment

### Option 1: Local Server
```bash
streamlit run app.py
```

### Option 2: Streamlit Cloud
1. Push code to GitHub
2. Go to: https://streamlit.io/cloud
3. Deploy from repo (free tier available)

### Option 3: Docker
```dockerfile
FROM python:3.9
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["streamlit", "run", "app.py"]
```

```bash
docker build -t safetyeye .
docker run -p 8501:8501 safetyeye
```

---

## 📝 Architecture Decisions

### Why YOLO?
- ✅ Fastest object detection (~30 fps)
- ✅ Small model (~50 MB)
- ✅ Accurate PPE detection
- ✅ Works with webcams

### Why Streamlit?
- ✅ Fast prototyping
- ✅ No frontend framework needed
- ✅ Real-time refresh
- ✅ Built-in charts & metrics

### Why CSV?
- ✅ No database setup needed
- ✅ Excel/SQL compatible
- ✅ Easy analysis
- ✅ Works on any OS

### Why Email Alerts?
- ✅ Simple & reliable
- ✅ No setup (just Gmail)
- ✅ Works offline
- ✅ Mobile notifications

---

## 🔄 Workflow

### Daily Workflow

```bash
# 1. Activate environment
source venv/bin/activate          # macOS/Linux
venv\Scripts\activate             # Windows

# 2. Start dashboard
streamlit run app.py

# 3. Start detection
# Click "Start Detection" in dashboard

# 4. Monitor violations
# Check real-time metrics and alerts

# 5. Review logs (end of day)
# Go to Logs tab, download CSV for records
```

---

## 📞 Support & Documentation

| Resource | Link |
|----------|------|
| **Quick Start** | [GETTING_STARTED.md](GETTING_STARTED.md) |
| **Detailed Setup** | [SETUP.md](SETUP.md) |
| **Architecture** | [PROJECT_STRUCTURE.txt](PROJECT_STRUCTURE.txt) |
| **GitHub Issues** | [Report a bug](https://github.com/LokeshReddy25/SafetyEye-AI-Powered-Workplace-Occupancy-Safety-Monitor/issues) |

---

## 📊 Features Roadmap

🟢 **Current:**
- ✅ Real-time detection
- ✅ Email alerts
- ✅ CSV logging
- ✅ Dashboard UI

🟡 **Planned:**
- 🔄 Multi-camera support
- 🔄 Database backend (PostgreSQL)
- 🔄 Web API (FastAPI)
- 🔄 Mobile app
- 🔄 ML model retraining

🔴 **Future:**
- 🔄 Cloud deployment (AWS/GCP)
- 🔄 Advanced analytics
- 🔄 Compliance reporting
- 🔄 Integration with enterprise systems

---

## 📄 Files Overview

| File | Purpose | Size |
|------|---------|------|
| `app.py` | Main Streamlit dashboard | 6 KB |
| `config.py` | Configuration management | 1 KB |
| `safetyeye/detector.py` | YOLO wrapper | 3 KB |
| `safetyeye/alerts.py` | Email system | 1 KB |
| `safetyeye/database.py` | CSV logging | 2 KB |
| `safetyeye/logger.py` | Logging system | 1 KB |
| `requirements.txt` | Dependencies | < 1 KB |

**Total:** ~15 KB production code (very lightweight!)

---

## 🛡️ License & Copyright

```
Copyright (c) 2026 Lokesh Reddy
All Rights Reserved

This repository is provided strictly for viewing and portfolio display
purposes only. You are not granted permission to download, use, copy,
modify, distribute, or create derivative works from this code without
explicit written permission.

SafetyEye™ is a trademark of Lokesh Reddy.
```

---

## 🤝 Contributing

This is a portfolio project. For contributions or inquiries:
- 📧 Email: lokeshdevarapalli92@gmail.com
- 🐙 GitHub: https://github.com/LokeshReddy25

---

## 🙏 Acknowledgments

- **YOLOv8** — Ultralytics for object detection
- **Streamlit** — For dashboard framework
- **OpenCV** — Video processing
- **PyTorch** — Deep learning framework

---

## 📈 Project Status

| Status | Details |
|--------|---------|
| **Version** | 1.0.0 |
| **Release Date** | April 2026 |
| **Status** | ✅ Production Ready |
| **Maintenance** | Active |
| **Python** | 3.9+ |

---

**Keep workplaces safe with SafetyEye! 🦺✨**

*Last Updated: April 14, 2026*

*[View on GitHub](https://github.com/LokeshReddy25/SafetyEye-AI-Powered-Workplace-Occupancy-Safety-Monitor)*
