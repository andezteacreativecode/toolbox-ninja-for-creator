#!/bin/bash
# 🚀 Clipper AI Desktop — Installer & Setup Wizard Otomatis untuk User Awam

set -e

echo "=========================================================="
echo "🎬 Clipper AI Desktop — Setup Wizard Otomatis"
echo "=========================================================="
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 1. Cek & Install System Dependencies (Python3, venv, ffmpeg, curl, git)
echo "🔍 [1/5] Memeriksa dependensi sistem..."
if ! command -v python3 &> /dev/null; then
    echo "⚠️ Python 3 belum terinstall. Menginstall Python 3..."
    sudo apt update && sudo apt install -y python3 python3-venv python3-pip ffmpeg curl git
fi

if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️ FFmpeg belum terinstall. Menginstall FFmpeg..."
    sudo apt update && sudo apt install -y ffmpeg
fi

# 2. Cek & Install Ollama Otomatis
echo "🦙 [2/5] Memeriksa Ollama (AI Lokal)..."
if ! command -v ollama &> /dev/null; then
    echo "⚡ Installing Ollama secara otomatis..."
    curl -fsSL https://ollama.com/install.sh | sh
else
    echo "✅ Ollama sudah terinstall."
fi

# 3. Jalankan Ollama Service & Download Model Rekomendasi
echo "🚀 [3/5] Memastikan Ollama Service berjalan & Mengunduh Model AI..."
if ! pgrep -x "ollama" > /dev/null; then
    echo "🔄 Menjalankan 'ollama serve' di background..."
    ollama serve > /dev/null 2>&1 &
    sleep 3
fi

echo "📦 Mengunduh model ringan rekomendasi (gemma2:2b)..."
ollama pull gemma2:2b || echo "⚠️ Gagal unduh gemma2:2b otomatis. Anda dapat mendownloadnya nanti dengan: ollama pull gemma2:2b"

# 4. Setup Python Virtual Environment & Install Requirements
echo "🐍 [4/5] Mengatur Virtual Environment Python & Install Library..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip setuptools
pip install -r requirements.txt

# 5. Buat Desktop Shortcut untuk Kemudahan User Awam
echo "🖥️ [5/5] Membuat Shortcut Aplikasi di Desktop & Menu..."
DESKTOP_FILE="$HOME/.local/share/applications/clipper-ai-desktop.desktop"
mkdir -p "$HOME/.local/share/applications"

cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Name=Clipper AI Desktop
Comment=Automated Short Video & Viral Moment Clipper
Exec=$SCRIPT_DIR/run.sh
Icon=$SCRIPT_DIR/assets/ninja_logo.jpg
Terminal=false
Type=Application
Categories=Utility;AudioVideo;
EOF

chmod +x "$DESKTOP_FILE"
chmod +x "$SCRIPT_DIR/run.sh"

echo ""
echo "=========================================================="
echo "🎉 Pemasangan Selesai 100%!"
echo "=========================================================="
echo "Anda dapat menjalankan aplikasi dengan:"
echo "1. Klik ganda ikon 'Clipper AI Desktop' di App Menu / Launcher"
echo "2. Atau jalankan perintah: ./run.sh"
echo "=========================================================="
