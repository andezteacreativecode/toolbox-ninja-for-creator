import sys
import threading
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QFrame, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from gui.styles import Styles
from core.utils.system_checker import SystemChecker, ensure_bin_path

class SetupSignals(QObject):
    status_updated = pyqtSignal(str, int)
    setup_finished = pyqtSignal(bool)

class SetupWizardDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🥷 Clipper AI Desktop — Wizard Pengaturan Awal")
        self.setMinimumSize(540, 420)
        self.setStyleSheet(Styles.get_qss())
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self.signals = SetupSignals()
        self.signals.status_updated.connect(self._on_status_updated)
        self.signals.setup_finished.connect(self._on_setup_finished)

        self._init_ui()
        self._check_initial_status()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header Title
        title_lbl = QLabel("🎬 Pengaturan Komponen Pendukung")
        title_lbl.setObjectName("heading")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #ECE9F7;")
        layout.addWidget(title_lbl)

        desc_lbl = QLabel(
            "Selamat datang! Clipper AI Desktop membutuhkan beberapa komponen pendukung (FFmpeg & Model AI) "
            "agar dapat memotong video dan membuat subtitle secara otomatis."
        )
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("color: #A7A0C4; font-size: 13px;")
        layout.addWidget(desc_lbl)

        # Status Card Box
        card = QFrame()
        card.setObjectName("glass_panel")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(12)

        self.lbl_ffmpeg_status = QLabel("⚡ FFmpeg Engine: Memeriksa...")
        self.lbl_ffmpeg_status.setStyleSheet("color: #ECE9F7; font-weight: 600;")
        card_layout.addWidget(self.lbl_ffmpeg_status)

        self.lbl_ollama_status = QLabel("🤖 Ollama AI (gemma2:2b): Memeriksa...")
        self.lbl_ollama_status.setStyleSheet("color: #ECE9F7; font-weight: 600;")
        card_layout.addWidget(self.lbl_ollama_status)

        layout.addWidget(card)

        # Progress Section
        self.status_detail_lbl = QLabel("Siap untuk memulai pengunduhan komponen.")
        self.status_detail_lbl.setWordWrap(True)
        self.status_detail_lbl.setStyleSheet("color: #8B5CF6; font-size: 12px; font-weight: 600;")
        layout.addWidget(self.status_detail_lbl)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(12)
        layout.addWidget(self.progress_bar)

        layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_skip = QPushButton("Lewati & Buka Aplikasi")
        self.btn_skip.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_skip)

        self.btn_start = QPushButton("Unduh & Pasang Otomatis")
        self.btn_start.setObjectName("primary_btn")
        self.btn_start.clicked.connect(self.start_download_process)
        btn_layout.addWidget(self.btn_start)

        layout.addLayout(btn_layout)

    def _check_initial_status(self):
        ensure_bin_path()
        has_ffmpeg = SystemChecker.is_ffmpeg_installed()
        has_model = SystemChecker.has_ollama_model("gemma2:2b")

        if has_ffmpeg:
            self.lbl_ffmpeg_status.setText("✅ FFmpeg Engine: Terpasang & Siap")
        else:
            self.lbl_ffmpeg_status.setText("⚠️ FFmpeg Engine: Belum Ada (Akan Diunduh Otomatis)")

        if has_model:
            self.lbl_ollama_status.setText("✅ Ollama AI (gemma2:2b): Terpasang & Siap")
        else:
            self.lbl_ollama_status.setText("⚠️ Ollama AI (gemma2:2b): Belum Siap (Akan Diunduh Otomatis)")

        if has_ffmpeg and has_model:
            self.status_detail_lbl.setText("🎉 Semua komponen siap! Anda bisa langsung membuka aplikasi.")
            self.btn_start.setText("Buka Clipper AI Desktop")
            self.progress_bar.setValue(100)

    def start_download_process(self):
        has_ffmpeg = SystemChecker.is_ffmpeg_installed()
        has_model = SystemChecker.has_ollama_model("gemma2:2b")

        if has_ffmpeg and has_model:
            self.accept()
            return

        self.btn_start.setEnabled(False)
        self.btn_skip.setEnabled(False)

        def _worker():
            def cb(msg, pct):
                self.signals.status_updated.emit(msg, pct)

            success_ff = True
            if not SystemChecker.is_ffmpeg_installed():
                success_ff = SystemChecker.download_ffmpeg(progress_callback=cb)

            success_ai = True
            if not SystemChecker.has_ollama_model("gemma2:2b"):
                success_ai = SystemChecker.pull_ollama_model("gemma2:2b", progress_callback=cb)

            self.signals.setup_finished.emit(success_ff and success_ai)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_status_updated(self, msg: str, percent: int):
        self.status_detail_lbl.setText(msg)
        if percent >= 0:
            self.progress_bar.setValue(percent)

    def _on_setup_finished(self, success: bool):
        self._check_initial_status()
        self.btn_start.setEnabled(True)
        self.btn_skip.setEnabled(True)
        if success:
            self.status_detail_lbl.setText("🎉 Seluruh komponen berhasil dipasang! Klik tombol di bawah untuk melanjutkan.")
            self.btn_start.setText("Buka Clipper AI Desktop")
            QMessageBox.information(self, "Setup Selesai", "Seluruh komponen pendukung telah siap!")
        else:
            self.status_detail_lbl.setText("⚠️ Beberapa komponen memerlukan instalasi manual.")
