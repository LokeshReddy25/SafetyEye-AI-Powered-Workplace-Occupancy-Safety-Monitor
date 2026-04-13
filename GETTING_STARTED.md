# SafetyEye - Getting Started

## 🎯 Quick Setup (5 minutes)

### Step 1: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure
```bash
# Copy config template
cp .env.example .env

# Edit .env and add:
# SENDER_EMAIL=your_email@gmail.com
# EMAIL_PASSWORD=your_app_password
# RECEIVER_EMAIL=recipient@gmail.com
```

### Step 4: Run
```bash
streamlit run app.py
```

**Dashboard opens at: http://localhost:8501**

---

## 📋 Dashboard Features

### 📊 Dashboard Tab
- Real-time violation metrics
- Compliance rate
- Pie charts and trends
- Statistics

### 📷 Live Feed Tab
- Live camera with detection overlay
- Real-time violation alerts
- Frame-by-frame processing

### 📋 Logs Tab
- Complete violation history
- Download CSV
- Clear logs

### ⚠️ Alerts Tab
- Send test email
- Simulate violations
- Manual controls

---

## 🔧 Configuration Options

### Email Setup (Required for Alerts)

1. **Go to Gmail Security:**
   https://myaccount.google.com/security

2. **Enable 2-Step Verification**

3. **Generate App Password:**
   https://myaccount.google.com/apppasswords
   - Select: Mail + Windows Computer
   - Copy 16-character password

4. **Add to .env:**
   ```
   SENDER_EMAIL=your_email@gmail.com
   EMAIL_PASSWORD=paste_your_app_password_here
   RECEIVER_EMAIL=recipient@gmail.com
   ```

### Detection Settings

Edit `.env`:
```env
CONFIDENCE_THRESHOLD=0.5       # 0.1-0.9 (higher = more accurate)
IOU_THRESHOLD=0.3              # Box overlap threshold
CAMERA_INDEX=0                 # 0=default, 1,2 for other cameras
EMAIL_COOLDOWN=60              # Seconds between alerts
```

---

## ✅ Files You Need to Know

| File | Purpose |
|------|---------|
| `app.py` | **Main application** |
| `config.py` | Configuration management |
| `safetyeye/detector.py` | YOLO detection |
| `safetyeye/alerts.py` | Email alerts |
| `safetyeye/database.py` | Violation logging |
| `.env.example` | Configuration template |
| `README.md` | Full documentation |

---

## 🐛 Troubleshooting

### Camera not working
```bash
# Check camera index (try 0, 1, 2...)
# Edit .env: CAMERA_INDEX=0
```

### Email not sending
- Verify Gmail credentials
- Use App Password (not regular password)
- Check internet connection
- Look in: `safetyeye/logs/`

### Dependencies error
```bash
pip install -r requirements.txt --upgrade
```

---

## 📞 Need Help?

1. Read `README.md`
2. Check logs: `safetyeye/logs/app_*.log`
3. Review error messages
4. Check `config.py` for defaults

---

**You're all set! 🚀**

Run: `streamlit run app.py`
