#!/bin/bash
# 🚀 Build macOS App Bundle & .dmg Installer for Clipper AI Desktop

set -e

echo "=========================================================="
echo "🎬 Building Clipper AI Desktop for macOS (.app & .dmg)"
echo "=========================================================="

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

pip install --upgrade pyinstaller

echo "📦 Mengompilasi kode Python menjadi Aplikasi macOS (.app)..."
pyinstaller --noconfirm --onedir --windowed \
    --name "Clipper AI Desktop" \
    --icon "assets/ninja_logo.jpg" \
    main.py

echo "🎉 Build selesai! Hasil aplikasi berada di folder: dist/Clipper AI Desktop.app"
