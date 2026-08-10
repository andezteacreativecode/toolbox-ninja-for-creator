import os
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSpinBox, QComboBox, QProgressBar, QScrollArea, QFileDialog,
    QMessageBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from config.settings import SettingsManager
from providers.provider_factory import ProviderFactory
from core.downloader import VideoDownloader
from core.transcriber import VideoTranscriber
from core.moment_detector import MomentDetector
from core.clipper import VideoClipper
from gui.qt_settings_dialog import QtSettingsDialog
from gui.qt_clip_card import QtClipCardWidget


class PipelineThread(QThread):
    progress_signal = pyqtSignal(str, float)
    finished_signal = pyqtSignal(list, list)
    error_signal = pyqtSignal(str)

    def __init__(self, source: str, num_clips: int, duration: int, aspect_ratio: str, settings_mgr: SettingsManager, topic: str = ""):
        super().__init__()
        self.source = source
        self.num_clips = num_clips
        self.duration = duration
        self.aspect_ratio = aspect_ratio
        self.settings_mgr = settings_mgr
        self.topic = topic

    def run(self):
        try:
            self.progress_signal.emit("Memulai penyiapan video...", 0.05)
            downloader = VideoDownloader()
            video_path, source_video_title = downloader.prepare_video(
                self.source,
                progress_callback=lambda msg: self.progress_signal.emit(msg, 0.15)
            )

            self.progress_signal.emit("Mengekstrak audio dan transkripsi dengan Whisper...", 0.25)
            transcriber = VideoTranscriber()
            segments = transcriber.transcribe(
                video_path,
                model_size="base",
                progress_callback=lambda msg: self.progress_signal.emit(msg, 0.40)
            )

            self.progress_signal.emit("Menghubungi AI Provider untuk mendeteksi momen viral...", 0.55)
            active_key = self.settings_mgr.data.get("active_provider", "ollama")
            prov_cfg = self.settings_mgr.get_active_provider_config()
            ai_provider = ProviderFactory.get_provider(active_key, prov_cfg)

            detector = MomentDetector(ai_provider)
            detected_clips = detector.detect_viral_moments(
                video_path=video_path,
                segments=segments,
                num_clips=self.num_clips,
                target_duration=self.duration,
                topic=self.topic,
                source_video_title=source_video_title,
                progress_callback=lambda msg: self.progress_signal.emit(msg, 0.70)
            )

            self.progress_signal.emit("Memotong dan memformat klip video...", 0.85)
            out_dir = self.settings_mgr.data['clip_settings'].get('output_dir', 'output_clips')
            clipper = VideoClipper(output_dir=out_dir)

            output_files = clipper.process_all_clips(
                video_path=video_path,
                clips=detected_clips,
                aspect_ratio=self.aspect_ratio,
                progress_callback=lambda msg: self.progress_signal.emit(msg, 0.90)
            )

            self.progress_signal.emit(f"🎉 Selesai! {len(output_files)} video klip berhasil dibuat.", 1.0)
            self.finished_signal.emit(detected_clips, output_files)

        except Exception as e:
            self.error_signal.emit(str(e))


