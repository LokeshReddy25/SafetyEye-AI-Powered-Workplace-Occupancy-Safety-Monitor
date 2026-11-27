from unittest import mock

import numpy as np

from src.alerts import AlertManager, EmailConfig, ViolationLog, send_email
from src.rules import Detection, RuleEngine

CFG = EmailConfig("smtp.example.com", 465, "sender@example.com", "secret", "to@example.com", True)


def _frame_result():
    return RuleEngine().evaluate([Detection("Person", 0.9, (10, 10, 60, 120)),
                                  Detection("NO-Hardhat", 0.8, (20, 10, 50, 35))])


def _mgr(tmp_path, t, sender, cfg=CFG):
    return AlertManager("test.mp4", db=ViolationLog(tmp_path / "v.db"), snapshot_dir=tmp_path / "snaps",
                        cooldown_s=5, email_cooldown_s=60, email_cfg=cfg, clock=lambda: t[0],
                        email_sender=sender, async_email=False)


def test_violation_logged_with_snapshot_and_cooldown(tmp_path):
    t = [0.0]
    sender = mock.Mock()
    m = _mgr(tmp_path, t, sender)
    frame = np.zeros((150, 100, 3), np.uint8)
    assert len(m.handle(frame, _frame_result())) == 1
    assert m.handle(frame, _frame_result()) == []          # within cooldown -> suppressed
    t[0] = 6
    assert len(m.handle(frame, _frame_result())) == 1     # after cooldown
    df = m.db.query()
    assert len(df) == 2
    assert set(df.columns) >= {"ts", "rule", "cls_name", "confidence", "snapshot"}
    assert df.iloc[0]["rule"] == "Missing hardhat" and abs(df.iloc[0]["confidence"] - 0.8) < 1e-6
    assert len(list((tmp_path / "snaps").glob("*.jpg"))) == 2
    # email has a longer cooldown: only the first violation emailed
    assert sender.call_count == 1
    assert df.iloc[0]["emailed"] == 1 and df.iloc[1]["emailed"] == 0
    assert len(m.db.query(table="frame_stats")) >= 1


def test_query_filters(tmp_path):
    db = ViolationLog(tmp_path / "v.db")
    db.add_violation("2026-01-01T10:00:00", "s", "Missing hardhat", "NO-Hardhat", 0.9, (0, 0, 1, 1), "a.jpg")
    db.add_violation("2026-01-02T10:00:00", "s", "Missing safety vest", "NO-Safety Vest", 0.7, (0, 0, 1, 1), "b.jpg")
    assert len(db.query(start="2026-01-02")) == 1
    assert len(db.query(rule="Missing hardhat")) == 1
    assert len(db.query(end="2026-01-01T23:59:59")) == 1


def test_email_failure_does_not_raise(tmp_path):
    t = [0.0]
    sender = mock.Mock(side_effect=OSError("network down"))
    m = _mgr(tmp_path, t, sender)
    assert len(m.handle(np.zeros((150, 100, 3), np.uint8), _frame_result())) == 1
    assert m.db.query().iloc[0]["emailed"] == 0


def test_email_not_sent_when_disabled(tmp_path):
    sender = mock.Mock()
    cfg = EmailConfig("h", 465, "u", "p", "to", enabled=False)
    _mgr(tmp_path, [0.0], sender, cfg).handle(None, _frame_result())
    sender.assert_not_called()


def test_send_email_uses_smtp_and_attaches_snapshot(tmp_path):
    snap = tmp_path / "s.jpg"
    snap.write_bytes(b"\xff\xd8fakejpeg")
    smtp = mock.MagicMock()
    send_email(CFG, "subj", "body", snap, smtp_factory=lambda: smtp)
    inst = smtp.__enter__.return_value
    inst.login.assert_called_once_with("sender@example.com", "secret")
    msg = inst.send_message.call_args[0][0]
    assert msg["Subject"] == "subj" and msg["To"] == "to@example.com"
    assert any(p.get_filename() == "s.jpg" for p in msg.iter_attachments())
    inst.starttls.assert_not_called()                     # port 465 = implicit TLS


def test_send_email_starttls_on_587():
    smtp = mock.MagicMock()
    cfg = EmailConfig("h", 587, "u", "p", "to", True)
    send_email(cfg, "s", "b", None, smtp_factory=lambda: smtp)
    smtp.__enter__.return_value.starttls.assert_called_once()
