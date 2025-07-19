@echo off
rem Live TV Player Setup Script for Windows
rem This script sets up the Python virtual environment and installs dependencies

echo 🚀 Setting up Live TV Player...
echo ==================================

rem Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not in PATH
    echo Please install Python 3.7+ and try again
    pause
    exit /b 1
)

echo ✅ Found Python
python --version

echo 📦 Creating virtual environment...
if exist venv (
    echo ⚠️  Virtual environment already exists. Removing old one...
    rmdir /s /q venv
)

python -m venv venv

echo 🔧 Activating virtual environment...
call venv\Scripts\activate

echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip

echo 📥 Installing dependencies...
if exist requirements.txt (
    pip install -r requirements.txt
) else (
    echo ❌ Error: requirements.txt not found
    pause
    exit /b 1
)

echo.
echo ✅ Setup complete!
echo ==================================
echo.
echo 🎉 Your Live TV Player is ready!
echo.
echo To start the application:
echo   1. Run: venv\Scripts\activate
echo   2. Run: python app.py
echo   3. Open: http://localhost:7734
echo.
echo Or use the activation script:
echo   activate_venv.bat
echo.
pause
