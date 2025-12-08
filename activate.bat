@echo off
REM Quick activation script for Windows
REM Usage:
REM   call activate.bat

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo.
    echo ✓ Virtual environment activated
    echo.
    echo Quick commands:
    echo   jupyter notebook           - Start Jupyter
    echo   python                     - Python shell
    echo   deactivate                 - Exit venv
    echo.
) else (
    echo.
    echo ERROR: Virtual environment not found!
    echo Run setup.bat first to create it.
    exit /b 1
)
