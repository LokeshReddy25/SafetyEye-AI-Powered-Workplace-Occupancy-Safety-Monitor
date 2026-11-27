"""Take dashboard screenshots with headless Chromium (Playwright). Requires `streamlit run app.py` on :8501.

Usage: python scripts/screenshot_dashboard.py
"""
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parents[1] / "docs"
URL = "http://localhost:8501"

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1500, "height": 1100})
    # Live tab: autostart on hardhat.mp4 with the selected weights, let it run a few seconds
    pg.goto(f"{URL}/?autostart=1&weights=best&video=hardhat.mp4&frames=100000")
    pg.wait_for_timeout(25000)
    pg.screenshot(path=str(OUT / "dashboard_live.png"))
    # Other tabs without autostart
    pg.goto(URL)
    pg.wait_for_timeout(6000)
    for tab, name in (("Compliance", "dashboard_compliance.png"), ("Violation log", "dashboard_log.png")):
        pg.get_by_role("tab", name=tab).click()
        pg.wait_for_timeout(4000)
        pg.screenshot(path=str(OUT / name), full_page=True)
    b.close()
print("saved to", OUT)
