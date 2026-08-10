import os
import shutil
import subprocess
from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from gui.dialogs.ai_caption_dialog import AiCaptionDialog


class QtClipCardWidget(QFrame):
    def __init__(self, clip_info: dict, file_path: str = "", parent=None):
        super().__init__(parent)
        self.clip_info = clip_info
        self.file_path = file_path

        self.setStyleSheet("""
            QFrame#clip_card {
                background-color: #161226;
                border: 1px solid rgba(255,255,255,0.09);
                border-radius: 10px;
            }
            QFrame#clip_card:hover {
                border: 1px solid rgba(139,92,246,0.5);
                background-color: #1E1832;
            }
            QLabel {
                border: none;
                background: transparent;
            }
            QPushButton#btn_play {
                background-color: #8B5CF6;
                color: #140F24;
                font-weight: bold;
                border-radius: 6px;
                padding: 5px 14px;
                font-size: 12px;
                border: none;
            }
            QPushButton#btn_play:hover {
                background-color: #A78BFA;
            }
        """)
        self.setObjectName("clip_card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # ── Title & Score row ─────────────────────────────────────────────
        top_row = QHBoxLayout()

        title_text = clip_info.get('title', 'Clip')
        title_lbl = QLabel(title_text)
        title_lbl.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #ECE9F7;")
        title_lbl.setWordWrap(True)
        top_row.addWidget(title_lbl, stretch=1)

        score = clip_info.get('score', 85.0)
        try:
            score_val = float(score)
        except (TypeError, ValueError):
            score_val = 85.0

        score_lbl = QLabel(f"Score {score_val:.0f}/100")
        score_lbl.setStyleSheet(
            "font-size: 12px; font-weight: bold; color: #8B5CF6;"
            " background-color: #241D3E; border-radius: 10px; padding: 2px 8px;")
        score_lbl.setToolTip("Virality Score (0-100)")
        top_row.addWidget(score_lbl)

        layout.addLayout(top_row)

        # ── Description / Reason ──────────────────────────────────────────
        description = clip_info.get('description', clip_info.get('reason', ''))
        if description:
            desc_lbl = QLabel(description)
            desc_lbl.setStyleSheet(
                "font-size: 12px; color: #A7A0C4; line-height: 1.4;")
            desc_lbl.setWordWrap(True)
            layout.addWidget(desc_lbl)

        # ── Timestamp info ────────────────────────────────────────────────
        start = clip_info.get('start', 0)
        end = clip_info.get('end', 30)
        dur = clip_info.get('duration', end - start)
        start_m, start_s = int(start // 60), int(start % 60)
        end_m, end_s = int(end // 60), int(end % 60)

        time_row = QHBoxLayout()
        time_lbl = QLabel(
            f"{start_m:02d}:{start_s:02d} \u2192 {end_m:02d}:{end_s:02d}  |  {dur:.1f}s")
        time_lbl.setStyleSheet("font-size: 11px; color: #A7A0C4;")
        time_row.addWidget(time_lbl)
        time_row.addStretch()

        # File badge
        if self.file_path and os.path.exists(self.file_path):
            fname = os.path.basename(self.file_path)
            file_badge = QLabel(fname)
            file_badge.setStyleSheet(
                "font-size: 10px; color: #6C6690; "
                "background-color: rgba(108,102,144,0.15); "
                "border-radius: 4px; padding: 2px 6px;")
            file_badge.setToolTip(self.file_path)
            time_row.addWidget(file_badge)

        layout.addLayout(time_row)

        # ── Action Buttons ────────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        if self.file_path and os.path.exists(self.file_path):
            play_btn = QPushButton("Play Video")
            play_btn.setObjectName("btn_play")
            play_btn.setFixedHeight(30)
            play_btn.clicked.connect(self.open_video)
            btn_layout.addWidget(play_btn)

        ai_caption_btn = QPushButton("Title & Caption")
        ai_caption_btn.setFixedHeight(30)
        ai_caption_btn.setStyleSheet("""
            QPushButton {
                background-color: #241D3E;
                color: #8B5CF6;
                border: 1px solid rgba(139,92,246,0.4);
                border-radius: 6px;
                padding: 5px 12px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8B5CF6;
                color: #140F24;
            }
        """)
        ai_caption_btn.clicked.connect(self.open_ai_caption_dialog)
        btn_layout.addWidget(ai_caption_btn)

        if self.file_path and os.path.exists(self.file_path):
            download_btn = QPushButton("Download")
            download_btn.setFixedHeight(30)
            download_btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #A7A0C4;
                    border: 1px solid rgba(255,255,255,0.1);
                    border-radius: 6px;
                    padding: 5px 14px;
                    font-size: 12px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #2A2247;
                    color: #ECE9F7;
                }
            """)
            download_btn.clicked.connect(self.download_video)
            btn_layout.addWidget(download_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def open_video(self):
        if self.file_path and os.path.exists(self.file_path):
            try:
                subprocess.Popen(["xdg-open", self.file_path])
            except Exception as e:
                print(f"Error opening video: {e}")

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
            "Save / Download Video Clip",
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
