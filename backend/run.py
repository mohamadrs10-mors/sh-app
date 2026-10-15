"""یک فایل برای همه‌چیز: سرور را بالا می‌آورد و پنجره‌ی برنامه را باز می‌کند.

python run.py            -> پنجره‌ی برنامه (یا مرورگر اگر پنجره‌ی داخلی نبود)
python run.py --no-ui    -> فقط سرور
"""
import argparse
import os
import sys
import threading
import time
import urllib.request
import webbrowser

import uvicorn

from app import config
from app.main import PORT, app


def wait_ready(url: str) -> bool:
    for _ in range(100):
        try:
            urllib.request.urlopen(url + "/health", timeout=1)
            return True
        except Exception:
            time.sleep(0.1)
    return False


if __name__ == "__main__":
    if sys.stdout is None or sys.stderr is None:  # exe بدون کنسول
        sys.stdout = sys.stderr = open(os.devnull, "w")
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-ui", action="store_true")
    ap.add_argument("--lan", action="store_true", help="اجازه‌ی اتصال از شبکه‌ی محلی (موبایل)")
    a = ap.parse_args()
    lan = a.lan or bool(config.load().get("lan"))
    host = "0.0.0.0" if lan else "127.0.0.1"
    url = f"http://127.0.0.1:{PORT}"

    server = uvicorn.Server(uvicorn.Config(app, host=host, port=PORT, log_level="warning"))
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    if not wait_ready(url):
        raise SystemExit("سرور بالا نیامد (شاید پورت ۸۷۶۵ اشغال است)")

    if a.no_ui:
        t.join()
    else:
        try:
            import webview  # pywebview: پنجره‌ی بومی ویندوز (WebView2)

            webview.create_window("یابنده‌ی محصول پرفروش", url, width=1200, height=800)
            webview.start()
        except Exception:
            webbrowser.open(url)
            t.join()
        server.should_exit = True
