import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QSplitter, QScrollArea, QFrame, QPushButton, QProgressBar, QMessageBox, QTabWidget, QStackedWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl, QRectF
from PyQt6.QtGui import QDesktopServices, QPixmap, QPainter, QPainterPath, QPen, QColor


def make_circular_pixmap(pixmap: QPixmap, size: int = 180, border_color: str = "#8B5CF6", border_width: float = 4.0) -> QPixmap:
    target = QPixmap(size, size)
    target.fill(Qt.GlobalColor.transparent)

    painter = QPainter(target)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    margin = border_width / 2.0
    rect = QRectF(margin, margin, size - border_width, size - border_width)

    path = QPainterPath()
    path.addEllipse(rect)

    painter.save()
    painter.setClipPath(path)

    scaled_pixmap = pixmap.scaled(
        int(rect.width()),
        int(rect.height()),
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation
    )

    x = int(rect.x() + (rect.width() - scaled_pixmap.width()) / 2.0)
    y = int(rect.y() + (rect.height() - scaled_pixmap.height()) / 2.0)
    painter.drawPixmap(x, y, scaled_pixmap)
    painter.restore()

    if border_color and border_width > 0:
        pen = QPen(QColor(border_color))
        pen.setWidthF(border_width)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(rect)

    painter.end()
    return target


from config.settings import SettingsManager
from gui.panels.input_panel import InputPanel
from gui.panels.reference_panel import ReferencePanel
from gui.panels.voiceover_panel import VoiceoverWorkspaceWidget
from gui.panels.thumbnail_panel import ThumbnailWorkspaceWidget
from gui.widgets.video_player import VideoPlayerWidget
from gui.widgets.waveform_widget import WaveformWidget
from gui.dialogs.subtitle_settings import SubtitleSettingsDialog
from gui.widgets.clip_card_v2 import ClipCardV2Widget
from gui.qt_settings_dialog import QtSettingsDialog

from core.downloader import VideoDownloader
from core.transcriber_v2 import FasterWhisperTranscriber
from core.moment_detector import MomentDetector
from core.clipper import VideoClipper
from core.waveform_extractor import WaveformExtractor
from providers.provider_factory import ProviderFactory

_BG = "#0F0C1C"
_SURFACE = "#161226"
_INPUT = "#1E1832"
_HOVER = "#2A2247"
_BORDER = "rgba(255, 255, 255, 0.09)"
_ACCENT = "#8B5CF6"
_ACCENT_HOVER = "#A78BFA"
_ACCENT_SOFT = "#241D3E"
_ACCENT_TEXT = "#140F24"
_SUCCESS = "#8AC9A0"
_TEXT = "#ECE9F7"
_MUTED = "#A7A0C4"
_FAINT = "#6C6690"

_GHOST_BTN = f"""
QPushButton {{
    background-color: transparent;
    color: {_MUTED};
    border: 1px solid {_BORDER};
    border-radius: 7px;
    padding: 6px 14px;
    font-weight: 600;
}}
QPushButton:hover {{
    background-color: {_HOVER};
    color: {_TEXT};
    border: 1px solid rgba(139, 92, 246, 0.5);
}}
"""


class DonateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Support the Project")
        self.setFixedSize(460, 250)
        self.setStyleSheet(f"background-color: {_BG}; color: {_TEXT};")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        lbl = QLabel(
            "<h3 style='margin:0;'>Support Our Work</h3>"
            "<p>If <b>Toolbox Ninja</b> is helpful to you and you want to support its ongoing "
            "development, consider making a donation. Every contribution is deeply appreciated.</p>"
        )
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl, stretch=1)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        paypal_btn = QPushButton("PayPal (Global)")
        paypal_btn.setStyleSheet(_GHOST_BTN)
        paypal_btn.setMinimumHeight(40)
        paypal_btn.clicked.connect(self._open_paypal)
        btn_layout.addWidget(paypal_btn)

        dana_btn = QPushButton("DANA (Indonesia)")
        dana_btn.setStyleSheet(_GHOST_BTN)
        dana_btn.setMinimumHeight(40)
        dana_btn.clicked.connect(self._open_dana)
        btn_layout.addWidget(dana_btn)

        layout.addLayout(btn_layout)

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(_GHOST_BTN)
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)

    def _open_paypal(self):
        QDesktopServices.openUrl(QUrl("https://paypal.me/andeztea"))
        self.accept()

    def _open_dana(self):
        QDesktopServices.openUrl(QUrl("https://link.dana.id/minta?full_url=https://qr.dana.id/v1/281012012019072473369602"))
        self.accept()