MAIN_STYLE = """
QMainWindow {
    background-color: #0a0a14;
    color: #e2e8f0;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}
QWidget {
    background-color: #0a0a14;
    color: #e2e8f0;
    font-family: 'Inter', 'Segoe UI', sans-serif;
}
QFrame#card {
    background-color: #11111f;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
}
QLabel {
    color: #cbd5e1;
    background: transparent;
    border: none;
}
QLineEdit {
    background-color: #1a1a2e;
    color: #e2e8f0;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: #8B5CF6;
}
QLineEdit:focus {
    border: 1px solid #8B5CF6;
    background-color: #1e1e38;
}
QLineEdit::placeholder {
    color: #475569;
}
QSpinBox {
    background-color: #1a1a2e;
    color: #e2e8f0;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 7px 10px;
    font-size: 13px;
}
QSpinBox:focus {
    border: 1px solid #8B5CF6;
}
QSpinBox::up-button, QSpinBox::down-button {
    background-color: #252540;
    border: none;
    width: 20px;
}
QSpinBox::up-arrow { border-left: 4px solid transparent; border-right: 4px solid transparent; border-bottom: 6px solid #8B5CF6; }
QSpinBox::down-arrow { border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 6px solid #8B5CF6; }
QComboBox {
    background-color: #1a1a2e;
    color: #e2e8f0;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 7px 12px;
    font-size: 13px;
}
QComboBox:focus {
    border: 1px solid #8B5CF6;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: right center;
    width: 24px;
    border-left: 1px solid rgba(255,255,255,0.07);
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
    background-color: #252540;
}
QComboBox QAbstractItemView {
    background-color: #1a1a2e;
    color: #e2e8f0;
    selection-background-color: #8B5CF6;
    selection-color: #ffffff;
    border: 1px solid rgba(124,58,237,0.4);
    border-radius: 6px;
    padding: 4px;
    outline: none;
}
QComboBox QAbstractItemView::item {
    padding: 6px 12px;
    min-height: 22px;
}
QComboBox QAbstractItemView::item:hover {
    background-color: rgba(124,58,237,0.3);
    color: #ffffff;
}
QPushButton#btn_primary {
    background-color: #8B5CF6;
    color: white;
    font-size: 14px;
    font-weight: bold;
    border-radius: 10px;
    padding: 12px;
    border: none;
}
QPushButton#btn_primary:hover {
    background-color: #6D28D9;
}
QPushButton#btn_primary:disabled {
    background-color: #2d2d4e;
    color: #475569;
}
QPushButton#btn_secondary {
    background-color: #1a1a2e;
    color: #94a3b8;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 7px 14px;
    font-size: 12px;
    font-weight: 600;
}
QPushButton#btn_secondary:hover {
    background-color: #252540;
    color: #e2e8f0;
    border: 1px solid rgba(124,58,237,0.4);
}
QProgressBar {
    border: none;
    background-color: #1a1a2e;
    border-radius: 6px;
    height: 8px;
    text-align: center;
    font-size: 0px;
}
QProgressBar::chunk {
    background-color: #8B5CF6;
    border-radius: 6px;
}
QScrollArea {
    border: none;
    background-color: transparent;
}
QScrollBar:vertical {
    border: none;
    background: #11111f;
    width: 7px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: rgba(124,58,237,0.4);
    min-height: 20px;
    border-radius: 3px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
"""


class QtClipperMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Toolbox Ninja AI Desktop")
        self.resize(940, 740)
        self.setMinimumSize(760, 560)
        self.settings_mgr = SettingsManager()
        self.setStyleSheet(MAIN_STYLE)

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        # ── Header ──────────────────────────────────────────────────────────
        header_frame = QFrame()
        header_frame.setObjectName("card")
        header_frame.setMaximumHeight(60)
        h_inner = QHBoxLayout(header_frame)
        h_inner.setContentsMargins(16, 0, 16, 0)

        title_lbl = QLabel("🥷  Toolbox Ninja AI — 🎬 Clipper AI")
        title_lbl.setStyleSheet(
            "font-size: 18px; font-weight: 800; color: #e2e8f0; letter-spacing: -0.5px;")
        h_inner.addWidget(title_lbl)

        h_inner.addStretch()

        self.badge_lbl = QLabel("●  Ollama")
        self.badge_lbl.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #8B5CF6; "
            "background-color: rgba(124,58,237,0.15); "
            "border: 1px solid rgba(124,58,237,0.35); "
            "padding: 4px 12px; border-radius: 20px;")
        h_inner.addWidget(self.badge_lbl)

        settings_btn = QPushButton("⚙  Settings")
        settings_btn.setObjectName("btn_secondary")
        settings_btn.clicked.connect(self.open_settings)
        h_inner.addWidget(settings_btn)

        main_layout.addWidget(header_frame)

        # ── Source Input ─────────────────────────────────────────────────────
        source_card = QFrame()
        source_card.setObjectName("card")
        s_layout = QVBoxLayout(source_card)
        s_layout.setContentsMargins(16, 14, 16, 14)
        s_layout.setSpacing(8)

        src_title = QLabel("Source Video")
        src_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #94a3b8; letter-spacing: 0.5px;")
        s_layout.addWidget(src_title)

        src_row = QHBoxLayout()
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText(
            "Select video file (.mp4, .mkv, .mov) or paste YouTube / TikTok URL...")
        self.source_input.setFixedHeight(40)
        src_row.addWidget(self.source_input)

        browse_btn = QPushButton("📂  Browse")
        browse_btn.setObjectName("btn_secondary")
        browse_btn.setFixedHeight(40)
        browse_btn.clicked.connect(self.browse_file)
        src_row.addWidget(browse_btn)

        s_layout.addLayout(src_row)
        main_layout.addWidget(source_card)

        # ── Config Options ───────────────────────────────────────────────────
        opts_card = QFrame()
        opts_card.setObjectName("card")
        opts_layout = QVBoxLayout(opts_card)
        opts_layout.setContentsMargins(16, 14, 16, 14)
        opts_layout.setSpacing(8)

        cfg_title = QLabel("Clip Configuration")
        cfg_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #94a3b8; letter-spacing: 0.5px;")
        opts_layout.addWidget(cfg_title)

        opts_row = QHBoxLayout()
        opts_row.setSpacing(16)

        # Clip count
        clips_col = QVBoxLayout()
        clips_col.setSpacing(4)
        clips_lbl = QLabel("Clip Count")
        clips_lbl.setStyleSheet("font-size: 11px; color: #64748b; font-weight: 600;")
        clips_col.addWidget(clips_lbl)
        self.num_clips_spin = QSpinBox()
        self.num_clips_spin.setRange(1, 50)
        self.num_clips_spin.setValue(self.settings_mgr.data['clip_settings'].get('num_clips', 3))
        self.num_clips_spin.setFixedHeight(36)
        clips_col.addWidget(self.num_clips_spin)
        opts_row.addLayout(clips_col)

        # Duration
        dur_col = QVBoxLayout()
        dur_col.setSpacing(4)
        dur_lbl = QLabel("Duration (sec)")
        dur_lbl.setStyleSheet("font-size: 11px; color: #64748b; font-weight: 600;")
        dur_col.addWidget(dur_lbl)
        self.dur_spin = QSpinBox()
        self.dur_spin.setRange(5, 300)
        self.dur_spin.setValue(self.settings_mgr.data['clip_settings'].get('target_duration', 30))
        self.dur_spin.setFixedHeight(36)
        dur_col.addWidget(self.dur_spin)
        opts_row.addLayout(dur_col)

        # Aspect ratio
        ratio_col = QVBoxLayout()
        ratio_col.setSpacing(4)
        ratio_lbl = QLabel("Aspect Ratio")
        ratio_lbl.setStyleSheet("font-size: 11px; color: #64748b; font-weight: 600;")
        ratio_col.addWidget(ratio_lbl)
        self.ratio_combo = QComboBox()
        self.ratio_combo.addItems(["9:16", "1:1", "original"])
        cur_r = self.settings_mgr.data['clip_settings'].get('aspect_ratio', '9:16')
        if "1:1" in cur_r:
            self.ratio_combo.setCurrentIndex(1)
        elif "original" in cur_r:
            self.ratio_combo.setCurrentIndex(2)
        self.ratio_combo.setFixedHeight(36)
        ratio_col.addWidget(self.ratio_combo)
        opts_row.addLayout(ratio_col)

        # Topik / Niche
        topic_col = QVBoxLayout()
        topic_col.setSpacing(4)
        topic_lbl = QLabel("🎯 Niche / Topic (Optional)")
        topic_lbl.setStyleSheet("font-size: 11px; color: #8B5CF6; font-weight: 600;")
        topic_col.addWidget(topic_lbl)
        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("Education, Comedy, Motivation...")
        self.topic_input.setFixedHeight(36)
        topic_col.addWidget(self.topic_input)
        opts_row.addLayout(topic_col, stretch=1)

        opts_layout.addLayout(opts_row)
        main_layout.addWidget(opts_card)

        # ── Process Button ───────────────────────────────────────────────────
        self.process_btn = QPushButton("🚀  Process & Find Viral Moments")
        self.process_btn.setObjectName("btn_primary")
        self.process_btn.setFixedHeight(48)
        self.process_btn.clicked.connect(self.start_processing)
        main_layout.addWidget(self.process_btn)

        # ── Progress ─────────────────────────────────────────────────────────
        prog_card = QFrame()
        prog_card.setObjectName("card")
        p_layout = QVBoxLayout(prog_card)
        p_layout.setContentsMargins(16, 12, 16, 12)
        p_layout.setSpacing(6)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(8)
        p_layout.addWidget(self.progress_bar)

        self.status_lbl = QLabel("Ready to process video.")
        self.status_lbl.setStyleSheet("font-size: 12px; color: #475569;")
        p_layout.addWidget(self.status_lbl)

        main_layout.addWidget(prog_card)

        # ── Results ───────────────────────────────────────────────────────────
        results_hdr = QLabel("Generated Clips")
        results_hdr.setStyleSheet(
            "font-size: 13px; font-weight: 700; color: #94a3b8; "
            "letter-spacing: 0.5px; padding-left: 2px;")
        main_layout.addWidget(results_hdr)

        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)

        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 4, 0)
        self.scroll_layout.setSpacing(8)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.results_scroll.setWidget(self.scroll_content)

        main_layout.addWidget(self.results_scroll)

        self.update_provider_badge()

    def update_provider_badge(self):
        active = self.settings_mgr.data.get("active_provider", "ollama")
        label = "Ollama" if active == "ollama" else "9router / OpenRouter"
        self.badge_lbl.setText(f"●  {label}")

    def open_settings(self):
        dialog = QtSettingsDialog(self.settings_mgr, self)
        if dialog.exec():
            self.update_provider_badge()

    def browse_file(self):
        fname, _ = QFileDialog.getOpenFileName(
            self, "Select Input Video File", "",
            "Video Files (*.mp4 *.mkv *.mov *.avi *.webm);;All Files (*)"
        )
        if fname:
            self.source_input.setText(fname)

    def start_processing(self):
        source = self.source_input.text().strip()
        if not source:
            QMessageBox.warning(self, "Warning",
                                "Please select a video file or paste a video URL first!")
            return

        for i in reversed(range(self.scroll_layout.count())):
            w = self.scroll_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        self.process_btn.setEnabled(False)
        self.process_btn.setText("⏳  Processing Video...")

        self.thread = PipelineThread(
            source=source,
            num_clips=self.num_clips_spin.value(),
            duration=self.dur_spin.value(),
            aspect_ratio=self.ratio_combo.currentText(),
            settings_mgr=self.settings_mgr,
            topic=self.topic_input.text().strip()
        )
        self.thread.progress_signal.connect(self.on_progress)
        self.thread.finished_signal.connect(self.on_finished)
        self.thread.error_signal.connect(self.on_error)
        self.thread.start()

    def on_progress(self, msg: str, val: float):
        self.status_lbl.setText(msg)
        self.status_lbl.setStyleSheet("font-size: 12px; color: #8B5CF6;")
        self.progress_bar.setValue(int(val * 100))

    def on_finished(self, clips: list, output_files: list):
        self.process_btn.setEnabled(True)
        self.process_btn.setText("🚀  Process & Find Viral Moments")
        self.status_lbl.setText(f"🎉 Done! Successfully created {len(output_files)} video clips.")
        self.status_lbl.setStyleSheet("font-size: 12px; color: #4ade80;")
        self.progress_bar.setValue(100)

        for i, clip in enumerate(clips):
            file_path = output_files[i] if i < len(output_files) else ""
            card = QtClipCardWidget(clip_info=clip, file_path=file_path)
            self.scroll_layout.addWidget(card)

    def on_error(self, err_msg: str):
        self.process_btn.setEnabled(True)
        self.process_btn.setText("🚀  Process & Find Viral Moments")
        self.status_lbl.setText(f"❌ Error: {err_msg}")
        self.status_lbl.setStyleSheet("font-size: 12px; color: #f87171;")
        QMessageBox.critical(self, "Pipeline Error", err_msg)
