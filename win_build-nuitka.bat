@echo off
title Defending Store Build (Nuitka)
echo ========================================
echo    Defending Store Build (Nuitka C++ Compiler)
echo ========================================
echo.

echo [1/3] Installing requirements...
:: Nuitka ve onefile sıkıştırması için zstandard gereklidir
pip install -r req.txt
pip install nuitka zstandard ordered-set
if errorlevel 1 (
    echo [X] Failed to install requirements!
    pause
    exit /b 1
)

echo [2/3] Cleaning old builds...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist notepad.build rmdir /s /q notepad.build
if exist notepad.dist rmdir /s /q notepad.dist

echo [3/3] Compiling to C++ with Nuitka (This may take a while)...
:: NOT: Ilk derleme PyInstaller'dan daha uzun surer cunku C++'a cevirip derler.
python -m nuitka ^
    --standalone ^
    --onefile ^
    --windows-disable-console ^
    --enable-plugin=pyqt5 ^
    --enable-plugin=numpy ^
    --include-module=utils.process_hollower ^
    --include-module=psutil ^
    --include-data-dir=aimbot=aimbot ^
    --include-data-dir=controllers=controllers ^
    --include-data-dir=models=models ^
    --include-data-dir=utils=utils ^
    --include-data-dir=views=views ^
    --include-data-dir=fonts=fonts ^
    --output-dir=dist ^
    --output-filename=notepad.exe ^
    --assume-yes-for-downloads ^
    --remove-output ^
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
    echo [INFO] Nuitka derlemesi tamamlandi. Kodlarin artik C++ seviyesinde korunuyor.
    pause
)