class PipelineThread(QThread):
    progress_signal = pyqtSignal(str, float)
    finished_signal = pyqtSignal(list, list)
    error_signal = pyqtSignal(str)

    def __init__(self, source: str, num_clips: int, duration: int, aspect_ratio: str, settings_mgr: SettingsManager, subtitle_settings: dict, topic: str = ""):
        super().__init__()
        self.source = source
        self.num_clips = num_clips
        self.duration = duration
        self.aspect_ratio = aspect_ratio
        self.settings_mgr = settings_mgr
        self.subtitle_settings = subtitle_settings
        self.topic = topic

    def run(self):
        try:
            self.progress_signal.emit("Preparing video...", 0.05)
            downloader = VideoDownloader()
            video_path, source_video_title = downloader.prepare_video(
                self.source,
                progress_callback=lambda msg: self.progress_signal.emit(msg, 0.15)
            )

            self.progress_signal.emit("Extracting audio and transcribing...", 0.25)
            transcriber = FasterWhisperTranscriber()
            lang_setting = self.subtitle_settings.get("language", "auto") if self.subtitle_settings else "auto"
            target_lang = None if lang_setting == "auto" else lang_setting
            task_setting = "translate" if lang_setting == "en" else "transcribe"

            segments = transcriber.transcribe(
                video_path,
                model_size="base",
                language=target_lang,
                task=task_setting,
                progress_callback=lambda msg: self.progress_signal.emit(msg, 0.40)
            )

            self.progress_signal.emit("Contacting AI provider...", 0.55)
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

            self.progress_signal.emit("Cropping and formatting video clips...", 0.85)
            out_dir = self.settings_mgr.data['clip_settings'].get('output_dir', 'output_clips')
            clipper = VideoClipper(output_dir=out_dir)

            output_files = clipper.process_all_clips(
                video_path=video_path,
                clips=detected_clips,
                aspect_ratio=self.aspect_ratio,
                subtitle_settings=self.subtitle_settings,
                progress_callback=lambda msg: self.progress_signal.emit(msg, 0.90)
            )

            self.progress_signal.emit(f"Done. Successfully created {len(output_files)} video clips.", 1.0)
            self.finished_signal.emit(detected_clips, output_files)

        except Exception as e:
            self.error_signal.emit(str(e))


