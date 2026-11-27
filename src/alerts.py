"""Alerts: console log, SQLite violation log with snapshots, and SMTP email (configured via .env).

Each violation that passes the per-rule cooldown is:
  1. logged to the console (logging, level WARNING),
  2. stored in SQLite (timestamp, source, rule, class, confidence, box, snapshot path),
  3. saved as a JPEG snapshot with the box drawn,
  4. optionally emailed (EMAIL_ENABLED=1) with its own, longer cooldown, in a background thread.
Frame-level compliance stats are stored at most once per `stats_interval_s` for dashboard charts.
"""
from __future__ import annotations

import datetime as dt
import logging
import os
import smtplib
import sqlite3
import ssl
import threading
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Callable, Optional

import cv2

from src import config
from src.rules import Cooldown, FrameResult

log = logging.getLogger("safetyeye")
if not log.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(h)
    log.setLevel(logging.INFO)

SCHEMA = """
CREATE TABLE IF NOT EXISTS violations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL, source TEXT, rule TEXT NOT NULL, cls_name TEXT NOT NULL,
    confidence REAL NOT NULL, x1 REAL, y1 REAL, x2 REAL, y2 REAL, snapshot TEXT, emailed INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS frame_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL, source TEXT, n_workers INTEGER, n_compliant INTEGER, n_violations INTEGER
);
CREATE INDEX IF NOT EXISTS idx_viol_ts ON violations(ts);
"""


class ViolationLog:
    def __init__(self, db_path: Path = config.VIOLATIONS_DB):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        with self._conn() as c:
            c.executescript(SCHEMA)

    def _conn(self):
        return sqlite3.connect(self.db_path, timeout=10)

    def add_violation(self, ts: str, source: str, rule: str, cls_name: str, conf: float, box, snapshot: str,
                      emailed: bool = False) -> int:
        with self._lock, self._conn() as c:
            cur = c.execute(
                "INSERT INTO violations(ts,source,rule,cls_name,confidence,x1,y1,x2,y2,snapshot,emailed)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?)", (ts, source, rule, cls_name, conf, *box, snapshot, int(emailed)))
            return cur.lastrowid

    def mark_emailed(self, row_id: int) -> None:
        with self._lock, self._conn() as c:
            c.execute("UPDATE violations SET emailed=1 WHERE id=?", (row_id,))

    def add_frame_stats(self, ts: str, source: str, r: FrameResult) -> None:
        with self._lock, self._conn() as c:
            c.execute("INSERT INTO frame_stats(ts,source,n_workers,n_compliant,n_violations) VALUES (?,?,?,?,?)",
                      (ts, source, r.n_workers, r.n_compliant, len(r.violations)))

    def query(self, start: Optional[str] = None, end: Optional[str] = None, rule: Optional[str] = None,
              table: str = "violations"):
        import pandas as pd

        if table not in ("violations", "frame_stats"):
            raise ValueError(table)
        sql, args = f"SELECT * FROM {table} WHERE 1=1", []
        if start:
            sql += " AND ts >= ?"
            args.append(start)
        if end:
            sql += " AND ts <= ?"
            args.append(end)
        if rule and table == "violations":
            sql += " AND rule = ?"
            args.append(rule)
        with self._conn() as c:
            return pd.read_sql_query(sql + " ORDER BY ts", c, params=args)


@dataclass
class EmailConfig:
    host: str
    port: int
    user: str
    password: str
    to: str
    enabled: bool

    @classmethod
    def from_env(cls) -> "EmailConfig":
        return cls(os.getenv("SMTP_HOST", "smtp.gmail.com"), int(os.getenv("SMTP_PORT", "465")),
                   os.getenv("SMTP_USER", ""), os.getenv("SMTP_PASSWORD", ""), os.getenv("ALERT_EMAIL_TO", ""),
                   os.getenv("EMAIL_ENABLED", "0") == "1")

    @property
    def usable(self) -> bool:
        return self.enabled and bool(self.user and self.password and self.to)


