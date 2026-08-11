# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path

block_cipher = None

project_dir = os.path.abspath(os.path.dirname('__file__'))

added_files = [
    ('assets', 'assets'),
    ('config', 'config'),
]

hidden_imports = [
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'customtkinter',
    'httpx',
    'yt_dlp',
    'ffmpeg',
    'moviepy',
    'moviepy.editor',
    'cv2',
    'numpy',
    'scipy',
    'PIL',
    'requests',
    'faster_whisper',
    'mediapipe',
    'matplotlib',
    'matplotlib.pyplot',
    'fontTools',
    'torch',
    'torchaudio',
    'edge_tts',
    'gui',
    'gui.app',
    'gui.main_window_v2',
    'gui.styles',
    'gui.dialogs.setup_wizard_dialog',
    'core',
    'core.clipper',
    'core.downloader',
    'core.moment_detector',
    'core.subtitle_burner',
    'core.auto_reframe',
    'core.transcriber_v2',
    'core.tts_engine',
    'core.utils.system_checker',
]

a = Analysis(
    ['main.py'],
    pathex=[project_dir],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['IPython', 'notebook', 'nvidia', 'triton', 'caffe2', 'tensorboard'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ClipperAIDesktop',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI mode - no command prompt window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/ninja_logo.jpg',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ClipperAIDesktop',
)
