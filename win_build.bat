@echo off
title Defending Store Build
echo ========================================
echo    Defending Store Build
echo ========================================
echo.

echo [1/3] Installing requirements...
pip install -r req.txt
if errorlevel 1 (
    echo [X] Failed to install requirements!
    pause
    exit /b 1
)

echo [2/3] Installing PyInstaller...
pip install pyinstaller
if errorlevel 1 (
    echo [X] Failed to install PyInstaller!
    pause
    exit /b 1
)

echo [3/3] Building executable as notepad.exe...
python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name "notepad" ^
    --hidden-import utils.process_hollower ^
    --hidden-import psutil ^
    --add-data "aimbot;aimbot" ^
    --add-data "controllers;controllers" ^
    --add-data "models;models" ^
    --add-data "utils;utils" ^
    --add-data "views;views" ^
    --add-data "fonts;fonts" ^
    main.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo        BUILD FAILED!
    echo ========================================
    echo Check error details above.
    pause
    exit /b 1
) else (
    echo.
    echo ========================================
    echo        BUILD SUCCESSFUL!
    echo ========================================
    echo File: dist\notepad.exe
    if exist dist\notepad.exe (
        for %%A in (dist\notepad.exe) do echo Size: %%~zA bytes
    ) else (
        echo [!] File not found!
    )
    echo.
    echo This executable will appear as "notepad.exe" in:
    echo - Task Manager
    echo - Process list
    echo - Running processes
    echo.
    echo Build completed!
    pause
)