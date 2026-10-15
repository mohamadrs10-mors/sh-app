"""یک فایل برای همه‌چیز: سرور را بالا می‌آورد و برنامه را در پنجره‌ی Edge/Chrome (حالت app) باز می‌کند.

python run.py          -> پنجره‌ی برنامه؛ با بستن پنجره برنامه خاموش می‌شود
python run.py --no-ui  -> فقط سرور
"""
import argparse
import os
import shutil
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
    for _ in range(tries):
        try:
            urllib.request.urlopen(url + "/health", timeout=1)
            return True
        except Exception:
            time.sleep(0.1)
    return False


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
    from app.main import PORT, _last_ping, app
    import uvicorn

    url = f"http://127.0.0.1:{PORT}"
    if healthy(url):  # نسخه‌ی دیگری از برنامه باز است
        if not a.no_ui:
            open_window(url)
        return

    lan = a.lan or bool(config.load().get("lan"))
    server = uvicorn.Server(uvicorn.Config(app, host="0.0.0.0" if lan else "127.0.0.1",
                                           port=PORT, log_level="warning", log_config=None))
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    if not healthy(url, tries=100):
        alert(f"سرور بالا نیامد (شاید پورت {PORT} توسط برنامه‌ی دیگری اشغال است).\nجزئیات: {LOG}")
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
