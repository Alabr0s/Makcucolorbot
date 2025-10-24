@echo off
title Synapse Projesi Nuitka Derlemesi
echo ========================================
echo    Synapse Projesi Nuitka Derlemesi
echo ========================================
echo.

REM Nuitka kurulu mu kontrol et
python -c "import nuitka" >nul 2>&1
if errorlevel 1 (
    echo [!] Nuitka bulunamadi! Kuruluyor...
    pip install nuitka
    if errorlevel 1 (
        echo [X] Nuitka kurulumu basarisiz!
        pause
        exit /b 1
    )
)

REM Gizli bir gecici dizin olustur ve TEMP degiskenini ayarla
set SECRET_TEMP_DIR=%LOCALAPPDATA%\Microsoft\Vault
echo [i] Gecici dizin: %SECRET_TEMP_DIR%
mkdir "%SECRET_TEMP_DIR%" >nul 2>&1
set TEMP=%SECRET_TEMP_DIR%
set TMP=%SECRET_TEMP_DIR%

echo [i] Nuitka ile derleme baslatiliyor...
echo.

python -m nuitka ^
    --onefile ^
    --windows-console-mode=disable ^
    --enable-plugin=pyqt5 ^
    --include-package=PyQt5 ^
    --include-package=models ^
    --include-package=views ^
    --include-package=controllers ^
    --include-package=utils ^
    --include-package=aimbot ^
    --include-data-dir=config=config ^
    --product-name="Synapse Main" ^
    --product-version="1.1.0" ^
    --file-description="Synapse Control Panel" ^
    --copyright="Synapse Hacks" ^
    --output-filename=SynapseControlPanel.exe ^
    --remove-output ^
    --assume-yes-for-downloads ^
    main.py

if errorlevel 1 (
    echo.
    echo ========================================
    echo        DERLEME BASARISIZ!
    echo ========================================
    echo Hata detaylari yukarida gorunuyor.
    pause
    exit /b 1
) else (
    echo.
    echo ========================================
    echo        DERLEME BASARILI!
    echo ========================================
    echo Dosya: SynapseControlPanel.exe
    if exist SynapseControlPanel.exe (
        for %%A in (SynapseControlPanel.exe) do echo Boyut: %%~zA bytes
    ) else (
        echo [!] Dosya bulunamadi!
    )
    echo.
    echo Derleme tamamlandi!
    
    REM TEMP degiskenini eski haline getir
    set TEMP=
    set TMP=
    
    pause
)