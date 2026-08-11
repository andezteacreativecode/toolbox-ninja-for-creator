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
if ! command -v python3 &> /dev/null || ! command -v git &> /dev/null; then
    echo "⚠️ Memasang dependensi dasar (Python 3, Git, FFmpeg, Curl)..."
    sudo apt update && sudo apt install -y python3 python3-venv python3-pip ffmpeg curl git unzip
fi

if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️ FFmpeg belum terinstall. Menginstall FFmpeg..."
    sudo apt update && sudo apt install -y ffmpeg
fi

# 1.5. Cek & Unduh Kode Proyek jika setup.sh dijalankan terpisah (standalone)
if [ ! -f "requirements.txt" ]; then
    echo "📦 Kode aplikasi Clipper AI belum ada di folder ini."
    echo "📥 Mengunduh proyek Clipper AI Desktop dari GitHub..."
    if command -v git &> /dev/null; then
        git clone https://github.com/andezteacreativecode/toolbox-ninja-for-creator.git clipper_desktop
        cd clipper_desktop
        SCRIPT_DIR="$(pwd)"
    else
        curl -sL https://github.com/andezteacreativecode/toolbox-ninja-for-creator/archive/refs/heads/main.zip -o clipper.zip
        unzip -q clipper.zip
        cd toolbox-ninja-for-creator-main
        SCRIPT_DIR="$(pwd)"
    fi
    echo "✅ Berhasil mengunduh kode proyek ke: $SCRIPT_DIR"
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
echo "2. Atau jalankan perintah: cd $SCRIPT_DIR && ./run.sh"
echo "=========================================================="
