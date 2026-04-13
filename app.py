import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import cv2
import time
import psutil
from safetyeye.detector import detector
from safetyeye.alerts import alert_system
from safetyeye.database import db
from safetyeye.logger import get_logger
from config import CAMERA_INDEX

logger = get_logger()

# Page config
st.set_page_config(page_title="SafetyEye", layout="wide", initial_sidebar_state="expanded")

# CSS
st.markdown("""
<style>
h1 { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; }
.metric-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white; }
</style>
""", unsafe_allow_html=True)

# Session state
if "detecting" not in st.session_state:
    st.session_state.detecting = False

# Header
st.markdown("<h1>🦺 SafetyEye - Workplace Safety Monitor</h1>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")
    auto_refresh = st.checkbox("Auto Refresh", True)
    cpu = psutil.cpu_percent()
    memory = psutil.virtual_memory().percent
    st.metric("CPU", f"{cpu}%")
    st.metric("Memory", f"{memory}%")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "📷 Live Feed", "📋 Logs", "⚠️ Alerts"])

# TAB 1: Dashboard
with tab1:
    st.subheader("📈 Real-Time Metrics")

    summary = db.get_summary()
    total = summary["total"]
    helmet = summary["helmet"]
    vest = summary["vest"]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🚨 Total", total)
    col2.metric("🪖 Helmet", helmet)
    col3.metric("🦺 Vest", vest)
    col4.metric("✅ Compliance", f"{100 - (helmet + vest) // max(total, 1) * 100 if total > 0 else 100}%")

    st.divider()

    # Charts
    violations = db.get_violations()
    if violations:
        df = pd.DataFrame(violations)
        df["Timestamp"] = pd.to_datetime(df["Timestamp"])

        col1, col2 = st.columns(2)

        with col1:
            counts = df["Violation Type"].value_counts()
            fig = go.Figure(data=[go.Pie(labels=counts.index, values=counts.values)])
            fig.update_layout(title="Distribution", height=350)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            trend = df.groupby(df["Timestamp"].dt.date).size()
            fig = go.Figure(data=[go.Bar(x=trend.index, y=trend.values)])
            fig.update_layout(title="Trend", height=350)
            st.plotly_chart(fig, use_container_width=True)

# TAB 2: Live Feed
with tab2:
    st.subheader("📷 Live Camera Feed")

    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("▶️ Start Detection", use_container_width=True):
            st.session_state.detecting = True
        if st.button("⏹️ Stop Detection", use_container_width=True):
            st.session_state.detecting = False

    frame_window = st.empty()

    if st.session_state.detecting:
        try:
            cap = cv2.VideoCapture(CAMERA_INDEX)
            while st.session_state.detecting:
                ret, frame = cap.read()
                if not ret:
                    break

                detections = detector.detect(frame)
                violations = detector.get_violations(detections) if detections else []

                annotated = detector.draw_boxes(frame, violations)
                frame_window.image(annotated, channels="BGR")

                for v in violations:
                    if db.log_violation(v["type"], v["box"]):
                        alert_system.send_email(
                            f"SafetyEye: {v['type']}",
                            f"Violation detected: {v['type']}"
                        )

                time.sleep(0.03)
            cap.release()
        except Exception as e:
            st.error(f"Camera error: {e}")
            logger.error(f"Camera error: {e}")

# TAB 3: Logs
with tab3:
    st.subheader("📋 Violation Logs")

    violations = db.get_violations()
    if violations:
        df = pd.DataFrame(violations)
        st.dataframe(df, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button("📥 Download CSV", df.to_csv(index=False), "violations.csv")
        with col2:
            if st.button("🗑️ Clear Logs"):
                open(db.VIOLATIONS_LOG, 'w').close()
                with open(db.VIOLATIONS_LOG, 'w', newline='') as f:
                    import csv
                    csv.writer(f).writerow(['Timestamp', 'Violation Type', 'X1', 'Y1', 'X2', 'Y2'])
                st.success("Logs cleared")
    else:
        st.info("No violations logged yet")

# TAB 4: Alerts
with tab4:
    st.subheader("⚠️ Alert Management")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧪 Send Test Email"):
            if alert_system.send_email("SafetyEye Test", "Testing email alerts"):
                st.success("✅ Email sent!")
            else:
                st.error("❌ Failed to send")

    with col2:
        if st.button("🎬 Simulate Violation"):
            db.log_violation("Helmet Missing")
            alert_system.send_email("SafetyEye Alert", "Simulated violation")
            st.warning("⚠️ Violation simulated")

# Auto refresh
if auto_refresh:
    time.sleep(5)
    st.rerun()