class ToolboxDashboardWidget(QWidget):
    launch_clipper = pyqtSignal()
    launch_voiceover = pyqtSignal()
    launch_thumbnails = pyqtSignal()
    open_settings_requested = pyqtSignal()
    show_about_requested = pyqtSignal()
    show_donate_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"background: {_BG}; border: none;")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(32, 24, 32, 28)
        content_layout.setSpacing(16)

        # ── Top Action Bar ─────────────────────────────────────────────────
        top_bar = QHBoxLayout()
        top_bar.addStretch()

        settings_btn = QPushButton("Settings")
        settings_btn.setStyleSheet(_GHOST_BTN)
        settings_btn.clicked.connect(self.open_settings_requested.emit)
        top_bar.addWidget(settings_btn)

        about_btn = QPushButton("About")
        about_btn.setStyleSheet(_GHOST_BTN)
        about_btn.clicked.connect(self.show_about_requested.emit)
        top_bar.addWidget(about_btn)

        donate_btn = QPushButton("Donate")
        donate_btn.setStyleSheet(_GHOST_BTN)
        donate_btn.clicked.connect(self.show_donate_requested.emit)
        top_bar.addWidget(donate_btn)

        content_layout.addLayout(top_bar)

        # ── Centered Hero: Ninja Mascot + Wordmark ────────────────────────
        hero_col = QVBoxLayout()
        hero_col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_col.setSpacing(8)

        img_lbl = QLabel()
        img_lbl.setFixedSize(150, 150)
        img_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "ninja_logo.jpg")
        if os.path.exists(img_path):
            pixmap = QPixmap(img_path)
            img_lbl.setPixmap(make_circular_pixmap(pixmap, size=150, border_color="#8B5CF6", border_width=4.0))
        hero_col.addWidget(img_lbl, alignment=Qt.AlignmentFlag.AlignCenter)

        wordmark = QLabel("Toolbox Ninja")
        wordmark.setStyleSheet(
            f"font-size: 32px; font-weight: 800; color: {_TEXT}; letter-spacing: 3px;"
        )
        wordmark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_col.addWidget(wordmark)

        sub_lbl = QLabel("For creator — auto-detect viral highlight moments, crop to 9:16, and add captions.")
        sub_lbl.setStyleSheet(f"font-size: 13px; color: {_MUTED};")
        sub_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hero_col.addWidget(sub_lbl)

        rule = QFrame()
        rule.setFixedSize(48, 2)
        rule.setStyleSheet(f"background-color: {_ACCENT}; border: none;")
        hero_col.addWidget(rule, alignment=Qt.AlignmentFlag.AlignCenter)

        content_layout.addLayout(hero_col)

        # ── Section Label ──────────────────────────────────────────────────
        sec_row = QHBoxLayout()
        bullet = QLabel("\u25aa")
        bullet.setStyleSheet(f"color: {_ACCENT}; font-size: 14px;")
        sec_row.addWidget(bullet)
        sec_lbl = QLabel("Available Tools")
        sec_lbl.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {_TEXT}; letter-spacing: 0.5px;")
        sec_row.addWidget(sec_lbl)
        sec_row.addStretch()
        content_layout.addLayout(sec_row)

        # ── Menu Cards ─────────────────────────────────────────────────────
        grid_layout = QHBoxLayout()
        grid_layout.setContentsMargins(0, 4, 0, 10)
        grid_layout.setSpacing(16)

        # ── CARD 1: Clipper ────────────────────────────────────────────────
        card_clipper = QFrame()
        card_clipper.setObjectName("tool_card")
        card_clipper.setStyleSheet(f"""
            QFrame#tool_card {{
                background-color: {_SURFACE};
                border: 1px solid rgba(255, 255, 255, 0.09);
                border-radius: 12px;
            }}
            QFrame#tool_card:hover {{
                border: 1px solid rgba(139, 92, 246, 0.5);
                background-color: {_INPUT};
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        c1_layout = QVBoxLayout(card_clipper)
        c1_layout.setContentsMargins(18, 18, 18, 18)
        c1_layout.setSpacing(10)

        c1_icon_row = QHBoxLayout()
        c1_mono = QLabel("\u25b6")
        c1_mono.setFixedSize(36, 36)
        c1_mono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c1_mono.setStyleSheet(f"background-color: {_ACCENT_SOFT}; color: {_ACCENT}; border-radius: 8px; font-size: 15px;")
        c1_icon_row.addWidget(c1_mono)
        c1_icon_row.addStretch()

        badge = QLabel("READY")
        badge.setStyleSheet(
            f"font-size: 10px; font-weight: 700; color: {_SUCCESS}; "
            f"background-color: rgba(138, 201, 160, 0.12); border: none; border-radius: 10px; padding: 3px 8px;"
        )
        c1_icon_row.addWidget(badge)
        c1_layout.addLayout(c1_icon_row)

        c1_title = QLabel("Clipper")
        c1_title.setStyleSheet(f"font-size: 17px; font-weight: 700; color: {_TEXT};")
        c1_layout.addWidget(c1_title)

        c1_desc = QLabel(
            "Auto-detect viral highlight moments from video transcripts, crop to 9:16 Shorts/Reels, generate burned-in subtitles and captions."
        )
        c1_desc.setWordWrap(True)
        c1_desc.setStyleSheet(f"font-size: 12px; color: {_MUTED}; line-height: 1.4;")
        c1_layout.addWidget(c1_desc)

        c1_layout.addStretch()

        launch_btn = QPushButton("Open Clipper")
        launch_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {_ACCENT};
                color: {_ACCENT_TEXT};
                font-weight: 700;
                border-radius: 7px;
                padding: 10px 16px;
                font-size: 13px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {_ACCENT_HOVER};
            }}
        """)
        launch_btn.clicked.connect(self.launch_clipper.emit)
        c1_layout.addWidget(launch_btn)

        grid_layout.addWidget(card_clipper, stretch=1)

        # ── CARD 2: Voiceover ──────────────────────────────────────────────
        card_voice = QFrame()
        card_voice.setObjectName("tool_card")
        card_voice.setStyleSheet(f"""
            QFrame#tool_card {{
                background-color: {_SURFACE};
                border: 1px solid rgba(255, 255, 255, 0.09);
                border-radius: 12px;
            }}
            QFrame#tool_card:hover {{
                border: 1px solid rgba(56, 189, 248, 0.5);
                background-color: {_INPUT};
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        c2_layout = QVBoxLayout(card_voice)
        c2_layout.setContentsMargins(18, 18, 18, 18)
        c2_layout.setSpacing(10)

        c2_icon_row = QHBoxLayout()
        c2_mono = QLabel("🎙️")
        c2_mono.setFixedSize(36, 36)
        c2_mono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c2_mono.setStyleSheet(f"background-color: rgba(56, 189, 248, 0.15); color: #38bdf8; border-radius: 8px; font-size: 15px;")
        c2_icon_row.addWidget(c2_mono)
        c2_icon_row.addStretch()

        c2_badge = QLabel("READY")
        c2_badge.setStyleSheet(
            f"font-size: 10px; font-weight: 700; color: {_SUCCESS}; "
            f"background-color: rgba(138, 201, 160, 0.12); border: none; border-radius: 10px; padding: 3px 8px;"
        )
        c2_icon_row.addWidget(c2_badge)
        c2_layout.addLayout(c2_icon_row)

        c2_title = QLabel("Voiceover & Audio")
        c2_title.setStyleSheet(f"font-size: 17px; font-weight: 700; color: {_TEXT};")
        c2_layout.addWidget(c2_title)

        c2_desc = QLabel(
            "AI text-to-speech dubbing, background music studio, and auto-ducking audio mixer."
        )
        c2_desc.setWordWrap(True)
        c2_desc.setStyleSheet(f"font-size: 12px; color: {_MUTED}; line-height: 1.4;")
        c2_layout.addWidget(c2_desc)

        c2_layout.addStretch()

        c2_btn = QPushButton("Open Studio")
        c2_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: white;
                font-weight: 700;
                border-radius: 7px;
                padding: 10px 16px;
                font-size: 13px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
        """)
        c2_btn.clicked.connect(self.launch_voiceover.emit)
        c2_layout.addWidget(c2_btn)

        grid_layout.addWidget(card_voice, stretch=1)

        # ── CARD 3: Thumbnails ─────────────────────────────────────────────
        card_thumb = QFrame()
        card_thumb.setObjectName("tool_card")
        card_thumb.setStyleSheet(f"""
            QFrame#tool_card {{
                background-color: {_SURFACE};
                border: 1px solid rgba(255, 255, 255, 0.09);
                border-radius: 12px;
            }}
            QFrame#tool_card:hover {{
                border: 1px solid rgba(139, 92, 246, 0.5);
                background-color: {_INPUT};
            }}
            QLabel {{
                border: none;
                background: transparent;
            }}
        """)
        c3_layout = QVBoxLayout(card_thumb)
        c3_layout.setContentsMargins(18, 18, 18, 18)
        c3_layout.setSpacing(10)

        c3_icon_row = QHBoxLayout()
        c3_mono = QLabel("🖼️")
        c3_mono.setFixedSize(36, 36)
        c3_mono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c3_mono.setStyleSheet(f"background-color: {_ACCENT_SOFT}; color: {_ACCENT}; border-radius: 8px; font-size: 15px;")
        c3_icon_row.addWidget(c3_mono)
        c3_icon_row.addStretch()

        c3_badge = QLabel("READY")
        c3_badge.setStyleSheet(
            f"font-size: 10px; font-weight: 700; color: {_SUCCESS}; "
            f"background-color: rgba(138, 201, 160, 0.12); border: none; border-radius: 10px; padding: 3px 8px;"
        )
        c3_icon_row.addWidget(c3_badge)
        c3_layout.addLayout(c3_icon_row)

        c3_title = QLabel("Thumbnail Studio")
        c3_title.setStyleSheet(f"font-size: 17px; font-weight: 700; color: {_TEXT};")
        c3_layout.addWidget(c3_title)

        c3_desc = QLabel(
            "Auto-generate high-CTR thumbnails for YouTube, TikTok, and Instagram Reels."
        )
        c3_desc.setWordWrap(True)
        c3_desc.setStyleSheet(f"font-size: 12px; color: {_MUTED}; line-height: 1.4;")
        c3_layout.addWidget(c3_desc)

        c3_layout.addStretch()

        c3_btn = QPushButton("Open Studio")
        c3_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {_ACCENT};
                color: {_ACCENT_TEXT};
                font-weight: 700;
                border-radius: 7px;
                padding: 10px 16px;
                font-size: 13px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {_ACCENT_HOVER};
            }}
        """)
        c3_btn.clicked.connect(self.launch_thumbnails.emit)
        c3_layout.addWidget(c3_btn)

        grid_layout.addWidget(card_thumb, stretch=1)

        content_layout.addLayout(grid_layout)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)


class MainWindowV2(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Toolbox Ninja — For Creator")
        self.resize(1150, 780)
        self.setMinimumSize(850, 600)
        self.settings_mgr = SettingsManager()
        self.subtitle_settings = {
            "language": "id",
            "font_family": "Arial",
            "font_size": 48,
            "text_color": "#ffffff",
            "highlight_color": "#ffea00",
            "bg_color": "transparent",
            "position": "center",
            "style_bold": True,
            "style_italic": False,
            "stroke": True,
            "animation": "word_highlight"
        }

        self.setup_ui()

    def setup_ui(self):
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # ── PAGE 0: Dashboard Menu ─────────────────────────────────────────
        self.dashboard_view = ToolboxDashboardWidget()
        self.dashboard_view.launch_clipper.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        self.dashboard_view.launch_voiceover.connect(lambda: self.stacked_widget.setCurrentIndex(2))
        self.dashboard_view.launch_thumbnails.connect(lambda: self.stacked_widget.setCurrentIndex(3))
        self.dashboard_view.open_settings_requested.connect(self.open_settings)
        self.dashboard_view.show_about_requested.connect(self.show_about)
        self.dashboard_view.show_donate_requested.connect(self.show_donate_dialog)
        self.stacked_widget.addWidget(self.dashboard_view)

        # ── PAGE 1: Clipper Workspace ──────────────────────────────────────
        self.clipper_view = QWidget()
        clipper_layout = QVBoxLayout(self.clipper_view)
        clipper_layout.setContentsMargins(15, 15, 15, 15)

        header_layout = QHBoxLayout()

        back_btn = QPushButton("\u2190 Back")
        back_btn.setStyleSheet(_GHOST_BTN)
        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        header_layout.addWidget(back_btn)

        logo_lbl = QLabel("Toolbox Ninja")
        logo_lbl.setObjectName("heading")
        header_layout.addWidget(logo_lbl)

        self.donate_btn = QPushButton("Donate")
        self.donate_btn.setStyleSheet(_GHOST_BTN)
        self.donate_btn.clicked.connect(self.show_donate_dialog)
        header_layout.addWidget(self.donate_btn)

        btn_sub_settings = QPushButton("Subtitle Settings")
        btn_sub_settings.setStyleSheet(_GHOST_BTN)
        btn_sub_settings.clicked.connect(self.open_subtitle_settings)
        header_layout.addWidget(btn_sub_settings)

        settings_btn = QPushButton("Settings")
        settings_btn.setStyleSheet(_GHOST_BTN)
        settings_btn.clicked.connect(self.open_settings)
        header_layout.addWidget(settings_btn)

        about_btn = QPushButton("About")
        about_btn.setStyleSheet(_GHOST_BTN)
        about_btn.clicked.connect(self.show_about)
        header_layout.addWidget(about_btn)

        header_layout.addStretch()
        clipper_layout.addLayout(header_layout)

        # Splitter for Main Content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        clipper_layout.addWidget(splitter, stretch=1)

        # LEFT PANEL (Input & Controls)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 10, 0)

        self.left_tabs = QTabWidget()
        self.input_panel = InputPanel()
        self.input_panel.file_selected.connect(self.on_file_selected)

        self.reference_panel = ReferencePanel()

        self.left_tabs.addTab(self.reference_panel, "Viral References")
        self.left_tabs.addTab(self.input_panel, "Source Input")

        self.left_tabs.currentChanged.connect(self.on_tab_changed)

        left_layout.addWidget(self.left_tabs)

        # Export settings summary
        self.export_frame = QFrame()
        self.export_frame.setObjectName("glass_panel")
        export_layout = QVBoxLayout(self.export_frame)
        export_layout.setContentsMargins(12, 12, 12, 12)
        export_layout.setSpacing(8)
        export_layout.addWidget(QLabel("Export", objectName="heading"))

        self.process_btn = QPushButton("Find Viral Moments")
        self.process_btn.setObjectName("primary_btn")
        self.process_btn.clicked.connect(self.start_processing)
        export_layout.addWidget(self.process_btn)

        # Results area
        self.results_lbl = QLabel("Generated Clips", objectName="heading")
        left_layout.addWidget(self.results_lbl)

        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_content.setStyleSheet("background-color: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.results_scroll.setWidget(self.scroll_content)
        left_layout.addWidget(self.results_scroll, stretch=1)

        left_layout.addWidget(self.export_frame)

        # RIGHT PANEL (Preview & Results)
        self.right_panel = QWidget()
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(10, 0, 0, 0)

        preview_lbl = QLabel("Preview", objectName="heading")
        right_layout.addWidget(preview_lbl)

        # Video Player
        self.video_player = VideoPlayerWidget()
        right_layout.addWidget(self.video_player, stretch=1)

        # Waveform
        self.waveform = WaveformWidget()
        right_layout.addWidget(self.waveform)

        self.video_player.position_changed.connect(self.on_player_position_changed)
        self.video_player.duration_changed.connect(self.on_player_duration_changed)

        # Progress / Status Area
        self.status_lbl = QLabel("Ready.")
        self.status_lbl.setStyleSheet(f"color: {_MUTED}; font-size: 12px;")
        right_layout.addWidget(self.status_lbl)
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        right_layout.addWidget(self.progress_bar)

        splitter.addWidget(left_panel)
        splitter.addWidget(self.right_panel)
        splitter.setSizes([400, 700])

        # Add Clipper view to stacked widget (Index 1)
        self.stacked_widget.addWidget(self.clipper_view)

        # ── PAGE 2: Voiceover Workspace (Index 2) ─────────────────────────
        self.voiceover_view = VoiceoverWorkspaceWidget()
        self.voiceover_view.back_requested.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self.stacked_widget.addWidget(self.voiceover_view)

        # ── PAGE 3: Thumbnail Workspace (Index 3) ─────────────────────────
        self.thumbnail_view = ThumbnailWorkspaceWidget()
        self.thumbnail_view.back_requested.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self.stacked_widget.addWidget(self.thumbnail_view)

        # Set initial page to Dashboard (Index 0)
        self.stacked_widget.setCurrentIndex(0)
        self.on_tab_changed(0)

    def open_subtitle_settings(self):
        dlg = SubtitleSettingsDialog(self.subtitle_settings, self)
        if dlg.exec():
            self.subtitle_settings = dlg.get_settings()

    def open_settings(self):
        dlg = QtSettingsDialog(self.settings_mgr, self)
        dlg.exec()

    def show_about(self):
        QMessageBox.about(
            self,
            "About Toolbox Ninja AI Desktop",
            "<h3>🥷 Toolbox Ninja AI Desktop</h3>"
            "<p><b>Version 1.0.3</b> (Build 100 - Initial Release)</p>"
            "<p>All-in-one AI creation suite for creators — Clipper AI (Viral Moment Detector), "
            "Voiceover & Audio Studio, and AI Thumbnail Studio.</p>"
            "<br/>"
            "<p>Developed with ❤️ by <b>Andeztea Creative Code</b>.</p>"
        )

    def show_donate_dialog(self):
        dlg = DonateDialog(self)
        dlg.exec()

    def on_file_selected(self, file_path):
        self.current_file = file_path
        self.video_player.load_video(file_path)

        import threading
        def extract():
            data = WaveformExtractor.extract_waveform(file_path, num_points=100)
            self.waveform.set_waveform_data(data)
        threading.Thread(target=extract, daemon=True).start()

    def on_player_position_changed(self, pos):
        dur = self.video_player.media_player.duration()
        if dur > 0:
            self.waveform.set_position(pos / dur)

    def on_player_duration_changed(self, dur):
        pass

    def on_tab_changed(self, index):
        if index == 0:  # Viral References
            self.right_panel.hide()
            self.export_frame.hide()
            self.results_scroll.hide()
            self.results_lbl.hide()
        else:           # Source Input
            self.right_panel.show()
            self.export_frame.show()
            self.results_scroll.show()
            self.results_lbl.show()

    def start_processing(self):
        source = getattr(self, "current_file", None)
        if not source:
            QMessageBox.warning(self, "Warning", "Please select a video first!")
            return

        for i in reversed(range(self.scroll_layout.count())):
            w = self.scroll_layout.itemAt(i).widget()
            if w: w.deleteLater()

        self.process_btn.setEnabled(False)
        self.process_btn.setText("Processing...")
        self.progress_bar.setValue(0)

        num_clips = self.settings_mgr.data['clip_settings'].get('num_clips', 3)
        duration = self.settings_mgr.data['clip_settings'].get('target_duration', 30)
        aspect = self.settings_mgr.data['clip_settings'].get('aspect_ratio', '9:16')
        topic = self.input_panel.get_topic()

        self.thread = PipelineThread(source, num_clips, duration, aspect, self.settings_mgr, self.subtitle_settings, topic=topic)
        self.thread.progress_signal.connect(self.on_progress)
        self.thread.finished_signal.connect(self.on_finished)
        self.thread.error_signal.connect(self.on_error)
        self.thread.start()

    def on_progress(self, msg, val):
        self.status_lbl.setText(msg)
        self.progress_bar.setValue(int(val * 100))

    def on_finished(self, clips, output_files):
        self.process_btn.setEnabled(True)
        self.process_btn.setText("Find Viral Moments")
        for i, clip in enumerate(clips):
            path = output_files[i] if i < len(output_files) else ""
            card = ClipCardV2Widget(clip, path)
            card.play_requested.connect(self.video_player.load_video)
            self.scroll_layout.addWidget(card)

    def on_error(self, err):
        self.process_btn.setEnabled(True)
        self.process_btn.setText("Find Viral Moments")
        self.status_lbl.setText(f"Error: {err}")
        QMessageBox.critical(self, "Error", err)