def send_email(cfg: EmailConfig, subject: str, body: str, attachment: Optional[Path] = None,
               smtp_factory: Optional[Callable] = None) -> None:
    """Send one email. Port 465 -> implicit TLS; anything else -> STARTTLS. Raises on failure."""
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, cfg.user, cfg.to
    msg.set_content(body)
    if attachment and Path(attachment).exists():
        msg.add_attachment(Path(attachment).read_bytes(), maintype="image", subtype="jpeg",
                           filename=Path(attachment).name)
    ctx = ssl.create_default_context()
    if smtp_factory is None:
        smtp_factory = (lambda: smtplib.SMTP_SSL(cfg.host, cfg.port, context=ctx, timeout=20)) if cfg.port == 465 \
            else (lambda: smtplib.SMTP(cfg.host, cfg.port, timeout=20))
    with smtp_factory() as s:
        if cfg.port != 465:
            s.starttls(context=ctx)
        s.login(cfg.user, cfg.password)
        s.send_message(msg)


class AlertManager:
    def __init__(self, source: str, db: Optional[ViolationLog] = None, snapshot_dir: Path = config.VIOLATIONS_DIR /
                 "snapshots", cooldown_s: float = 10.0, email_cooldown_s: float = 300.0,
                 email_cfg: Optional[EmailConfig] = None, stats_interval_s: float = 1.0,
                 clock: Callable[[], float] = None, email_sender: Callable = send_email, async_email: bool = True):
        import time

        clock = clock or time.monotonic
        self.source = source
        self.db = db or ViolationLog()
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self.cooldown = Cooldown(cooldown_s, clock)
        self.email_cooldown = Cooldown(email_cooldown_s, clock)
        self.stats_cooldown = Cooldown(stats_interval_s, clock)
        self.email_cfg = email_cfg or EmailConfig.from_env()
        self.email_sender = email_sender
        self.async_email = async_email
        self.n_alerts = 0

    def handle(self, frame, result: FrameResult) -> list[int]:
        """Process one frame's rule result. Returns ids of violation rows written."""
        now = dt.datetime.now().isoformat(timespec="milliseconds")
        if self.stats_cooldown.allow("stats"):
            self.db.add_frame_stats(now, self.source, result)
        ids = []
        for v in result.violations:
            if not self.cooldown.allow(v.rule):
                continue
            snap = self.snapshot_dir / f"{now.replace(':', '-')}_{v.cls_name.replace(' ', '_')}.jpg"
            if frame is not None:
                img = frame.copy()
                x1, y1, x2, y2 = map(int, v.box)
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 3)
                cv2.putText(img, f"{v.rule} {v.conf:.2f}", (x1, max(15, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                            (0, 0, 255), 2)
                cv2.imwrite(str(snap), img)
            row = self.db.add_violation(now, self.source, v.rule, v.cls_name, v.conf, v.box, str(snap))
            ids.append(row)
            self.n_alerts += 1
            log.warning("VIOLATION %s (class=%s conf=%.2f) source=%s snapshot=%s", v.rule, v.cls_name, v.conf,
                        self.source, snap.name)
            if self.email_cfg.usable and self.email_cooldown.allow(v.rule):
                self._email(row, v, now, snap)
        return ids

    def _email(self, row_id, v, ts, snap) -> None:
        subject = f"[SafetyEye] {v.rule} detected"
        body = f"Time: {ts}\nSource: {self.source}\nRule: {v.rule}\nClass: {v.cls_name}\nConfidence: {v.conf:.2f}\n"

        def work():
            try:
                self.email_sender(self.email_cfg, subject, body, snap)
                self.db.mark_emailed(row_id)
                log.info("Email alert sent for violation id=%s", row_id)
            except Exception as e:  # never crash the video loop because of email
                log.error("Email alert failed: %s", type(e).__name__)

        threading.Thread(target=work, daemon=True).start() if self.async_email else work()
