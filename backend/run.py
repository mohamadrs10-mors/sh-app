"""یک فایل برای همه‌چیز: سرور را بالا می‌آورد و برنامه را در پنجره‌ی Edge/Chrome (حالت app) باز می‌کند.

python run.py          -> پنجره‌ی برنامه؛ با بستن پنجره برنامه خاموش می‌شود
python run.py --no-ui  -> فقط سرور
"""
import argparse
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import traceback
import urllib.request
import webbrowser
from pathlib import Path

HOME = Path.home() / ".sh-app"
HOME.mkdir(parents=True, exist_ok=True)
LOG = HOME / "log.txt"


def log(msg: str) -> None:
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%H:%M:%S')} {msg}\n")
    except Exception:
        pass


def alert(msg: str) -> None:
    log(msg)
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.user32.MessageBoxW(0, msg, "یابنده‌ی محصول", 0x10)
    else:
        print(msg, file=sys.stderr)


def healthy(url: str, tries: int = 1) -> bool:
    """سرور همین برنامه روی این آدرس زنده است؟ (نه هر برنامه‌ی دیگری)"""
    for _ in range(tries):
        try:
            with urllib.request.urlopen(url + "/health", timeout=1) as r:
                if b'"shapp"' in r.read():
                    return True
        except Exception:
            time.sleep(0.1)
    return False


def port_free(port: int, host: str) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return True
        except OSError:
            return False


def pick_port(preferred: int, host: str) -> int:
    """۸۷۶۵ اگر آزاد بود؛ وگرنه یک پورت آزاد که سیستم‌عامل بدهد."""
    if port_free(preferred, host):
        return preferred
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, 0))
        return s.getsockname()[1]


def find_browser() -> str | None:
    cands = []
    if sys.platform == "win32":
        for env in ("PROGRAMFILES(X86)", "PROGRAMFILES", "LOCALAPPDATA"):
            base = os.environ.get(env)
            if base:
                cands += [Path(base) / "Microsoft/Edge/Application/msedge.exe",
                          Path(base) / "Google/Chrome/Application/chrome.exe"]
        for c in cands:
            if c.exists():
                return str(c)
    for name in ("msedge", "microsoft-edge", "google-chrome", "chromium", "chrome"):
        if shutil.which(name):
            return shutil.which(name)
    return None


def open_window(url: str) -> subprocess.Popen | None:
    exe = find_browser()
    if exe:
        try:
            return subprocess.Popen([exe, f"--app={url}", f"--user-data-dir={HOME / 'profile'}",
                                     "--no-first-run", "--no-default-browser-check",
                                     "--window-size=1280,820"])
        except Exception:
            log(traceback.format_exc())
    webbrowser.open(url)
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-ui", action="store_true")
    ap.add_argument("--lan", action="store_true", help="اجازه‌ی اتصال از شبکه‌ی محلی (موبایل)")
    a = ap.parse_args()

    from app import config
    import app.main as m
    import uvicorn

    url = f"http://127.0.0.1:{m.PORT}"
    if healthy(url):  # نسخه‌ی دیگری از همین برنامه باز است
        if not a.no_ui:
            open_window(url)
        return

    lan = a.lan or bool(config.load().get("lan"))
    host = "0.0.0.0" if lan else "127.0.0.1"
    m.PORT = pick_port(m.PORT, host)
    if m.PORT != 8765:
        log(f"port 8765 busy, using {m.PORT}")
    url = f"http://127.0.0.1:{m.PORT}"
    _last_ping = m._last_ping
    server = uvicorn.Server(uvicorn.Config(m.app, host=host, port=m.PORT,
                                           log_level="warning", log_config=None))
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    if not healthy(url, tries=100):
        alert(f"سرور بالا نیامد.\nجزئیات: {LOG}")
        return
    log("server up")
    if a.no_ui:
        t.join()
        return

    proc = open_window(url)
    # خاموش شدن خودکار: صفحه هر چند ثانیه /api/ping می‌زند؛ اگر دیگر نزد، برنامه بسته شده است.
    started = time.time()
    while t.is_alive():
        time.sleep(2)
        seen = _last_ping["t"]
        if seen and time.time() - seen > 25:
            break
        if not seen and time.time() - started > 60:
            break
    server.should_exit = True


if __name__ == "__main__":
    if sys.stdout is None or sys.stderr is None:  # exe بدون کنسول
        sys.stdout = sys.stderr = open(os.devnull, "w")
    try:
        main()
    except Exception:
        alert("خطای برنامه:\n" + traceback.format_exc()[-800:])
