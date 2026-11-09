@echo off
setlocal
cd /d "%~dp0"

set "PYTHON=.venv\Scripts\python.exe"

if exist "%PYTHON%" goto install

py -3.13 --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo Python 3.13 was not found. Install it from https://www.python.org/downloads/
    echo and tick "Add python.exe to PATH" in the installer, then run this again.
    echo.
    pause
    exit /b 1
)

echo Creating the virtual environment...
py -3.13 -m venv .venv
if errorlevel 1 (
    echo Could not create the virtual environment.
    pause
    exit /b 1
)

:install
fc /b requirements.txt .venv\requirements.installed >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies. The first run takes a few minutes...
    "%PYTHON%" -m pip install --quiet --disable-pip-version-check -r requirements.txt
    if errorlevel 1 (
        echo Could not install dependencies. Check your internet connection.
        pause
        exit /b 1
    )
    copy /y requirements.txt .venv\requirements.installed >nul
)

"%PYTHON%" main.py %*
if errorlevel 1 pause
