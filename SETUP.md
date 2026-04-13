# SafetyEye Setup Guide

Complete setup and configuration guide for SafetyEye system.

## Quick Start (5 minutes)

### 1. Clone Repository
```bash
git clone https://github.com/LokeshReddy25/SafetyEye-AI-Powered-Workplace-Occupancy-Safety-Monitor.git
cd SafetyEye
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your settings (see Configuration section below)
```

### 5. Run Dashboard
```bash
streamlit run app.py
```

Dashboard opens at: `http://localhost:8501`

---

## Detailed Configuration

### 1. Email Configuration (Gmail)

#### Step 1: Enable Gmail 2FA
1. Visit: https://myaccount.google.com/
2. Go to Security (left sidebar)
3. Enable 2-Step Verification

#### Step 2: Generate App Password
1. Go to: https://myaccount.google.com/apppasswords
2. Select "Mail" and "Windows Computer"
3. Copy the generated 16-character password

#### Step 3: Update .env
```env
SENDER_EMAIL=your_email@gmail.com
EMAIL_PASSWORD=your_generated_app_password
RECEIVER_EMAIL=recipient@gmail.com
```

### 2. Detection Configuration

```env
# Detection accuracy vs speed
CONFIDENCE_THRESHOLD=0.5      # 0.1-0.9 (higher = more accurate, slower)
IOU_THRESHOLD=0.3             # Intersection over Union threshold

# Camera settings
CAMERA_INDEX=0                # 0 = default webcam, 1, 2 for other cameras
```

### 3. Alert Configuration

```env
# Cooldown times to prevent spam
EMAIL_COOLDOWN=60             # Seconds between emails
ALERT_COOLDOWN=3              # Seconds between same violation alerts
LOG_COOLDOWN=2.0              # Seconds between logging same violation
```

### 4. Application Settings

```env
# Logging level
LOG_LEVEL=INFO               # DEBUG, INFO, WARNING, ERROR

# Debug mode (verbose output)
DEBUG_MODE=False
```

---

## Project Structure After Setup

```
SafetyEye/
├── app.py                           # Main dashboard (RUNNING FILE)
├── requirements.txt                 # Dependencies
├── .env                            # Environment config (DO NOT COMMIT)
├── .env.example                    # Example config (template)
│
├── safetyeye/                      # Main package
│   ├── config.py                   # Configuration module
│   ├── modules/
│   │   ├── detection.py            # YOLO detection
│   │   ├── alerts.py               # Email alerts
│   │   ├── database.py             # CSV logging
│   ├── utils/
│   │   └── logger.py               # Logging
│   ├── data/                       # Data storage
│   └── logs/                       # Application logs
│
└── Src/                            # Utility scripts
    ├── main.py                     # Dataset processing
    ├── train.py                    # Model training
    ├── predict.py                  # Single image prediction
    └── evaluate.py                 # Model validation
```

---

## First Run Checklist

- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `.env` file created and configured
- [ ] Gmail App Password generated (if using email alerts)
- [ ] YOLO model (`best.pt`) exists in project root
- [ ] Webcam/camera is connected and working
- [ ] Run: `streamlit run app.py`

---

## Testing the Setup

### 1. Test Camera Connection
```python
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera Failed')"
```

### 2. Test Email Configuration
- Open dashboard
- Go to **Alerts** tab
- Click **Send Test Alert**
- Check email inbox (wait 2-3 mins)

### 3. Test Detection
- Open dashboard
- Click **Start Detection** in 📊 Dashboard tab
- System should display live camera feed
- Trigger simulation to test logging and alerts

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'safetyeye'"
**Solution:**
```bash
# Make sure you're in the correct directory
cd path/to/SafetyEye

# Reinstall requirements
pip install -r requirements.txt

# Try running app.py
streamlit run app.py
```

### Issue: "Camera Failed" or "Cannot access camera"
**Solution:**
1. Check camera is connected
2. Try different camera index in `.env`:
   ```env
   CAMERA_INDEX=0    # Try 0, 1, 2, etc.
   ```
3. Install camera drivers if needed
4. Test with: `python -c "import cv2; cap = cv2.VideoCapture(0)"`

### Issue: "Email alert not sent"
**Solution:**
1. Verify Gmail credentials in `.env`
2. Ensure App Password (not regular password) is used
3. Check "Less secure app access" is enabled
4. Verify internet connection
5. Check spam folder
6. Try sending test alert from dashboard

### Issue: "YOLO model not found"
**Solution:**
1. Ensure `best.pt` exists in project root
2. Or train a model: `python Src/train.py`
3. Update model path in `safetyeye/config.py` if using different path

### Issue: "Permission denied" on Linux/Mac
**Solution:**
```bash
chmod +x app.py
chmod +x Src/*.py
```

---

## Daily Usage

### Starting the Application
```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Run dashboard
streamlit run app.py
```

### Monitoring Safety
1. Open dashboard at `http://localhost:8501`
2. Click "Start Detection"
3. Monitor violations in real-time
4. View logs and analytics
5. Click "Stop Detection" when done

### Generating Reports
```bash
python SafetyEye_RealTimeDetection/generate_report.py
```

---

## Advanced Configuration

### Using Different YOLO Models

In `safetyeye/config.py`:
```python
MODEL_PATH = "best.pt"  # Change to yolov8n.pt, yolov8m.pt, etc.
```

Options:
- `yolov8n.pt` - Fastest (Nano)
- `yolov8s.pt` - Fast (Small) 
- `yolov8m.pt` - Balanced (Medium)
- `yolov8l.pt` - Accurate (Large)

### Custom Email Templates

Edit `safetyeye/modules/alerts.py` in `send_email_alert()` method to customize email content.

### Adding New Violation Types

1. Update `ppe_data.yaml`:
```yaml
names: ['helmet', 'vest', 'mask', 'gloves']  # Add 'gloves'
```

2. Retrain model with new class

3. Update detection logic in `safetyeye/modules/detection.py`

---

## Documentation

- **Full Documentation:** See `README.md`
- **API Reference:** See module docstrings in `safetyeye/modules/`
- **Configuration:** See `safetyeye/config.py`

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review application logs in `safetyeye/logs/`
3. Open issue on GitHub repository

---

**Happy Monitoring! 🦺**
