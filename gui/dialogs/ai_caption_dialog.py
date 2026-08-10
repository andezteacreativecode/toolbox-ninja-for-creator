import json
import httpx
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QFrame, QMessageBox, QApplication, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from config.settings import SettingsManager
from providers.provider_factory import ProviderFactory

_ACCENT = "#8B5CF6"
_ACCENT_HOVER = "#A78BFA"
_ACCENT_SOFT = "#241D3E"
_ACCENT_TEXT = "#140F24"
_BG = "#0F0C1C"
_SURFACE = "#161226"
_INPUT = "#1E1832"
_HOVER = "#2A2247"
_BORDER = "rgba(255, 255, 255, 0.09)"
_TEXT = "#ECE9F7"
_MUTED = "#A7A0C4"
_SUCCESS = "#8AC9A0"
_DANGER = "#E58A7E"


class CaptionFetchThread(QThread):
    done = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, ai_provider, clip_info: dict, topic: str = "", source_video_title: str = ""):
        super().__init__()
        self.ai_provider = ai_provider
        self.clip_info = clip_info
        self.topic = topic
        self.source_video_title = source_video_title

    def run(self):
        try:
            title = self.clip_info.get("title", "")
            text = self.clip_info.get("text", "")
            reason = self.clip_info.get("reason", "")

            # If provider has generate_caption method, use it
            if hasattr(self.ai_provider, "generate_caption"):
                res = self.ai_provider.generate_caption(
                    title, text, reason, topic=self.topic, source_video_title=self.source_video_title
                )
                if res and isinstance(res, dict) and "title" in res:
                    self.done.emit(res)
                    return

            topic_tag = f" #{self.topic.replace(' ', '')}" if self.topic else ""
            src_text = f" (from video '{self.source_video_title}')" if self.source_video_title else ""
            result = {
                "title": title,
                "description": f"{title}\n\n{reason}{src_text}\n\nFollow & share for more viral clips!\n\n#viral #fyp #trending #shorts #reels{topic_tag}"
            }
            self.done.emit(result)
        except Exception as e:
            self.error.emit(str(e))


DIALOG_STYLE = f"""
QDialog#caption_dialog {{
    background-color: {_BG};
    color: {_TEXT};
    font-family: 'Inter', 'Segoe UI', sans-serif;
}}
QLabel {{
    color: {_MUTED};
    background: transparent;
    border: none;
}}
QLineEdit, QComboBox {{
    background-color: {_INPUT};
    color: {_TEXT};
    border: 1px solid {_BORDER};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
    selection-background-color: {_ACCENT};
    selection-color: {_ACCENT_TEXT};
}}
QLineEdit:focus, QComboBox:focus {{
    border: 1px solid {_ACCENT};
    background-color: {_SURFACE};
}}
QComboBox QAbstractItemView {{
    background-color: {_INPUT};
    color: {_TEXT};
    selection-background-color: {_ACCENT};
    selection-color: {_ACCENT_TEXT};
    border: 1px solid {_BORDER};
    border-radius: 6px;
    padding: 4px;
    outline: none;
}}
QComboBox QAbstractItemView::item {{
    background-color: {_INPUT};
    color: {_TEXT};
    padding: 6px 12px;
    min-height: 24px;
}}
QTextEdit {{
    background-color: {_INPUT};
    color: {_TEXT};
    border: 1px solid {_BORDER};
    border-radius: 6px;
    padding: 10px 12px;
    font-size: 13px;
    line-height: 1.5;
    selection-background-color: {_ACCENT};
    selection-color: {_ACCENT_TEXT};
}}
QTextEdit:focus {{
    border: 1px solid {_ACCENT};
    background-color: {_SURFACE};
}}
QPushButton#btn_copy {{
    background-color: {_ACCENT_SOFT};
    color: {_ACCENT};
    border: 1px solid rgba(139, 92, 246, 0.4);
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 12px;
}}
QPushButton#btn_copy:hover {{
    background-color: {_ACCENT};
    color: {_ACCENT_TEXT};
}}
QPushButton#btn_gen_ai {{
    background-color: {_ACCENT};
    color: {_ACCENT_TEXT};
    border: none;
    border-radius: 7px;
    padding: 10px 18px;
    font-size: 13px;
    font-weight: 700;
}}
QPushButton#btn_gen_ai:hover {{
    background-color: {_ACCENT_HOVER};
}}
QPushButton#btn_copy_all {{
    background-color: {_INPUT};
    color: {_TEXT};
    border: 1px solid {_BORDER};
    border-radius: 7px;
    padding: 10px 18px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton#btn_copy_all:hover {{
    background-color: {_HOVER};
}}
QPushButton#btn_close {{
    background-color: {_INPUT};
    color: {_MUTED};
    border: 1px solid {_BORDER};
    border-radius: 7px;
    padding: 10px 16px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton#btn_close:hover {{
    background-color: {_HOVER};
    color: {_TEXT};
}}
"""


