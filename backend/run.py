"""نقطه‌ی ورود (برای PyInstaller هم استفاده می‌شود): python run.py [--host 0.0.0.0] [--port 8765]"""
import argparse

import uvicorn

from app.main import app

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()
    uvicorn.run(app, host=a.host, port=a.port, log_level="warning")
