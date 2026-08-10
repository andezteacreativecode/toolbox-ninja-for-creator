import os
import shutil
import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSlider, QFileDialog, QMessageBox, QFrame, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QPixmap, QImage, QIcon

from core.thumbnail_engine import ThumbnailEngine
from config.settings import SettingsManager
from providers.provider_factory import ProviderFactory
from gui.widgets.dark_combo_box import DarkComboBox


class FrameExtractWorkerThread(QThread):
    finished_signal = pyqtSignal(list)
    error_signal = pyqtSignal(str)

    def __init__(self, video_path: str):
        super().__init__()
        self.video_path = video_path

    def run(self):
        try:
            frames = ThumbnailEngine.extract_key_frames(self.video_path, num_frames=6)
            self.finished_signal.emit(frames)
        except Exception as e:
            self.error_signal.emit(str(e))


class AIHookWorkerThread(QThread):
    finished_signal = pyqtSignal(list)
    error_signal = pyqtSignal(str)

    def __init__(self, topic: str, settings_mgr: SettingsManager):
        super().__init__()
        self.topic = topic
        self.settings_mgr = settings_mgr

    def run(self):
        try:
            active_key = self.settings_mgr.data.get("active_provider", "ollama")
            prov_cfg = self.settings_mgr.get_active_provider_config()
            ai_provider = ProviderFactory.get_provider(active_key, prov_cfg)
            hooks = ThumbnailEngine.generate_catchy_hooks(self.topic, ai_provider)
            self.finished_signal.emit(hooks)
        except Exception as e:
            self.error_signal.emit(str(e))