class AiCaptionDialog(QDialog):
    def __init__(self, clip_info: dict, settings_mgr: SettingsManager = None, parent=None):
        super().__init__(parent)
        self.clip_info = clip_info
        self.settings_mgr = settings_mgr or SettingsManager()
        self.setObjectName("caption_dialog")
        self.setWindowTitle("Title & Caption Generator")
        self.setMinimumSize(660, 640)
        self.setStyleSheet(DIALOG_STYLE)

        self._fetch_thread = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 16)
        layout.setSpacing(10)

        # ── Header Frame ──────────────────────────────────────────────────
        hdr_frame = QFrame()
        hdr_frame.setStyleSheet(
            f"QFrame {{ background-color: {_ACCENT_SOFT}; border: 1px solid rgba(139,92,246,0.3); border-radius: 10px; }}"
        )
        h_layout = QVBoxLayout(hdr_frame)
        h_layout.setContentsMargins(14, 12, 14, 12)
        h_layout.setSpacing(4)

        hdr_title = QLabel("Title & Caption Generator")
        hdr_title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {_ACCENT};")
        h_layout.addWidget(hdr_title)

        start = self.clip_info.get("start", 0)
        end = self.clip_info.get("end", 30)
        score = self.clip_info.get("score", 85)
        start_m, start_s = int(start // 60), int(start % 60)
        end_m, end_s = int(end // 60), int(end % 60)

        info_str = f"Clip moment: {start_m:02d}:{start_s:02d} - {end_m:02d}:{end_s:02d}   |   Virality Score: {score}/100"
        sub_lbl = QLabel(info_str)
        sub_lbl.setStyleSheet(f"font-size: 11px; color: {_MUTED};")
        h_layout.addWidget(sub_lbl)

        layout.addWidget(hdr_frame)

        # ── Source Video Title Section ────────────────────────────────────
        src_row = QVBoxLayout()
        src_row.setSpacing(4)

        src_lbl = QLabel("Original Video Title (source context):")
        src_lbl.setStyleSheet(f"font-weight: 600; font-size: 12px; color: {_MUTED};")
        src_row.addWidget(src_lbl)

        self.source_title_input = QLineEdit()
        init_src_title = self.clip_info.get("source_video_title", "")
        self.source_title_input.setText(init_src_title)
        self.source_title_input.setPlaceholderText("Original video title (e.g. Business Podcast...)")
        self.source_title_input.setFixedHeight(36)
        src_row.addWidget(self.source_title_input)

        layout.addLayout(src_row)

        # ── Section 1: Title Input ────────────────────────────────────────
        title_lbl = QLabel("Viral Clip Title (hook):")
        title_lbl.setStyleSheet(f"font-weight: 600; font-size: 13px; color: {_TEXT};")
        layout.addWidget(title_lbl)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        self.title_input = QLineEdit()
        init_title = self.clip_info.get("title", "Viral Highlight Moment")
        self.title_input.setText(init_title)
        self.title_input.setFixedHeight(38)
        title_row.addWidget(self.title_input, stretch=1)

        copy_title_btn = QPushButton("Copy Title")
        copy_title_btn.setObjectName("btn_copy")
        copy_title_btn.setFixedHeight(38)
        copy_title_btn.clicked.connect(self.copy_title)
        title_row.addWidget(copy_title_btn)

        layout.addLayout(title_row)

        # ── Section 2: Description / Caption Input ────────────────────────
        desc_lbl = QLabel("Social Media Caption (TikTok / Reels / Shorts):")
        desc_lbl.setStyleSheet(f"font-weight: 600; font-size: 13px; color: {_TEXT};")
        layout.addWidget(desc_lbl)

        self.desc_input = QTextEdit()
        self.desc_input.setMinimumHeight(150)

        # Build initial caption template
        init_desc = self.build_initial_caption()
        self.desc_input.setText(init_desc)
        layout.addWidget(self.desc_input)

        # ── Status / Toast Bar ────────────────────────────────────────────
        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet(f"font-size: 11px; color: {_SUCCESS}; font-weight: 600; padding: 0 2px;")
        self.status_lbl.setFixedHeight(18)
        layout.addWidget(self.status_lbl)

        # ── Bottom Action Buttons ──────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        gen_ai_btn = QPushButton("Generate Title & Caption")
        gen_ai_btn.setObjectName("btn_gen_ai")
        gen_ai_btn.setFixedHeight(40)
        gen_ai_btn.clicked.connect(self.generate_ai_caption)
        btn_row.addWidget(gen_ai_btn)

        copy_all_btn = QPushButton("Copy Full Caption")
        copy_all_btn.setObjectName("btn_copy_all")
        copy_all_btn.setFixedHeight(40)
        copy_all_btn.clicked.connect(self.copy_all)
        btn_row.addWidget(copy_all_btn)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("btn_close")
        close_btn.setFixedHeight(40)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

    def build_initial_caption(self) -> str:
        title = self.clip_info.get("title", "Viral Moment Highlight")
        desc = self.clip_info.get("description", self.clip_info.get("reason", "Best viral highlight moment!"))
        clip_text = self.clip_info.get("text", "")
        src_title = self.clip_info.get("source_video_title", "")

        lines = [
            title,
            "",
            desc,
        ]

        if src_title:
            lines.extend([
                "",
                f"Source video: {src_title}"
            ])

        if clip_text:
            lines.extend([
                "",
                f"\"{clip_text[:150]}...\"" if len(clip_text) > 150 else f"\"{clip_text}\""
            ])

        lines.extend([
            "",
            "Follow & share for more viral clips!",
            "",
            "#viral #fyp #trending #shorts #reels #foryou #highlight #clipper"
        ])
        return "\n".join(lines)

    def copy_title(self):
        txt = self.title_input.text().strip()
        if txt:
            QApplication.clipboard().setText(txt)
            self._show_toast("Title copied to clipboard!")

    def copy_all(self):
        title = self.title_input.text().strip()
        desc = self.desc_input.toPlainText().strip()

        full_text = f"{title}\n\n{desc}" if title not in desc else desc
        QApplication.clipboard().setText(full_text)
        self._show_toast("Full title & caption copied to clipboard!")

    def _show_toast(self, msg: str, color: str = _SUCCESS):
        self.status_lbl.setText(msg)
        self.status_lbl.setStyleSheet(f"font-size: 11px; color: {color}; font-weight: 600; padding: 0 2px;")

    def generate_ai_caption(self):
        active_key = self.settings_mgr.data.get("active_provider", "ollama")
        prov_cfg = self.settings_mgr.get_active_provider_config()
        src_title = self.source_title_input.text().strip()

        try:
            ai_provider = ProviderFactory.get_provider(active_key, prov_cfg)
        except Exception as e:
            self._show_toast(f"AI provider error: {e}", _DANGER)
            return

        self._show_toast(f"Generating new title & caption for '{src_title[:30]}...'...", _ACCENT)
        self._fetch_thread = CaptionFetchThread(
            ai_provider, self.clip_info, source_video_title=src_title
        )
        self._fetch_thread.done.connect(self._on_ai_caption_done)
        self._fetch_thread.error.connect(lambda err: self._show_toast(f"AI error: {err}", _DANGER))
        self._fetch_thread.start()

    def _on_ai_caption_done(self, res: dict):
        new_title = res.get("title", "")
        new_desc = res.get("description", "")

        if new_title:
            self.title_input.setText(new_title)
        if new_desc:
            self.desc_input.setText(new_desc)

        self._show_toast("New title & caption generated.", _SUCCESS)
