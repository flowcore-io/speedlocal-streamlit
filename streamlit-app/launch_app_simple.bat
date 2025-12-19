@echo off
REM ============================================
REM TIMES Data Explorer - Simple Launcher
REM ============================================

echo Starting TIMES Data Explorer...
echo.

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo [WARNING] Virtual environment not found at venv\
    echo Please run the full launch_app.bat first to set up the environment
    pause
    exit /b 1
)

REM Launch Streamlit
echo Launching Streamlit...
echo.
call streamlit run main.py

pause
