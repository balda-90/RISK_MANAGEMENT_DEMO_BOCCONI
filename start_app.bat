@echo off
echo Starting Automotive Risk Assessment Application...

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in PATH. Please install Python 3.8 or higher.
    pause
    exit /b
)

REM Check if virtual environment exists, create if not
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install requirements if needed
if not exist venv\Lib\site-packages\streamlit (
    echo Installing dependencies...
    pip install -r requirements.txt
)

REM Create needed directories
if not exist data mkdir data
if not exist config mkdir config
if not exist backend mkdir backend

REM Check for .env file
if not exist .env (
    echo Creating .env file template...
    copy .env-template .env
    echo Please edit the .env file and add your OpenAI API key.
    notepad .env
)

REM Start the Flask backend in a new window
echo Starting Flask backend...
start "Flask Backend" cmd /k "cd %~dp0 && call venv\Scripts\activate.bat && python backend/app.py"

REM Wait a moment for the backend to start
timeout /t 5

REM Run the Streamlit frontend
echo Starting Streamlit frontend...
start "Streamlit Frontend" cmd /k "cd %~dp0 && call venv\Scripts\activate.bat && streamlit run app.py"

REM Keep the main window open
echo Both services are now running in separate windows.
echo Close this window when you want to stop the application.
pause 