@echo off
TITLE QuantOS - First Run Setup
CLS

echo ==================================================
echo      QuantOS v9.8 - Golden Master Setup
echo ==================================================
echo.

:: 1. CRITICAL FIX: Force Windows to use the current folder
cd /d "%~dp0"

:: 2. Check if Python is installed
echo [1/4] Checking for Python...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Python is not installed or not in your PATH.
    echo.
    echo --------------------------------------------------
    echo OPTION A: Install Python Manually
    echo 1. Go to python.org and download Python 3.12.
    echo 2. IMPORTANT: Check the box "Add Python to PATH" during install.
    echo --------------------------------------------------
    echo.
    echo Opening download page for you...
    start https://www.python.org/downloads/
    pause
    exit
)

:: 3. Create the Virtual Environment
IF NOT EXIST "venv" (
    echo [2/4] Creating virtual environment (First run only)...
    echo        This may take a minute...
    python -m venv venv
    IF %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create venv. Python might be corrupted.
        pause
        exit
    )
)

:: 4. Install Dependencies
echo [3/4] Installing libraries...
call venv\Scripts\activate.bat
pip install -r requirements.txt >nul 2>&1

:: 5. Launch the Bot
echo [4/4] Starting QuantOS...
echo.
echo --------------------------------------------------
echo  Keep this window open. The Dashboard will launch.
echo --------------------------------------------------
python main.py

pause
