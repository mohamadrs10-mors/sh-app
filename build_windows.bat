@echo off
REM ساخت یک فایل exe تک: dist\ShApp.exe  (فقط Python 3.11+ لازم است)
cd /d "%~dp0backend"
python -m pip install -r requirements.txt pyinstaller || exit /b 1
python -m pytest -q || exit /b 1
pyinstaller --onefile --noconsole --name ShApp ^
  --add-data "app\web;web" --collect-submodules uvicorn ^
  run.py || exit /b 1
echo.
echo Done: backend\dist\ShApp.exe
