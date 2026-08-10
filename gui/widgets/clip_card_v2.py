import os
import shutil
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from gui.dialogs.ai_caption_dialog import AiCaptionDialog

_ACCENT = "#8B5CF6"
_ACCENT_HOVER = "#A78BFA"
_ACCENT_SOFT = "#241D3E"
_ACCENT_TEXT = "#140F24"
_SURFACE = "#161226"
_INPUT = "#1E1832"
_HOVER = "#2A2247"
_BORDER = "rgba(255, 255, 255, 0.09)"
_TEXT = "#ECE9F7"
_MUTED = "#A7A0C4"
_FAINT = "#6C6690"

_GHOST_BTN = f"""
QPushButton {{
    background-color: transparent;
    color: {_MUTED};
    border: 1px solid {_BORDER};
    border-radius: 6px;
    padding: 5px 12px;
    font-size: 12px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: {_HOVER};
    color: {_TEXT};
}}
"""


class ClipCardV2Widget(QFrame):
    play_requested = pyqtSignal(str)

    def __init__(self, clip_info: dict, file_path: str = "", parent=None):
        super().__init__(parent)
        self.clip_info = clip_info
        self.file_path = file_path
        self.setObjectName("glass_panel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # Header: Title & Score badge
        header_layout = QHBoxLayout()
        title_lbl = QLabel(clip_info.get('title', 'Clip Highlight'))
        title_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {_TEXT};")
        title_lbl.setWordWrap(True)
        header_layout.addWidget(title_lbl, stretch=1)

        try:
            score = float(clip_info.get('score', 85.0))
        except (TypeError, ValueError):
            score = 85.0

        score_lbl = QLabel(f"Score {score:.0f}/100")
        score_lbl.setStyleSheet(
            f"font-size: 11px; font-weight: 700; color: {_ACCENT}; "
            f"background-color: {_ACCENT_SOFT}; border: none; border-radius: 10px; padding: 3px 8px;"
        )
        header_layout.addWidget(score_lbl)

        layout.addLayout(header_layout)

        # Time range & Duration
        start = clip_info.get('start', 0)
        end = clip_info.get('end', 30)
        dur = clip_info.get('duration', end - start)
        start_m, start_s = int(start // 60), int(start % 60)
        end_m, end_s = int(end // 60), int(end % 60)

        info_lbl = QLabel(
            f"{start_m:02d}:{start_s:02d} \u2013 {end_m:02d}:{end_s:02d}   |   {dur:.1f}s"
        )
        info_lbl.setStyleSheet(f"font-size: 11px; color: {_MUTED}; font-family: monospace;")
        layout.addWidget(info_lbl)

        # Reason
        reason = clip_info.get('reason', '')
        if reason:
            reason_lbl = QLabel(reason)
            reason_lbl.setStyleSheet(f"font-size: 12px; font-style: italic; color: {_MUTED};")
            reason_lbl.setWordWrap(True)
            layout.addWidget(reason_lbl)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        sys_play_btn = QPushButton("Preview")
        sys_play_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {_ACCENT};
                border: 1px solid rgba(139, 92, 246, 0.5);
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {_ACCENT_SOFT};
                border: 1px solid {_ACCENT};
            }}
        """)
        sys_play_btn.clicked.connect(self.open_video)
        btn_layout.addWidget(sys_play_btn)

        ai_caption_btn = QPushButton("Title & Caption")
        ai_caption_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {_ACCENT};
                color: {_ACCENT_TEXT};
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background-color: {_ACCENT_HOVER};
            }}
        """)
        ai_caption_btn.clicked.connect(self.open_ai_caption_dialog)
        btn_layout.addWidget(ai_caption_btn)

        download_btn = QPushButton("Download")
        download_btn.setStyleSheet(_GHOST_BTN)
        download_btn.clicked.connect(self.download_video)
        btn_layout.addWidget(download_btn)

        if not (self.file_path and os.path.exists(self.file_path)):
            sys_play_btn.setEnabled(False)
            download_btn.setEnabled(False)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def open_video(self):
        if self.file_path and os.path.exists(self.file_path):
            self.play_requested.emit(self.file_path)

    def open_ai_caption_dialog(self):
        dlg = AiCaptionDialog(self.clip_info, parent=self)
        dlg.exec()

    def download_video(self):
        if not (self.file_path and os.path.exists(self.file_path)):
            QMessageBox.warning(self, "Warning", "Video file not found!")
            return

        default_name = os.path.basename(self.file_path)
        home_downloads = os.path.expanduser("~/Downloads")
        default_path = os.path.join(home_downloads, default_name)

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Video Clip",
            default_path,
            "MP4 Video (*.mp4);;All Files (*)"
        )

        if save_path:
            try:
                shutil.copy2(self.file_path, save_path)
                QMessageBox.information(
                    self,
                    "Download Complete",
                    f"Video clip saved successfully to:\n{save_path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Download Error", f"Failed to save video: {e}")
