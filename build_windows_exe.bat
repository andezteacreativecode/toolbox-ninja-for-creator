@echo off
TITLE Build Windows Executable Installer - Clipper AI Desktop
cd /d "%~dp0"

echo ==========================================================
echo  🎬 Building Clipper AI Desktop - Executable (.exe) Wizard
echo ==========================================================
echo.

:: 1. Activate VENV if exists
if exist "venv\Scripts\activate.bat" (
    echo [1/4] Mengaktifkan Virtual Environment...
    call venv\Scripts\activate.bat
)

:: 2. Install PyInstaller
echo [2/4] Memeriksa PyInstaller...
pip install --upgrade pyinstaller

:: 3. Run PyInstaller Build
echo [3/4] Mengompilasi kode Python menjadi Executable...
pyinstaller --noconfirm clipper_build.spec

if %errorlevel% neq 0 (
    echo ❌ Gagal membuat PyInstaller build!
    pause
    exit /b %errorlevel%
)

:: 4. Build Inno Setup Installer if ISCC is installed
echo [4/4] Memeriksa Inno Setup Compiler (ISCC)...
set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

if exist "%ISCC_PATH%" (
    echo Mengompilasi Inno Setup Installer...
    "%ISCC_PATH%" inno_setup_script.iss
    echo.
    echo ==========================================================
    echo 🎉 BUILD SUKSES! File Installer siap digunakan:
    echo 📦 output_installer\ClipperAI_Desktop_v1.0_Setup.exe
    echo ==========================================================
) else (
    where iscc >nul 2>nul
    if %errorlevel% eq 0 (
        iscc inno_setup_script.iss
        echo.
        echo ==========================================================
        echo 🎉 BUILD SUKSES! File Installer siap digunakan:
        echo 📦 output_installer\ClipperAI_Desktop_v1.0_Setup.exe
        echo ==========================================================
    ) else (
        echo ⚠️ Inno Setup Compiler belum terinstall.
        echo Folder executable mandiri telah dibuat di:
        echo 📂 dist\ClipperAIDesktop\
        echo (Anda dapat langsung menjalankan ClipperAIDesktop.exe di folder tersebut)
    )
)

pause
