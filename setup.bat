@echo off
REM THAR Bengaluru Backend Setup Script for Windows

echo ======================================
echo THAR Bengaluru Backend Setup
echo ======================================

REM Create virtual environment
echo.
echo 1. Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo.
echo 2. Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo.
echo 3. Installing dependencies...
pip install -r requirements.txt

REM Create .env file from template
echo.
echo 4. Creating .env file...
if not exist .env (
    copy .env.example .env
    echo Created .env file. Please update with your database credentials.
) else (
    echo .env file already exists.
)

echo.
echo ======================================
echo Setup complete!
echo ======================================
echo.
echo Next steps:
echo 1. Update .env file with your PostgreSQL credentials
echo 2. Ensure PostgreSQL is running
echo 3. Run: python main.py
echo 4. Visit: http://localhost:8000/docs
pause
