@echo off
setlocal EnableDelayedExpansion
title Adaptive Learning System Lab - Setup ^& Launch
color 0A

echo.
echo  ============================================================
echo   ADAPTIVE LEARNING SYSTEM LAB v1.0
echo   BKT + SM-2 + Decision Engine + Interactive Dashboard
echo  ============================================================
echo.

:: ── CHECK PYTHON ──
echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+ from python.org
    echo         Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [OK] Python %PYVER% found

:: ── CHECK/CREATE VENV ──
echo.
echo [2/6] Setting up virtual environment...
if not exist "venv\" (
    echo  Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo  [OK] Virtual environment created
) else (
    echo  [OK] Virtual environment already exists
)

:: ── ACTIVATE VENV ──
echo.
echo [3/6] Activating environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo  [OK] Activated

:: ── INSTALL DEPS ──
echo.
echo [4/6] Installing dependencies (first run may take ~60 seconds)...
pip install -r requirements.txt -q --no-warn-script-location
if errorlevel 1 (
    echo [WARN] Some packages may have failed - trying individually...
    pip install flask flask-cors numpy pandas requests -q
)
echo  [OK] Dependencies ready

:: ── GENERATE DATASETS ──
echo.
echo [5/6] Pre-generating all datasets...
if not exist "data\" mkdir data
python -c "import sys; sys.path.insert(0,'backend'); from datasets import preload_all; preload_all(); print('[OK] All datasets generated')"
if errorlevel 1 (
    echo [WARN] Dataset pre-generation had warnings - will generate on demand
)

:: ── LAUNCH SERVER ──
echo.
echo [6/6] Starting server...
echo  Dashboard URL: http://localhost:5000
echo.
echo  ╔══════════════════════════════════════════════════════╗
echo  ║  Server is starting...                               ║
echo  ║  Browser will open automatically in 3 seconds       ║
echo  ║  Press Ctrl+C to stop the server                    ║
echo  ╚══════════════════════════════════════════════════════╝
echo.

:: Auto-open browser after 3s
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:5000"

:: Start server
python backend/server.py

echo.
echo [Server stopped]
pause
