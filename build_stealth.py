#!/usr/bin/env python3
"""
Build script for creating a stealth version of the application
"""

import os
import sys
import subprocess
import shutil

def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "req.txt"])
        print("Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install requirements: {e}")
        return False

def build_executable():
    """Build executable with PyInstaller"""
    print("Building executable...")
    try:
        # Create spec file for PyInstaller
        spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('aimbot/*', 'aimbot'), ('controllers/*', 'controllers'), 
           ('models/*', 'models'), ('utils/*', 'utils'), ('views/*', 'views'),
           ('fonts/*', 'fonts')],
    hiddenimports=['utils.process_hollower', 'psutil'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DefendingStore',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico'  # Add your icon file here
)
'''
        
        # Write spec file
        with open('defending_store.spec', 'w') as f:
            f.write(spec_content)
        
        # Build with PyInstaller
        subprocess.check_call([
            sys.executable, "-m", "PyInstaller", 
            "--onefile", 
            "--windowed",
            "--name", "DefendingStore",
            "--hidden-import", "utils.process_hollower",
            "--hidden-import", "psutil",
            "main.py"
        ])
        
        print("Executable built successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to build executable: {e}")
        return False
    except FileNotFoundError:
        print("PyInstaller not found. Please install it with: pip install pyinstaller")
        return False

def main():
    """Main build function"""
    print("=== Defending Store Stealth Build Script ===")
    
    # Change to project directory
    project_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_dir)
    
    print(f"Working directory: {project_dir}")
    
    # Install requirements
    if not install_requirements():
        print("Failed to install requirements. Exiting.")
        return False
    
    # Build executable
    if not build_executable():
        print("Failed to build executable. Exiting.")
        return False
    
    print("\n=== Build completed successfully! ===")
    print("Executable location: dist/DefendingStore.exe")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)