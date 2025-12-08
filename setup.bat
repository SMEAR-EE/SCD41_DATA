@echo off
setlocal ENABLEDELAYEDEXPANSION

echo ================================================
echo   SMEAR Estonia CO2 Processing - Setup (Windows)
echo ================================================

REM -------------------------------
REM Check Python is available
REM -------------------------------
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python not found! Please install Python 3.x and ensure it is in PATH.
    goto :error
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo Found Python %PYVER%

REM -------------------------------
REM Check requirements.txt exists
REM -------------------------------
if not exist requirements.txt (
    echo.
    echo ERROR: requirements.txt not found in the current directory.
    goto :error
)

REM -------------------------------
REM Create virtual environment (safe)
REM -------------------------------
if exist venv (
    echo.
    echo Virtual environment already exists at .\venv
) else (
    echo.
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to create virtual environment.
        goto :error
    )
)

REM -------------------------------
REM Activate virtual environment
REM -------------------------------
if exist venv\Scripts\activate.bat (
    echo.
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo.
    echo ERROR: venv\Scripts\activate.bat not found. Virtual environment creation may have failed.
    goto :error
)

REM -------------------------------
REM Upgrade pip, setuptools, wheel
REM -------------------------------
echo.
echo Upgrading pip, setuptools, and wheel...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 (
    echo.
    echo ERROR: Failed to upgrade pip/setuptools/wheel.
    goto :error
)

REM -------------------------------
REM Install dependencies
REM -------------------------------
echo.
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install dependencies from requirements.txt.
    goto :error
)

REM -------------------------------
REM Create directory structure (idempotent)
REM -------------------------------
echo.
echo Creating directory structure (non-destructive)...

mkdir output\individual 2>nul
mkdir output\parquet 2>nul
mkdir output\logs 2>nul
mkdir output\plots 2>nul
mkdir config 2>nul
mkdir notebooks 2>nul

echo   ✓ Ensured: output\individual
echo   ✓ Ensured: output\parquet
echo   ✓ Ensured: output\logs
echo   ✓ Ensured: output\plots
echo   ✓ Ensured: config
echo   ✓ Ensured: notebooks

REM -------------------------------
REM Create default config\sensors.yaml if missing
REM -------------------------------
if not exist config\sensors.yaml (
    echo Creating config\sensors.yaml from template...
    copy config\sensors.example.yaml config\sensors.yaml
    echo Edit config\sensors.yaml before running!
)


echo.
echo ================================================
echo   ✓ Setup Complete! (No destructive actions)
echo ================================================
echo.
echo Next steps:
echo   1. Activate the environment:
echo      venv\Scripts\activate
echo.
echo   2. Edit config\sensors.yaml with your paths
echo.
echo   3. Run processing:
echo      jupyter notebook notebooks\process_data.ipynb
echo.
pause
goto :eof

REM -------------------------------
REM Error handler
REM -------------------------------
:error
echo.
echo ================================================
echo   Setup failed. See error messages above.
echo ================================================
echo.
pause
exit /b 1