class ThumbnailWorkspaceWidget(QWidget):
    back_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings_mgr = SettingsManager()
        self.video_path = ""
        self.selected_bg_path = ""
        self.candidate_frames = []
        self.extract_thread = None
        self.hook_thread = None

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # ── Header ──────────────────────────────────────────────────────────
        header_layout = QHBoxLayout()
        back_btn = QPushButton("⬅ Back to Menu")
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(139, 92, 246, 0.2);
                color: #a78bfa;
                font-weight: bold;
                border: 1px solid rgba(139, 92, 246, 0.4);
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #8b5cf6;
                color: white;
            }
        """)
        back_btn.clicked.connect(self.back_requested.emit)
        header_layout.addWidget(back_btn)

        title_lbl = QLabel("🖼️ AI Thumbnail Studio")
        title_lbl.setStyleSheet("font-size: 20px; font-weight: 800; color: #f8fafc;")
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # ── Scroll Container for Layout ───────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        content_layout = QHBoxLayout(scroll_content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(16)

        # ── LEFT COLUMN: Source Input & Candidate Keyframes ───────────────
        left_card = QFrame()
        left_card.setStyleSheet("background-color: #1a1a2e; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px;")
        left_layout = QVBoxLayout(left_card)
        left_layout.setContentsMargins(18, 18, 18, 18)
        left_layout.setSpacing(12)

        sec1_title = QLabel("1. 🎬 Select Background Frame")
        sec1_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #a78bfa;")
        left_layout.addWidget(sec1_title)

        # Video File Selector
        vid_btn_row = QHBoxLayout()
        self.video_label = QLabel("No video selected")
        self.video_label.setStyleSheet("color: #64748b; background: #0f0f1e; padding: 6px; border-radius: 6px;")
        browse_vid_btn = QPushButton("📁 Browse Video")
        browse_vid_btn.setStyleSheet("background-color: rgba(255,255,255,0.08); color: #e2e8f0; border-radius: 6px; padding: 6px 12px;")
        browse_vid_btn.clicked.connect(self.browse_video)
        vid_btn_row.addWidget(self.video_label, stretch=1)
        vid_btn_row.addWidget(browse_vid_btn)
        left_layout.addLayout(vid_btn_row)

        self.extract_btn = QPushButton("⚡ Extract Candidate Frames")
        self.extract_btn.setMinimumHeight(38)
        self.extract_btn.setStyleSheet("""
            QPushButton {
                background-color: #8b5cf6;
                color: white;
                font-weight: 700;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #7c3aed;
            }
            QPushButton:disabled {
                background-color: #334155;
                color: #64748b;
            }
        """)
        self.extract_btn.clicked.connect(self.extract_frames)
        left_layout.addWidget(self.extract_btn)

        # Candidate Grid Label
        left_layout.addWidget(QLabel("Candidate Frames (Click to Select):"))
        
        # Grid Frame Container
        self.grid_frame = QFrame()
        self.grid_frame.setStyleSheet("background-color: #0f0f1e; border-radius: 8px; padding: 6px;")
        self.grid_layout = QGridLayout(self.grid_frame)
        self.grid_layout.setSpacing(8)
        left_layout.addWidget(self.grid_frame, stretch=1)

        # Custom Image Upload Button
        custom_img_btn = QPushButton("🖼️ Upload Custom Image")
        custom_img_btn.setStyleSheet("background-color: rgba(255,255,255,0.08); color: #e2e8f0; border-radius: 6px; padding: 8px;")
        custom_img_btn.clicked.connect(self.browse_custom_image)
        left_layout.addWidget(custom_img_btn)

        content_layout.addWidget(left_card, stretch=1)

        # ── RIGHT COLUMN: Live Preview Canvas & Typography Controls ───────
        right_card = QFrame()
        right_card.setStyleSheet("background-color: #1a1a2e; border: 1px solid rgba(255,255,255,0.08); border-radius: 12px;")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(18, 18, 18, 18)
        right_layout.setSpacing(12)

        sec2_title = QLabel("2. 🎨 Live Preview & Typography Studio")
        sec2_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #38bdf8;")
        right_layout.addWidget(sec2_title)

        # Aspect Ratio Selector
        ratio_row = QHBoxLayout()
        ratio_lbl = QLabel("Aspect Ratio Preset:")
        ratio_lbl.setStyleSheet("color: #94a3b8; font-weight: 600;")
        self.ratio_combo = DarkComboBox()
        self.ratio_combo.addItems(["16:9 YouTube Desktop/TV", "9:16 Shorts / Reels Cover", "1:1 Square Feed"])
        self.ratio_combo.currentIndexChanged.connect(self.update_preview)
        ratio_row.addWidget(ratio_lbl)
        ratio_row.addWidget(self.ratio_combo, stretch=1)
        right_layout.addLayout(ratio_row)

        # Live Canvas Preview Label
        self.preview_canvas = QLabel("Select or upload an image to preview thumbnail")
        self.preview_canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_canvas.setFixedSize(540, 304)
        self.preview_canvas.setStyleSheet("background-color: #0f0f1e; border: 1px dashed rgba(255,255,255,0.15); border-radius: 8px; color: #64748b;")
        right_layout.addWidget(self.preview_canvas, alignment=Qt.AlignmentFlag.AlignCenter)

        # Header Text Input + AI Hook Button
        header_text_lbl = QLabel("Main Title Hook:")
        header_text_lbl.setStyleSheet("color: #94a3b8; font-weight: 600;")
        right_layout.addWidget(header_text_lbl)

        header_row = QHBoxLayout()
        self.header_input = QLineEdit()
        self.header_input.setPlaceholderText("Enter main catchy hook (e.g., VIRAL SECRET!)...")
        self.header_input.setStyleSheet("background-color: #0f0f1e; color: #f8fafc; padding: 8px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.1);")
        self.header_input.textChanged.connect(self.update_preview)

        self.ai_hook_btn = QPushButton("✨ AI Hooks")
        self.ai_hook_btn.setStyleSheet("background-color: #8b5cf6; color: white; font-weight: bold; border-radius: 6px; padding: 8px 12px;")
        self.ai_hook_btn.clicked.connect(self.generate_ai_hooks)
        header_row.addWidget(self.header_input, stretch=1)
        header_row.addWidget(self.ai_hook_btn)
        right_layout.addLayout(header_row)

        # Subtext Input & Badge Tag
        subtext_row = QHBoxLayout()
        sub_layout = QVBoxLayout()
        sub_lbl = QLabel("Subtext Title:")
        sub_lbl.setStyleSheet("color: #94a3b8; font-weight: 600;")
        self.sub_input = QLineEdit()
        self.sub_input.setPlaceholderText("Enter subtext (optional)...")
        self.sub_input.setStyleSheet("background-color: #0f0f1e; color: #f8fafc; padding: 8px; border-radius: 6px; border: 1px solid rgba(255,255,255,0.1);")
        self.sub_input.textChanged.connect(self.update_preview)
        sub_layout.addWidget(sub_lbl)
        sub_layout.addWidget(self.sub_input)

        badge_layout = QVBoxLayout()
        badge_lbl = QLabel("Sticker Badge:")
        badge_lbl.setStyleSheet("color: #94a3b8; font-weight: 600;")
        self.badge_combo = DarkComboBox()
        self.badge_combo.addItems(["🔥 VIRAL", "😱 UNBELIEVABLE", "💡 MUST WATCH", "⭐ TOP TIPS", "None"])
        self.badge_combo.currentIndexChanged.connect(self.update_preview)
        badge_layout.addWidget(badge_lbl)
        badge_layout.addWidget(self.badge_combo)

        subtext_row.addLayout(sub_layout, stretch=2)
        subtext_row.addLayout(badge_layout, stretch=1)
        right_layout.addLayout(subtext_row)

        # Text Color & Filter Adjustments
        style_row = QHBoxLayout()
        color_lbl = QLabel("Text Color:")
        color_lbl.setStyleSheet("color: #94a3b8; font-weight: 600;")
        self.color_combo = DarkComboBox()
        self.color_combo.addItem("Kuning (#FFFF00)", "#FFFF00")
        self.color_combo.addItem("Putih (#FFFFFF)", "#FFFFFF")
        self.color_combo.addItem("Sian (#38BDF8)", "#38BDF8")
        self.color_combo.addItem("Hijau (#4ADE80)", "#4ADE80")
        self.color_combo.addItem("Merah (#F43F5E)", "#F43F5E")
        self.color_combo.currentIndexChanged.connect(self.update_preview)
        style_row.addWidget(color_lbl)
        style_row.addWidget(self.color_combo, stretch=1)
        right_layout.addLayout(style_row)

        # Sliders: Brightness & Contrast
        adj_row = QHBoxLayout()
        bright_layout = QVBoxLayout()
        bright_layout.addWidget(QLabel("Brightness:"))
        self.bright_slider = QSlider(Qt.Orientation.Horizontal)
        self.bright_slider.setRange(50, 150)
        self.bright_slider.setValue(100)
        self.bright_slider.valueChanged.connect(self.update_preview)
        bright_layout.addWidget(self.bright_slider)
        adj_row.addLayout(bright_layout)

        contrast_layout = QVBoxLayout()
        contrast_layout.addWidget(QLabel("Contrast:"))
        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setRange(50, 180)
        self.contrast_slider.setValue(110)
        self.contrast_slider.valueChanged.connect(self.update_preview)
        contrast_layout.addWidget(self.contrast_slider)
        adj_row.addLayout(contrast_layout)

        right_layout.addLayout(adj_row)
        right_layout.addStretch()

        # Export Button
        self.export_btn = QPushButton("💾 Export High-Res Thumbnail")
        self.export_btn.setMinimumHeight(44)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: white;
                font-weight: 700;
                font-size: 14px;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
        """)
        self.export_btn.clicked.connect(self.export_thumbnail)
        right_layout.addWidget(self.export_btn)

        content_layout.addWidget(right_card, stretch=1)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def browse_video(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "Video Files (*.mp4 *.mkv *.mov *.avi)")
        if file_path:
            self.video_path = file_path
            self.video_label.setText(os.path.basename(file_path))

    def browse_custom_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Background Image", "", "Image Files (*.jpg *.jpeg *.png)")
        if file_path:
            self.selected_bg_path = file_path
            self.update_preview()

    def extract_frames(self):
        if not self.video_path or not os.path.exists(self.video_path):
            QMessageBox.warning(self, "Warning", "Please select a video file first!")
            return

        self.extract_btn.setEnabled(False)
        self.extract_btn.setText("Extracting Frames...")

        self.extract_thread = FrameExtractWorkerThread(self.video_path)
        self.extract_thread.finished_signal.connect(self.on_frames_extracted)
        self.extract_thread.error_signal.connect(self.on_extract_error)
        self.extract_thread.start()

    def on_frames_extracted(self, frames: list):
        self.extract_btn.setEnabled(True)
        self.extract_btn.setText("⚡ Extract Candidate Frames")
        self.candidate_frames = frames

        # Clear grid layout
        for i in reversed(range(self.grid_layout.count())):
            w = self.grid_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        # Display extracted frames in 2-column grid
        for idx, fpath in enumerate(frames):
            btn = QPushButton()
            btn.setFixedSize(140, 80)
            btn.setIconSize(btn.size())

            pixmap = QPixmap(fpath)
            btn.setIcon(QIcon(pixmap))
            btn.setStyleSheet("border: 2px solid rgba(255,255,255,0.1); border-radius: 6px; background-color: black;")
            btn.clicked.connect(lambda _, path=fpath: self.set_selected_bg(path))

            row = idx // 2
            col = idx % 2
            self.grid_layout.addWidget(btn, row, col)

        if frames:
            self.set_selected_bg(frames[0])

    def on_extract_error(self, err_msg: str):
        self.extract_btn.setEnabled(True)
        self.extract_btn.setText("⚡ Extract Candidate Frames")
        QMessageBox.critical(self, "Extract Error", f"Failed to extract frames:\n{err_msg}")

    def set_selected_bg(self, bg_path: str):
        self.selected_bg_path = bg_path
        self.update_preview()

    def generate_ai_hooks(self):
        topic = self.header_input.text().strip() or "Viral Moment Highlights"
        self.ai_hook_btn.setEnabled(False)
        self.ai_hook_btn.setText("Generating...")

        self.hook_thread = AIHookWorkerThread(topic, self.settings_mgr)
        self.hook_thread.finished_signal.connect(self.on_hooks_generated)
        self.hook_thread.error_signal.connect(self.on_hook_error)
        self.hook_thread.start()

    def on_hooks_generated(self, hooks: list):
        self.ai_hook_btn.setEnabled(True)
        self.ai_hook_btn.setText("✨ AI Hooks")
        if hooks:
            self.header_input.setText(hooks[0])

    def on_hook_error(self, err_msg: str):
        self.ai_hook_btn.setEnabled(True)
        self.ai_hook_btn.setText("✨ AI Hooks")
        QMessageBox.warning(self, "AI Hook Warning", f"Could not generate AI hook:\n{err_msg}")

    def update_preview(self):
        if not self.selected_bg_path or not os.path.exists(self.selected_bg_path):
            return

        ratio_text = self.ratio_combo.currentText()
        if "16:9" in ratio_text:
            ratio_val = "16:9"
        elif "9:16" in ratio_text:
            ratio_val = "9:16"
        else:
            ratio_val = "1:1"

        badge_val = self.badge_combo.currentText()
        if badge_val == "None":
            badge_val = ""

        header_val = self.header_input.text().strip()
        sub_val = self.sub_input.text().strip()
        text_col = self.color_combo.currentData() or "#FFFF00"
        bright = self.bright_slider.value() / 100.0
        contrast = self.contrast_slider.value() / 100.0

        try:
            temp_preview_path = os.path.join(os.getcwd(), "temp_frames", "preview_rendered.png")
            ThumbnailEngine.render_thumbnail(
                bg_image_path=self.selected_bg_path,
                header_text=header_val,
                sub_text=sub_val,
                badge_text=badge_val,
                aspect_ratio=ratio_val,
                text_color=text_col,
                brightness=bright,
                contrast=contrast,
                output_path=temp_preview_path
            )

            pix = QPixmap(temp_preview_path)
            # Adjust canvas fixed size preview box based on aspect ratio
            if ratio_val == "16:9":
                self.preview_canvas.setFixedSize(540, 304)
            elif ratio_val == "9:16":
                self.preview_canvas.setFixedSize(225, 400)
            else:
                self.preview_canvas.setFixedSize(360, 360)

            scaled_pix = pix.scaled(
                self.preview_canvas.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_canvas.setPixmap(scaled_pix)
        except Exception as e:
            print(f"[ThumbnailWorkspace] Preview render error: {e}")

    def export_thumbnail(self):
        if not self.selected_bg_path or not os.path.exists(self.selected_bg_path):
            QMessageBox.warning(self, "Warning", "Please select or upload a background image first!")
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export High-Res Thumbnail",
            "thumbnail.png",
            "PNG Image (*.png);;JPG Image (*.jpg)"
        )
        if save_path:
            ratio_text = self.ratio_combo.currentText()
            ratio_val = "16:9" if "16:9" in ratio_text else ("9:16" if "9:16" in ratio_text else "1:1")
            badge_val = self.badge_combo.currentText()
            if badge_val == "None":
                badge_val = ""

            try:
                ThumbnailEngine.render_thumbnail(
                    bg_image_path=self.selected_bg_path,
                    header_text=self.header_input.text().strip(),
                    sub_text=self.sub_input.text().strip(),
                    badge_text=badge_val,
                    aspect_ratio=ratio_val,
                    text_color=self.color_combo.currentData() or "#FFFF00",
                    brightness=self.bright_slider.value() / 100.0,
                    contrast=self.contrast_slider.value() / 100.0,
                    output_path=save_path
                )
                QMessageBox.information(self, "Success", f"Thumbnail saved successfully to:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export thumbnail:\n{e}")
