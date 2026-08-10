@echo off
TITLE Clipper AI Desktop - Automatic Setup Wizard for Windows
cd /d "%~dp0"

echo ==========================================================
echo  🎬 Clipper AI Desktop - Setup Wizard Otomatis (Windows)
echo ==========================================================
echo.

:: 1. Cek & Install Python via winget jika belum ada
echo [1/5] Memeriksa Python...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ⚠️ Python belum terinstall. Menginstall Python via winget...
    winget install -e --id Python.Python.3.11 --accept-package-agreements --accept-source-agreements
    echo Mohon restart CMD/PowerShell setelah instalasi Python jika diperlukan.
) else (
    echo ✅ Python sudah terinstall.
)

:: 2. Cek & Install FFmpeg via winget jika belum ada
echo [2/5] Memeriksa FFmpeg (Pemotong Video)...
where ffmpeg >nul 2>nul
if %errorlevel% neq 0 (
    echo ⚠️ FFmpeg belum terinstall. Menginstall FFmpeg via winget...
    winget install -e --id Gyan.FFmpeg --accept-package-agreements --accept-source-agreements
) else (
    echo ✅ FFmpeg sudah terinstall.
)

:: 3. Cek & Install Ollama via winget jika belum ada
echo [3/5] Memeriksa Ollama (AI Lokal)...
where ollama >nul 2>nul
if %errorlevel% neq 0 (
    echo ⚠️ Ollama belum terinstall. Menginstall Ollama...
    winget install -e --id Ollama.Ollama --accept-package-agreements --accept-source-agreements
    if %errorlevel% neq 0 (
        echo Opening Ollama download page...
        start https://ollama.com/download/OllamaSetup.exe
    )
) else (
    echo ✅ Ollama sudah terinstall.
)

:: 4. Unduh Model AI Lokal (gemma2:2b)
echo [4/5] Mengunduh Model AI Lokal (gemma2:2b)...
ollama pull gemma2:2b

:: 5. Setup Python Virtual Environment & Install Library
echo [5/5] Menginstall Library Python...
if not exist "venv" (
    python -m venv venv
)
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

:: Membuat Shortcut di Desktop Windows via PowerShell
powershell -Command "$s=(New-Object -COM WScript.Shell).CreateShortcut([System.IO.Path]::Combine([Environment]::GetFolderPath('Desktop'), 'Clipper AI Desktop.lnk')); $s.TargetPath='%~dp0run.bat'; $s.WorkingDirectory='%~dp0'; $s.IconLocation='%~dp0assets\ninja_logo.jpg'; $s.Save()"

echo.
echo ==========================================================
echo 🎉 Pemasangan Selesai 100%!
echo Shortcut 'Clipper AI Desktop' telah dibuat di Desktop Anda.
echo Cukup klik ganda ikon tersebut atau jalankan run.bat
echo ==========================================================
pause
