@echo off
REM ============================================
REM Streamlit TIMES Data Explorer - Launcher
REM ============================================

echo.
echo ========================================
echo   TIMES Data Explorer - Starting...
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

REM Check if we're in the correct directory (look for main.py)
if not exist "main.py" (
    echo [ERROR] main.py not found in current directory
    echo Please run this script from the project root folder
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo [INFO] Virtual environment not found. Creating one...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created
    echo.
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo [WARNING] requirements.txt not found
    echo Continuing without installing dependencies...
) else (
    REM Check if dependencies need to be installed
    echo [INFO] Checking dependencies...
    
    REM Simple check: if streamlit is not installed, install all requirements
    python -c "import streamlit" >nul 2>&1
    if errorlevel 1 (
        echo [INFO] Streamlit not found. Installing dependencies...
        echo [INFO] This may take a few minutes on first run...
        echo.
        python -m pip install --upgrade pip --quiet
        python -m pip install -r requirements.txt
        if errorlevel 1 (
            echo.
            echo [ERROR] Failed to install dependencies
            echo.
            echo Please try manually:
            echo   1. Open command prompt in this folder
            echo   2. Run: venv\Scripts\activate.bat
            echo   3. Run: pip install -r requirements.txt
            echo.
            pause
            exit /b 1
        )
        echo.
        echo [SUCCESS] Dependencies installed successfully!
        echo.
    ) else (
        echo [SUCCESS] Dependencies already installed
        echo.
    )
)

REM Check if inputs folder exists
if not exist "inputs" (
    echo [WARNING] 'inputs' folder not found
    echo Make sure you have the required CSV files in the inputs folder
    echo.
)

REM Verify streamlit is available
echo [INFO] Verifying Streamlit installation...
python -c "import streamlit; print('Streamlit version:', streamlit.__version__)" 2>nul
if errorlevel 1 (
    echo [ERROR] Streamlit is not properly installed
    echo.
    echo Please try:
    echo   1. Close this window
    echo   2. Delete the 'venv' folder
    echo   3. Run this script again
    echo.
    pause
    exit /b 1
)
echo.

REM Launch Streamlit
echo ========================================
echo   Launching Streamlit app...
echo ========================================
echo.
echo The app will open in your browser automatically
echo Press Ctrl+C in this window to stop the server
echo.

REM Run streamlit (browser will auto-open by default)
call streamlit run main.py

REM Keep window open if there's an error
echo.
echo [INFO] Streamlit has stopped
pause