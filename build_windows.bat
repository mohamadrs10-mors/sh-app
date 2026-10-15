@echo off
REM 1) بک‌اند پایتون -> backend.exe
cd backend
pip install -r requirements.txt pyinstaller || exit /b 1
pyinstaller --onefile --name backend run.py || exit /b 1
cd ..
REM 2) برنامه‌ی Flutter (یک‌بار: flutter create --platforms=windows,android,ios . داخل پوشه‌ی app)
cd app
flutter pub get && flutter build windows --release || exit /b 1
REM 3) کنار هم گذاشتن
mkdir build\windows\x64\runner\Release\backend 2>nul
copy ..\backend\dist\backend.exe build\windows\x64\runner\Release\backend\
echo Done: app\build\windows\x64\runner\Release\
