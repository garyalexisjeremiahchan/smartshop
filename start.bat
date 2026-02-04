@echo off
echo ========================================
echo SmartShop Quick Start Script
echo ========================================
echo.

REM Activate virtual environment
echo [1/6] Activating virtual environment...
call .venv\Scripts\activate.bat
echo.

REM Check if migrations exist
echo [2/6] Running database migrations...
python manage.py migrate
echo.

REM Create superuser prompt
echo [3/6] Creating superuser (skip if already exists)...
echo You can skip this step if you already have a superuser account.
python manage.py createsuperuser
echo.

REM Populate categories
echo [4/6] Populating initial categories...
python manage.py populate_categories
echo.

REM Collect static files
echo [5/6] Collecting static files...
python manage.py collectstatic --noinput
echo.

REM Start server
echo [6/6] Starting development server...
echo.
echo ========================================
echo SmartShop is running!
echo ========================================
echo.
echo Access the website at: http://127.0.0.1:8000/
echo Access admin panel at: http://127.0.0.1:8000/admin/
echo.
echo Press Ctrl+C to stop the server
echo.
python manage.py runserver

pause
