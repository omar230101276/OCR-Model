@echo off
echo ===================================================
echo      SpecSense AI - Project Startup Script
echo ===================================================
echo.

if not exist ..\venv (
    echo [INFO] Creating virtual environment...
    python -m venv ..\venv
)

echo [INFO] Activating virtual environment...
call ..\venv\Scripts\activate

echo [INFO] Step 1: Checking Dependencies...
pip install -r ..\requirements.txt --default-timeout=1000
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies. Please check your internet connection and try again.
    pause
    exit /b %errorlevel%
)
echo.
echo [INFO] Step 2: Launching Application...
echo.
echo [TIP] The application will open in your default browser.
echo [TIP] If it doesn't open automatically, visit http://localhost:8501
echo.
streamlit run app.py
pause
