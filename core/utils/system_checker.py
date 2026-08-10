import os
import sys
import shutil
import subprocess
import urllib.request
import zipfile
import json
from pathlib import Path

def get_app_dir() -> Path:
    """Returns local user app directory for Clipper Desktop (%LOCALAPPDATA%/ClipperDesktop or ~/.clipper_desktop)."""
    if os.name == 'nt':
        base = os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData' / 'Local'))
        app_dir = Path(base) / 'ClipperDesktop'
    else:
        app_dir = Path.home() / '.clipper_desktop'
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir

def get_bin_dir() -> Path:
    bin_dir = get_app_dir() / 'bin'
    bin_dir.mkdir(parents=True, exist_ok=True)
    return bin_dir

def ensure_bin_path():
    """Adds the app bin directory to os.environ['PATH'] so subprocesses find local ffmpeg."""
    bin_dir = str(get_bin_dir())
    if bin_dir not in os.environ.get('PATH', ''):
        os.environ['PATH'] = bin_dir + os.pathsep + os.environ.get('PATH', '')

class SystemChecker:
    @staticmethod
    def is_ffmpeg_installed() -> bool:
        ensure_bin_path()
        return shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None

    @staticmethod
    def is_ollama_installed() -> bool:
        return shutil.which("ollama") is not None

    @staticmethod
    def is_ollama_running() -> bool:
        try:
            req = urllib.request.Request("http://localhost:11434/api/tags", headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False

    @staticmethod
    def has_ollama_model(model_name: str = "gemma2:2b") -> bool:
        try:
            req = urllib.request.Request("http://localhost:11434/api/tags", headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    models = [m.get('name', '') for m in data.get('models', [])]
                    return any(model_name in m for m in models)
        except Exception:
            pass
        return False

    @staticmethod
    def download_ffmpeg(progress_callback=None) -> bool:
        """Downloads static ffmpeg zip for Windows and extracts to local bin directory."""
        bin_dir = get_bin_dir()
        ffmpeg_exe = bin_dir / ("ffmpeg.exe" if os.name == 'nt' else "ffmpeg")
        ffprobe_exe = bin_dir / ("ffprobe.exe" if os.name == 'nt' else "ffprobe")

        if ffmpeg_exe.exists() and ffprobe_exe.exists():
            if progress_callback:
                progress_callback("✅ FFmpeg sudah siap di folder bin lokal.", 100)
            return True

        if os.name != 'nt':
            if progress_callback:
                progress_callback("⚠️ Harap install ffmpeg via package manager sistem Anda (apt/brew).", 100)
            return SystemChecker.is_ffmpeg_installed()

        # Reliable static FFmpeg zip download URL for Windows
        url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        zip_path = bin_dir / "ffmpeg_temp.zip"

        try:
            if progress_callback:
                progress_callback("Mengunduh FFmpeg engine (~40 MB)...", 10)

            def req_progress(block_num, block_size, total_size):
                if total_size > 0 and progress_callback:
                    percent = min(90, int(10 + (block_num * block_size / total_size) * 80))
                    mb_read = (block_num * block_size) / (1024 * 1024)
                    mb_total = total_size / (1024 * 1024)
                    progress_callback(f"Mengunduh FFmpeg... {mb_read:.1f} MB / {mb_total:.1f} MB ({percent}%)", percent)

            urllib.request.urlretrieve(url, zip_path, reporthook=req_progress)

            if progress_callback:
                progress_callback("Mengekstrak file FFmpeg...", 92)

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for member in zip_ref.namelist():
                    if member.endswith("ffmpeg.exe"):
                        with zip_ref.open(member) as source, open(ffmpeg_exe, "wb") as target:
                            shutil.copyfileobj(source, target)
                    elif member.endswith("ffprobe.exe"):
                        with zip_ref.open(member) as source, open(ffprobe_exe, "wb") as target:
                            shutil.copyfileobj(source, target)

            if zip_path.exists():
                zip_path.unlink()

            ensure_bin_path()
            if progress_callback:
                progress_callback("✅ Pemasangan FFmpeg Berhasil!", 100)
            return True

        except Exception as e:
            if progress_callback:
                progress_callback(f"❌ Gagal mengunduh FFmpeg otomatis: {e}", 0)
            return False

    @staticmethod
    def pull_ollama_model(model_name: str = "gemma2:2b", progress_callback=None) -> bool:
        """Pulls Ollama model via ollama CLI or HTTP API."""
        if not SystemChecker.is_ollama_installed() and not SystemChecker.is_ollama_running():
            if progress_callback:
                progress_callback("⚠️ Ollama belum terinstall. Mengunduh installer Ollama...", 10)
            try:
                installer_path = get_app_dir() / "OllamaSetup.exe"
                url = "https://ollama.com/download/OllamaSetup.exe"
                urllib.request.urlretrieve(url, installer_path)
                if progress_callback:
                    progress_callback("Menjalankan Installer Ollama...", 50)
                subprocess.Popen([str(installer_path)])
                if progress_callback:
                    progress_callback("Harap selesaikan wizard Ollama di Windows Anda.", 80)
            except Exception as e:
                if progress_callback:
                    progress_callback(f"Buka https://ollama.com/download untuk instalasi manual. ({e})", 0)
                return False

        if progress_callback:
            progress_callback(f"Mengunduh model AI lokal ({model_name})...", 30)

        try:
            proc = subprocess.Popen(["ollama", "pull", model_name], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            while True:
                line = proc.stdout.readline()
                if not line and proc.poll() is not None:
                    break
                if line and progress_callback:
                    clean_line = line.strip()
                    if clean_line:
                        progress_callback(f"Ollama: {clean_line}", 60)
            proc.wait()
            if proc.returncode == 0:
                if progress_callback:
                    progress_callback(f"✅ Model AI {model_name} berhasil diunduh!", 100)
                return True
        except Exception as e:
            if progress_callback:
                progress_callback(f"Gagal pull model: {e}", 0)
        return False
