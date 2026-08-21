@echo off
setlocal enabledelayedexpansion
title PDF Password Remover - Build Script

echo.
echo  ==========================================
echo    PDF Password Remover  -  Build Script
echo  ==========================================
echo.

:: ── Check Python ──────────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found.
    echo  Please install Python 3.9+ from https://python.org and try again.
    echo  Make sure "Add Python to PATH" is checked during installation.
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('python --version 2^>^&1') do echo  Found: %%v

:: ── Create isolated virtual environment ───────────────────────────────────────
echo.
echo  [1/4]  Creating virtual environment...
if exist build_env (
    echo         (Removing old environment first)
    rmdir /s /q build_env
)
python -m venv build_env
if errorlevel 1 (
    echo  [ERROR] Failed to create virtual environment.
    pause & exit /b 1
)

:: ── Install dependencies ───────────────────────────────────────────────────────
echo  [2/4]  Installing dependencies (this may take a minute)...
call build_env\Scripts\activate.bat

pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

if errorlevel 1 (
    echo  [ERROR] Failed to install dependencies.
    pause & exit /b 1
)

:: ── Build with PyInstaller ─────────────────────────────────────────────────────
echo  [3/4]  Building executable...
echo.

pyinstaller PDF_Password_Remover.spec --noconfirm --clean

if errorlevel 1 (
    echo.
    echo  [ERROR] PyInstaller build failed. Check the output above for details.
    pause & exit /b 1
)

:: ── Done ───────────────────────────────────────────────────────────────────────
echo.
echo  [4/4]  Build complete!
echo.
echo  ==========================================
echo    Output file:  dist\PDF_Password_Remover.exe
echo  ==========================================
echo.
echo  This single .exe file is fully portable.
echo  No installation needed - just copy and run.
echo.

:: Optional: open the dist folder
set /p OPEN="  Open the dist folder now? [Y/N]: "
if /i "!OPEN!"=="Y" explorer dist

pause
