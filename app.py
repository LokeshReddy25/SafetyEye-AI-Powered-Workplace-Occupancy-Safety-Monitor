"""SafetyEye – Streamlit dashboard (Module 4).

Run:  streamlit run app.py
Tabs: Live feed (video file or webcam with overlays) | Compliance (charts) | Violation log (filter, export, snapshots)
"""
from __future__ import annotations

import datetime as dt
import time
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src import config
from src.alerts import AlertManager, ViolationLog
from src.rules import RULES

st.set_page_config(page_title="SafetyEye", page_icon="🦺", layout="wide")
db = ViolationLog()


@st.cache_resource(show_spinner="Loading model…")
def get_pipeline(weights: str, conf: float, rules: tuple):
    from src.detect import Pipeline

    return Pipeline(weights, conf=conf, rules=rules)


# ---------------- sidebar ----------------
st.sidebar.title("🦺 SafetyEye")
weights = sorted(str(p) for p in config.WEIGHTS.glob("*.pt"))
if not weights:
    st.sidebar.error("No weights in weights/. Train a model first (python -m src.train …).")
qp = st.query_params
default_w = next((i for i, w in enumerate(weights) if Path(w).stem == qp.get("weights", "best")), 0)
weights_sel = st.sidebar.selectbox("Model weights", weights, index=default_w if weights else None)
videos = sorted(str(p) for p in config.SOURCE_VIDEOS.glob("*.mp4")) if config.SOURCE_VIDEOS.exists() else []
src_kind = st.sidebar.radio("Input", ["Video file", "Webcam"], horizontal=True)
if src_kind == "Video file":
    default_v = next((i for i, v in enumerate(videos) if Path(v).name == qp.get("video", "hardhat.mp4")), 0)
    source = st.sidebar.selectbox("Video", videos, index=default_v, format_func=lambda p: Path(p).name) \
        if videos else st.sidebar.text_input("Video path")
else:
    source = str(st.sidebar.number_input("Webcam index", 0, 10, 0))
conf = st.sidebar.slider("Confidence threshold", 0.1, 0.9, 0.5, 0.05)
rules = st.sidebar.multiselect("Active rules", list(RULES), default=["NO-Hardhat", "NO-Safety Vest"],
                               format_func=lambda c: f"{RULES[c]} ({c})")
cooldown = st.sidebar.number_input("Alert cooldown (s)", 1, 600, 10)
max_frames = st.sidebar.number_input("Stop after N frames (0 = until end)", 0, 100000,
                                     int(qp.get("frames", 0)))

tab_live, tab_stats, tab_log = st.tabs(["📷 Live feed", "📊 Compliance", "📋 Violation log"])

# ---------------- live ----------------
with tab_live:
    c1, c2 = st.columns([1, 1])
    start = c1.button("▶ Start", type="primary", disabled=not (weights_sel and rules and source)) \
        or qp.get("autostart") == "1"
    c2.button("⏹ Stop")
    frame_ph = st.empty()
    m1, m2, m3, m4 = st.columns(4)
    fps_ph, workers_ph, comp_ph, alerts_ph = m1.empty(), m2.empty(), m3.empty(), m4.empty()
    warn_ph = st.empty()
    if start:
        import cv2

        from src.detect import open_source

        pipe = get_pipeline(weights_sel, conf, tuple(rules))
        name = Path(source).name if src_kind == "Video file" else f"webcam{source}"
        mgr = AlertManager(name, db=db, cooldown_s=cooldown)
        cap = open_source(source)
        fps, t_prev, n = None, time.perf_counter(), 0
        while cap.isOpened():
            ok, frame = cap.read()
            if not ok or (max_frames and n >= max_frames):
                break
            out = pipe.process(frame, fps)
            mgr.handle(frame, out.result)
            now = time.perf_counter()
            fps = 1 / max(now - t_prev, 1e-6) if fps is None else 0.9 * fps + 0.1 / max(now - t_prev, 1e-6)
            t_prev = now
            n += 1
            frame_ph.image(cv2.cvtColor(out.annotated, cv2.COLOR_BGR2RGB), channels="RGB", use_container_width=True)
            r = out.result
            fps_ph.metric("Dashboard FPS", f"{fps:.1f}")
            workers_ph.metric("Workers in frame", r.n_workers)
            comp_ph.metric("Compliance (frame)", "n/a" if r.compliance is None else f"{r.compliance:.0%}")
            alerts_ph.metric("Alerts this session", mgr.n_alerts)
            if r.violations:
                warn_ph.error("⚠️ VIOLATION: " + ", ".join(sorted({v.rule for v in r.violations})))
            else:
                warn_ph.success("No active violations")
        cap.release()
        st.info(f"Stopped after {n} frames. {mgr.n_alerts} alerts logged.")
    else:
        frame_ph.info("Pick a video or webcam in the sidebar and press Start.")

# ---------------- compliance ----------------
with tab_stats:
    stats = db.query(table="frame_stats")
    viol = db.query()
    if stats.empty:
        st.info("No data yet – run the live feed first.")
    else:
        stats["ts"] = pd.to_datetime(stats["ts"])
        s = stats[stats.n_workers > 0]
        overall = s.n_compliant.sum() / max(s.n_workers.sum(), 1)
        k1, k2, k3 = st.columns(3)
        k1.metric("Overall compliance (worker-samples)", f"{overall:.1%}")
        k2.metric("Violations logged (after cooldown)", len(viol))
        k3.metric("Sampled frames", len(stats))
        per_min = s.set_index("ts").resample("1min").sum(numeric_only=True)
        per_min = per_min[per_min.n_workers > 0]
        per_min["compliance_%"] = per_min.n_compliant / per_min.n_workers * 100
        st.plotly_chart(px.line(per_min.reset_index(), x="ts", y="compliance_%", markers=True,
                                title="Compliance % per minute", range_y=[0, 100]), use_container_width=True)
        if not viol.empty:
            viol["ts"] = pd.to_datetime(viol["ts"])
            vm = viol.groupby([pd.Grouper(key="ts", freq="1min"), "rule"]).size().reset_index(name="count")
            st.plotly_chart(px.bar(vm, x="ts", y="count", color="rule", title="Violations over time (per minute)"),
                            use_container_width=True)
            st.plotly_chart(px.pie(viol, names="rule", title="Violations by rule"), use_container_width=True)

# ---------------- log ----------------
with tab_log:
    today = dt.date.today()
    f1, f2, f3 = st.columns(3)
    d_from = f1.date_input("From", today - dt.timedelta(days=7))
    d_to = f2.date_input("To", today)
    rule_f = f3.selectbox("Rule", ["All"] + list(RULES.values()))
    df = db.query(start=d_from.isoformat(), end=(d_to + dt.timedelta(days=1)).isoformat(),
                  rule=None if rule_f == "All" else rule_f)
    st.caption(f"{len(df)} violations · stored in {config.VIOLATIONS_DB.relative_to(config.ROOT)}")
    st.dataframe(df.sort_values("ts", ascending=False), use_container_width=True, hide_index=True)
    st.download_button("⬇ Export CSV", df.to_csv(index=False), "violations.csv", "text/csv", disabled=df.empty)
    if not df.empty:
        vid = st.selectbox("Show snapshot for violation id", df.id.sort_values(ascending=False))
        snap = df.loc[df.id == vid, "snapshot"].iloc[0]
        if snap and Path(snap).exists():
            st.image(snap, caption=Path(snap).name)
